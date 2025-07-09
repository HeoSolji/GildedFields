# bot.py

import discord
from discord.ext import commands, tasks
import os
import json
import asyncio
import data_manager
from keep_alive import keep_alive
# --- Tải TOKEN ---
# Ưu tiên lấy TOKEN từ biến môi trường, nếu không có thì tìm trong file config.json
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    try:
        with open('config.json', 'r') as f:
            config_file = json.load(f)
        TOKEN = config_file.get('TOKEN')
    except FileNotFoundError:
        print("Lỗi: Không tìm thấy file config.json.")
        exit()
    except KeyError:
        print("Lỗi: Trong config.json không có key 'TOKEN'.")
        exit()

if not TOKEN:
    print("Lỗi: TOKEN không được cung cấp. Vui lòng tạo file config.json hoặc đặt biến môi trường DISCORD_BOT_TOKEN.")
    exit()


# --- Khởi tạo Bot ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


# --- Tác vụ nền (Background Task) ---
@tasks.loop(minutes=3)
async def auto_save_data():
    """Tự động lưu dữ liệu người chơi mỗi 3 phút."""
    print("Đang tự động lưu dữ liệu người chơi...")
    data_manager.save_player_data()



@tasks.loop(seconds=30) # Chạy mỗi 30 giây
async def check_harvest_notifications():
    # Chờ cho đến khi bot sẵn sàng và đã tải dữ liệu
    await bot.wait_until_ready()
    
    current_time = time.time()
    # Tạo một bản copy của các key để tránh lỗi khi dict thay đổi trong lúc lặp
    player_ids = list(data_manager.GAME_DATA.keys())

    for user_id in player_ids:
        user_data = data_manager.get_player_data(user_id)
        if not user_data:
            continue

        farm_data = user_data.get('farm', {})
        # Bỏ qua nếu người chơi đã được thông báo hoặc không có farm
        if farm_data.get('notification_sent', True):
            continue

        plots = farm_data.get('plots', {})
        planted_plots = [plot for plot in plots.values() if plot is not None]

        # Nếu không có cây nào đang trồng, reset cờ và bỏ qua
        if not planted_plots:
            user_data['farm']['notification_sent'] = True
            continue

        # Kiểm tra xem TẤT CẢ cây đã sẵn sàng chưa
        all_ready = all(current_time >= plot['ready_time'] for plot in planted_plots)

        if all_ready:
            try:
                user = await bot.fetch_user(int(user_id))
                await user.send("🔔 **Thông báo:** Tất cả cây trồng trong nông trại của bạn đã sẵn sàng để thu hoạch! Dùng lệnh `!harvest` ngay nhé.")
                
                # Đánh dấu đã gửi thông báo
                user_data['farm']['notification_sent'] = True
                print(f"Đã gửi thông báo thu hoạch cho {user.name}")
            except Exception as e:
                print(f"Không thể gửi tin nhắn cho người dùng {user_id}: {e}")
                # Vẫn đánh dấu đã gửi để không spam lỗi
                user_data['farm']['notification_sent'] = True

# --- Sự kiện của Bot ---
@bot.event
async def on_ready():
    """Sự kiện được kích hoạt khi bot sẵn sàng hoạt động."""
    print(f'Bot đã đăng nhập với tên: {bot.user.name}')
    print('------')
    data_manager.load_player_data()
    auto_save_data.start() # Bắt đầu vòng lặp tự động lưu

@bot.event
async def on_disconnect():
    """Sự kiện được kích hoạt khi bot mất kết nối."""
    print("Bot đang mất kết nối. Thực hiện lưu dữ liệu cuối cùng...")
    data_manager.save_player_data()


# --- Hàm chính để chạy bot ---
async def main():
    """Hàm chính để tải các Cogs và khởi động bot."""
    async with bot:
        # Tải tất cả các file lệnh trong thư mục 'cogs'
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Đã tải thành công: {filename}')
                except Exception as e:
                    print(f'Lỗi khi tải {filename}: {e}')
        
        # Bắt đầu chạy bot
        await bot.start(TOKEN)

# Chạy hàm main
if __name__ == "__main__":
    try:
        keep_alive()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot đang tắt...")