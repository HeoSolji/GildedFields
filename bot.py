# bot.py

# Bước 1: Nạp biến môi trường LÊN ĐẦU TIÊN
from dotenv import load_dotenv
load_dotenv()

# Bước 2: Import các thư viện và module cần thiết
import discord
from discord.ext import commands, tasks
import os, asyncio, random, time, traceback
from keep_alive import keep_alive
import data_manager, market_manager, config, utils, quest_manager

# --- Tải TOKEN ---
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    print("Lỗi: Không tìm thấy DISCORD_BOT_TOKEN trong file .env")
    exit()

# --- Định nghĩa Class Bot chính ---
intents = discord.Intents.all()

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        """Hàm này được tự động gọi một lần khi bot chuẩn bị khởi động."""
        print("--- Đang tải các Cogs... ---")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'  -> Đã tải thành công: {filename}')
                except Exception as e:
                    print(f'  -> Lỗi khi tải {filename}: {e}')
        
        print("\n--- Đang đồng bộ lệnh... ---")
        try:
            synced = await self.tree.sync()
            print(f"  -> Đã đồng bộ {len(synced)} lệnh / thành công.")
        except Exception as e:
            print(f"  -> Lỗi khi đồng bộ lệnh: {e}")

bot = MyBot()

# --- CÁC TÁC VỤ NỀN (BACKGROUND TASKS) ---

@tasks.loop(minutes=3)
async def auto_save_data():
    """Tự động lưu dữ liệu người chơi mỗi 3 phút."""
    await bot.wait_until_ready()
    print("Đang tự động lưu dữ liệu người chơi...")
    data_manager.save_player_data()

@tasks.loop(seconds=30)
async def check_harvest_notifications():
    await bot.wait_until_ready()
    current_time = time.time()
    player_ids = list(data_manager.GAME_DATA.keys())

    for user_id in player_ids:
        try:
            user_data = data_manager.get_player_data(user_id)
            if not user_data: continue

            # --- KIỂM TRA NÔNG TRẠI (FARM) ---
            farm_data = user_data.get('farm', {})
            if not farm_data.get('notification_sent', True):
                print(f"\n[NOTIF DEBUG] Checking FARM for user: {user_id}")
                plots = farm_data.get('plots', {})
                has_planted_crops, all_plots_ready = False, True
                
                for plot_data in plots.values():
                    if plot_data and "crop" in plot_data:
                        has_planted_crops = True
                        if current_time < plot_data.get('ready_time', float('inf')):
                            all_plots_ready = False
                            break
                
                print(f"[NOTIF DEBUG]  -> Has planted: {has_planted_crops}")
                print(f"[NOTIF DEBUG]  -> All plots ready: {all_plots_ready}")

                if has_planted_crops and all_plots_ready:
                    print(f"[NOTIF DEBUG]  --> Sending FARM notification to {user_id}")
                    try:
                        user = await bot.fetch_user(int(user_id))
                        await user.send("🔔 **Thông báo Farm:** Tất cả cây trồng đã sẵn sàng để thu hoạch! Dùng lệnh `/harvest`.")
                        farm_data['notification_sent'] = True
                    except Exception as e:
                        print(f"[ERROR] Không thể gửi tin nhắn farm cho {user_id}: {e}")
                        farm_data['notification_sent'] = True

            # --- KIỂM TRA CHUỒNG NUÔI (BARN) ---
            barn_data = user_data.get('barn', {})
            if not barn_data.get('notification_sent', True):
                print(f"\n[NOTIF DEBUG] Checking BARN for user: {user_id}")
                animals_in_barn = barn_data.get('animals', {})
                is_any_animal_ready = False
                if animals_in_barn:
                    for ready_times in animals_in_barn.values():
                        if any(current_time >= rt for rt in ready_times):
                            is_any_animal_ready = True
                            break
                
                print(f"[NOTIF DEBUG]  -> Any animal ready: {is_any_animal_ready}")

                if is_any_animal_ready:
                    print(f"[NOTIF DEBUG]  --> Sending BARN notification to {user_id}")
                    try:
                        user = await bot.fetch_user(int(user_id))
                        await user.send("🐄 **Thông báo Barn:** Bạn có sản phẩm trong chuồng đã sẵn sàng để thu hoạch! Dùng lệnh `/machine collect`.")
                        barn_data['notification_sent'] = True
                    except Exception as e:
                        print(f"[ERROR] Không thể gửi tin nhắn barn cho {user_id}: {e}")
                        barn_data['notification_sent'] = True
        except Exception as e:
            print(f"!!! [CRITICAL TASK ERROR] !!! Lỗi khi xử lý thông báo cho người dùng {user_id}: {e}")
            import traceback
            traceback.print_exc()

