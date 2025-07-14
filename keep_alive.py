# keep_alive.py

from flask import Flask
from threading import Thread
import logging

# Tắt bớt các log không cần thiết của Flask để console gọn gàng
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask('')

@app.route('/')
def home():
    print("Ping from UptimeRobot received!")
    return "Bot đang hoạt động!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # Thêm daemon=True để đảm bảo tiến trình này sẽ tự tắt
    # khi chương trình chính (bot.py) kết thúc.
    t = Thread(target=run, daemon=True)
    t.start()
    print("Server Keep-Alive đã được khởi động.")