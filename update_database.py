# update_players_add_quests.py
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os

def run_update():
    """Kịch bản dùng một lần để thêm trường 'quests' cho người chơi cũ."""
    load_dotenv()
    MONGO_URI = os.getenv('MONGO_CONNECTION_STRING')
    client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
    db = client.farmbot_db
    player_collection = db.players
    print("Đã kết nối tới MongoDB.")

    filter_query = {"quests": {"$exists": False}}
    update_operation = {
        "$set": {
            "quests": {
                "daily": [],
                "special": None,
                "last_updated": 0,
                "reputation": {"johnson": 0, "barry": 0}
            }
        }
    }

    result = player_collection.update_many(filter_query, update_operation)
    print(f"\n✅ Hoàn tất! Đã cập nhật {result.modified_count} người chơi.")

if __name__ == "__main__":
    run_update()