@tasks.loop(hours=24)
async def update_market():
    await bot.wait_until_ready()
    market_manager.generate_supply_demand_events()
    channel_id = config.MARKET_EVENT_CHANNEL_ID
    if channel_id:
        try:
            channel = await bot.fetch_channel(channel_id)
            embed = discord.Embed(title="📈 Bản Tin Thị Trường Nông Sản 📉", description=market_manager.current_event_message, color=discord.Color.random())
            await channel.send(embed=embed)
            print("Đã cập nhật và thông báo sự kiện thị trường mới.")
        except Exception as e:
            print(f"Không thể gửi thông báo thị trường đến kênh {channel_id}: {e}")

@tasks.loop(minutes=1)
async def check_companion_planting():
    """Kiểm tra và áp dụng hiệu ứng xen canh."""
    await bot.wait_until_ready()
    
    for user_id, user_data in data_manager.GAME_DATA.items():
        try:
            farm_data = user_data.get('farm', {})
            plots = farm_data.get('plots', {})
            farm_size = farm_data.get('size', 0)
            
            # 1. Thu thập thông tin các hàng cây đồng nhất
            rows_info = {}
            for r in range(farm_size):
                row_crop_id = None
                is_uniform = True
                # Kiểm tra xem cả hàng có trồng cùng 1 loại cây không
                for c in range(farm_size):
                    plot_data = plots.get(f"{r}_{c}")
                    if not plot_data or "crop" not in plot_data:
                        is_uniform = False; break
                    if row_crop_id is None: row_crop_id = plot_data['crop']
                    elif row_crop_id != plot_data['crop']: is_uniform = False; break
                
                # SỬA LỖI: Dòng này phải nằm ngoài vòng lặp 'c'
                if is_uniform and row_crop_id:
                    rows_info[r] = row_crop_id
            
            # 2. Kiểm tra và áp dụng bonus
            for r, crop_id in rows_info.items():
                bonus, has_companion = 0, False
                
                # Logic kiểm tra hai chiều
                companion_info = config.COMPANION_PLANTS.get(crop_id)
                if companion_info and (rows_info.get(r - 1) == companion_info['partner'] or rows_info.get(r + 1) == companion_info['partner']):
                    has_companion = True; bonus = companion_info['bonus']
                else:
                    for key, value in config.COMPANION_PLANTS.items():
                        if value['partner'] == crop_id and (rows_info.get(r - 1) == key or rows_info.get(r + 1) == key):
                            has_companion = True; bonus = value['bonus']; break
                
                # Áp dụng hoặc hủy bonus cho cả hàng
                for c in range(farm_size):
                    plot_data = plots.get(f"{r}_{c}")
                    if not plot_data: continue
                    
                    original_grow_time = config.CROPS[crop_id]['grow_time']
                    if has_companion and not plot_data.get('companion_bonus_applied'):
                        time_saved = original_grow_time * bonus
                        plot_data['ready_time'] -= time_saved
                        plot_data['companion_bonus_applied'] = True
                    elif not has_companion and plot_data.get('companion_bonus_applied'):
                        time_added = original_grow_time * bonus
                        plot_data['ready_time'] += time_added
                        plot_data['companion_bonus_applied'] = False
        except Exception as e:
            print(f"Lỗi trong tác vụ xen canh cho user {user_id}: {e}")

# --- SỰ KIỆN ON_READY ---
@bot.event
async def on_ready():
    print(f'\nBot đã đăng nhập với tên: {bot.user}')
    print('-------------------')
    data_manager.load_player_data()
    
    # Bắt đầu các vòng lặp tác vụ nền
    auto_save_data.start()
    check_harvest_notifications.start()
    update_market.start()
    check_companion_planting.start()

# --- KHỐI CHẠY CHÍNH ---
async def main():
    keep_alive()
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPhát hiện KeyboardInterrupt, đang tắt bot...")
    finally:
        print("Thực hiện lưu dữ liệu lần cuối...")
        data_manager.save_player_data()
        print("Đã lưu. Bot đã tắt hoàn toàn.")