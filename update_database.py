# update_database.py
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os

def run_database_update():
    """Kịch bản dùng một lần để đảm bảo tất cả người chơi có schema 'machines' đúng chuẩn."""
    print("--- Bắt đầu kịch bản cập nhật Database ---")
    load_dotenv()
    MONGO_URI = os.getenv('MONGO_CONNECTION_STRING')
    if not MONGO_URI:
        print("Lỗi: Không tìm thấy MONGO_CONNECTION_STRING.")
        return

    client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    db = client.farmbot_db
    player_collection = db.players
    print("✅ Đã kết nối tới MongoDB.")

    # Tìm tất cả người chơi CHƯA có cấu trúc machines.seed_maker
    filter_query = {"machines.seed_maker": {"$exists": False}}
    
    # Thao tác cập nhật: tạo ra cấu trúc machines.seed_maker hoàn chỉnh
    update_operation = {"$set": {"machines.seed_maker": []}}

    result = player_collection.update_many(filter_query, update_operation)

    print(f"\n✅ Hoàn tất!")
    print(f"Đã tìm thấy {result.matched_count} người chơi cần cập nhật.")
    print(f"Đã sửa đổi thành công {result.modified_count} người chơi.")

if __name__ == "__main__":
    run_database_update()