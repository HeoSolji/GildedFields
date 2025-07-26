# data_manager.py
from dotenv import load_dotenv
load_dotenv()

import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import config

# --- KẾT NỐI DATABASE ---
MONGO_URI = os.getenv('MONGO_CONNECTION_STRING')
if not MONGO_URI:
    raise Exception("MONGO_CONNECTION_STRING không được tìm thấy trong file .env")

# Tạo một client MongoDB mới
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client.farmbot_db # Tên database của bạn
player_collection = db.players # Tên collection (giống như bảng)

# Gửi một ping để xác nhận kết nối thành công
try:
    client.admin.command('ping')
    print("Ping thành công! Đã kết nối tới MongoDB.")
except Exception as e:
    print(e)

# GAME_DATA bây giờ sẽ hoạt động như một bộ nhớ đệm (cache)
GAME_DATA = {}

def load_player_data():
    """Tải tất cả dữ liệu người chơi từ MongoDB vào cache."""
    global GAME_DATA
    all_players = player_collection.find({})
    for player in all_players:
        user_id = player.pop('_id') # MongoDB dùng _id, ta chuyển nó thành key
        GAME_DATA[user_id] = player
    print(f"Đã tải dữ liệu của {len(GAME_DATA)} người chơi từ MongoDB vào cache.")

def save_player_data():
    """Lưu tất cả dữ liệu từ cache lên MongoDB."""
    if not GAME_DATA:
        return

    for user_id, data in GAME_DATA.items():
        # Dùng update_one với upsert=True: nếu user_id đã tồn tại thì cập nhật, nếu chưa có thì tạo mới.
        player_collection.update_one(
            {'_id': user_id},
            {'$set': data},
            upsert=True
        )
    print(f"Đã đồng bộ dữ liệu của {len(GAME_DATA)} người chơi lên MongoDB.")

def get_player_data(user_id):
    """Lấy dữ liệu của người chơi từ cache."""
    return GAME_DATA.get(str(user_id))

def initialize_player(user_id):
    """Khởi tạo dữ liệu cho người chơi mới trong cache (sẽ được lưu sau)."""
    user_id_str = str(user_id)
    if user_id_str in GAME_DATA:
        return False

    # Cấu trúc dữ liệu cho người chơi mới
    initial_farm_plots = {f"{r}_{c}": None for r in range(config.FARM_GRID_SIZE) for c in range(config.FARM_GRID_SIZE)}
    
    new_player_data = {
        "balance": config.INITIAL_BALANCE,
        "inventory": {},
        "farm": {"size": config.FARM_GRID_SIZE, "plots": initial_farm_plots, "notification_sent": True},
        "barn": {"capacity": config.INITIAL_BARN_CAPACITY, "animals": {}, "notification_sent": True},
        "last_daily_claim": None,
        "level": 1,
        "xp": 0,
        "achievements": {"unlocked": [], "progress": {}},
        "machines": {
                "seed_maker": []
        },
        "quests": {
            "daily": [],
            "special": None, # Chỉ có 1 nhiệm vụ đặc biệt tại một thời điểm
            "last_updated": 0, # Timestamp để biết khi nào cần reset
            "reputation": {"johnson": 0, "barry": 0},
            "unlocked_recipes": []
        }
    }
    GAME_DATA[user_id_str] = new_player_data
    # Lưu người chơi mới này lên DB ngay lập tức
    player_collection.update_one(
        {'_id': user_id_str},
        {'$set': GAME_DATA[user_id_str]},
        upsert=True
    )
    print(f"Đã khởi tạo và lưu người chơi mới {user_id_str} lên MongoDB.")
    return True