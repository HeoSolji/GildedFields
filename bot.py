# bot.py

import discord
from discord.ext import commands, tasks
import os
import json
import asyncio
import random
import time
from dotenv import load_dotenv

# Các module quản lý của chúng ta
import data_manager
import market_manager
from keep_alive import keep_alive # Dành cho Replit
import config

# --- Tải TOKEN từ file .env ---
load_dotenv() 
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    print("Lỗi: Không tìm thấy DISCORD_BOT_TOKEN trong file .env hoặc biến môi trường.")
    exit()

# --- Khởi tạo Bot ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


# --- CÁC TÁC VỤ NỀN (BACKGROUND TASKS) ---

@tasks.loop(minutes=3)
async def auto_save_data():
    """Tự động lưu dữ liệu người chơi mỗi 3 phút."""
    await bot.wait_until_ready()
    print("Đang tự động lưu dữ liệu người chơi...")
    data_manager.save_player_data()

@tasks.loop(seconds=30)
async def check_harvest_notifications():
    """Kiểm tra và gửi thông báo thu hoạch, đồng thời kiểm tra tỉ lệ cây khổng lồ."""
    # Chờ cho đến khi bot sẵn sàng và đã tải dữ liệu
    await bot.wait_until_ready()
    
    current_time = time.time()
    # Tạo một bản copy của các key để tránh lỗi khi dict thay đổi trong lúc lặp
    player_ids = list(data_manager.GAME_DATA.keys())

    # print("--- [BACKGROUND TASK] Running notification check... ---") # Có thể bật dòng này để debug

    for user_id in player_ids:
        # Bọc logic của mỗi người dùng trong try-except để lỗi của 1 người không làm hỏng cả tác vụ
        try:
            user_data = data_manager.get_player_data(user_id)
            if not user_data: continue

            farm_data = user_data.get('farm', {})
            plots = farm_data.get('plots', {})
            
            # Nếu cờ thông báo đã được gửi, không cần kiểm tra gì thêm cho người này
            if farm_data.get('notification_sent', True):
                continue

            all_plots_ready = True
            has_planted_crops = False

            for plot_data in plots.values():
                if not plot_data: continue
                
                has_planted_crops = True
                
                # Nếu có ít nhất 1 cây chưa chín, thì chưa thể có thông báo "tất cả đã sẵn sàng"
                if current_time < plot_data.get('ready_time', float('inf')):
                    all_plots_ready = False
                    continue # Bỏ qua cây này và đi đến cây tiếp theo
                
                # Nếu cây đã chín nhưng chưa được kiểm tra tỉ lệ khổng lồ
                if not plot_data.get('is_giant') and not plot_data.get('checked_for_giant'):
                    plot_data['checked_for_giant'] = True # Đánh dấu đã kiểm tra để không lặp lại
                    
                    crop_id = plot_data.get('crop')
                    # Thử vận may
                    if crop_id and crop_id in config.GIANT_CROP_CANDIDATES and random.random() < config.GIANT_CROP_CHANCE:
                        plot_data['is_giant'] = True
                        try:
                            user = await bot.fetch_user(int(user_id))
                            crop_info = config.CROPS[crop_id]
                            await user.send(f"🌟 Chúc mừng! Một cây **{crop_info['display_name']}** trong nông trại của bạn đã phát triển thành cây **KHỔNG LỒ**! Dùng `/harvest` để thu hoạch nó nhé.")
                            print(f"Đã tạo cây khổng lồ {crop_id} cho {user.name}")
                        except Exception as e:
                            print(f"Lỗi khi gửi DM cây khổng lồ cho {user_id}: {e}")

            # Gửi thông báo thu hoạch chung nếu tất cả cây đã chín và chưa gửi thông báo
            if has_planted_crops and all_plots_ready and not farm_data.get('notification_sent', True):
                try:
                    user = await bot.fetch_user(int(user_id))
                    await user.send("🔔 **Thông báo:** Tất cả cây trồng trong nông trại của bạn đã sẵn sàng để thu hoạch! Dùng lệnh `/harvest` ngay nhé.")
                    farm_data['notification_sent'] = True
                    print(f"[SUCCESS] Đã gửi thông báo thu hoạch cho {user.name} ({user_id})")
                except Exception as e:
                    print(f"[ERROR] Không thể gửi tin nhắn thu hoạch cho người dùng {user_id}: {e}")
                    # Vẫn set để không spam lỗi
                    farm_data['notification_sent'] = True

        except Exception as e:
            # Nếu có bất kỳ lỗi nào xảy ra với dữ liệu của người chơi này, in ra và tiếp tục với người chơi khác
            print(f"!!! [CRITICAL TASK ERROR] !!! Lỗi khi xử lý người dùng {user_id}: {e}")
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

# --- SỰ KIỆN CỦA BOT ---
@bot.event
async def on_ready():
    """Sự kiện được kích hoạt khi bot sẵn sàng và đã tải xong mọi thứ."""
    print(f'Bot đã đăng nhập với tên: {bot.user}')
    print('------')
    data_manager.load_player_data()
    
    # BẮT ĐẦU TẤT CẢ CÁC VÒNG LẶP TÁC VỤ NỀN
    auto_save_data.start()
    check_harvest_notifications.start()
    update_market.start()
    # check_giant_crops.start() # Tạm thời tắt vì đã gộp logic

# --- HÀM MAIN VÀ KHỐI CHẠY CHÍNH ---
async def main():
    """Hàm chính để tải các Cogs và khởi động bot."""
    async with bot:
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Đã tải thành công: {filename}')
                except Exception as e:
                    print(f'Lỗi khi tải {filename}: {e}')
        await bot.start(TOKEN)

if __name__ == "__main__":
    # Dành cho Replit hosting
    # keep_alive() 
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPhát hiện KeyboardInterrupt, đang tắt bot...")
    finally:
        print("Thực hiện lưu dữ liệu lần cuối...")
        data_manager.save_player_data()
        print("Đã lưu. Bot đã tắt hoàn toàn.")