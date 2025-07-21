# migrate_to_mongo.py
import json
import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# --- PHẦN NÀY SAO CHÉP TỪ CÁC FILE KHÁC ---

# Tải biến môi trường
load_dotenv()

# Kết nối MongoDB (giống data_manager.py mới)
MONGO_URI = os.getenv('MONGO_CONNECTION_STRING')
if not MONGO_URI:
    raise Exception("MONGO_CONNECTION_STRING không được tìm thấy trong file .env")
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client.farmbot_db
player_collection = db.players

# Sao chép file config.py cũ vào đây để lấy các hằng số
class Config:
    FARM_GRID_SIZE = 3
    INITIAL_BARN_CAPACITY = 5
    # Giả lập các hằng số cần thiết khác nếu cần
    # ANIMALS = {"chicken": {"production_time": 3600}} # Ví dụ

# Hàm migrate cũ (sao chép từ file data_manager.py cũ của bạn)
def _migrate_player_data_from_json(user_id_str, player_data):
    if 'farm' in player_data and (not isinstance(player_data['farm'], dict) or 'size' not in player_data['farm']):
        print(f"Nâng cấp dữ liệu farm cho người chơi {user_id_str}...")
        old_plots = player_data.get('farm', {})
        player_data['farm'] = {
            'size': config.FARM_GRID_SIZE,
            'plots': old_plots
        }
    
    # Nâng cấp dữ liệu Barn (Giữ nguyên)
    if 'barn' not in player_data:
        print(f"Thêm dữ liệu barn cho người chơi cũ {user_id_str}...")
        player_data['barn'] = {
            "capacity": config.INITIAL_BARN_CAPACITY,
            "animals": {}
        }
    
    # --- THÊM LOGIC MỚI: Chuyển đổi cấu trúc animals ---
    if 'animals' in player_data['barn']:
        for animal_id, data in player_data['barn']['animals'].items():
            # Nếu dữ liệu vẫn là dạng cũ (có 'count'), thì chuyển đổi nó
            if isinstance(data, dict) and 'count' in data:
                print(f"Chuyển đổi dữ liệu animal cho người chơi {user_id_str}...")
                count = data['count']
                last_collected = data['last_collected']
                production_time = config.ANIMALS[animal_id]['production_time']
                
                # Tạo danh sách các mốc thời gian sẵn sàng cho từng con vật
                ready_times = [last_collected + production_time] * count
                player_data['barn']['animals'][animal_id] = ready_times
                break # Chỉ cần chạy 1 lần là đủ
    
    if 'achievements' not in player_data:
        print(f"Thêm dữ liệu achievements cho người chơi cũ {user_id_str}...")
        player_data['achievements'] = {
            "unlocked": [],
            "progress": {}
        }
    if 'notification_sent' not in player_data.get('farm', {}):
        print(f"Thêm cờ thông báo cho người chơi {user_id_str}...")
        if 'farm' in player_data:
            player_data['farm']['notification_sent'] = True # Mặc định là True để không báo cho farm cũ
    if 'level' not in player_data:
        print(f"Thêm dữ liệu level/xp cho người chơi cũ {user_id_str}...")
        player_data['level'] = 1
        player_data['xp'] = 0
    
    if 'inventory' in player_data:
        # Tạo một kho đồ mới
        new_inventory = {}
        is_old_format = False
        for item_key, value in player_data['inventory'].items():
            # Nếu value là một con số (dạng cũ), thì cần chuyển đổi
            if isinstance(value, int):
                is_old_format = True
                if value > 0:
                    # Chuyển đổi: {"harvest_wheat": 10} -> {"harvest_wheat": {"0": 10}}
                    new_inventory[item_key] = {"0": value} 
            else:
                # Nếu đã là dạng mới thì giữ nguyên
                new_inventory[item_key] = value

    if 'barn' in player_data and 'notification_sent' not in player_data['barn']:
        print(f"Thêm cờ thông báo barn cho người chơi {user_id_str}...")
        player_data['barn']['notification_sent'] = True
    
    if 'inventory' in player_data:
        inventory_copy = player_data['inventory'].copy()
        needs_migration = any(isinstance(value, int) for value in inventory_copy.values())
        
        if needs_migration:
            print(f"Nâng cấp dữ liệu inventory cho người chơi {user_id_str}...")
            new_inventory = {}
            for item_key, value in inventory_copy.items():
                if isinstance(value, int): # Nếu là dạng cũ (số nguyên)
                    if value > 0:
                        new_inventory[item_key] = {"0": value} 
                else: # Nếu đã là dạng mới (dict)
                    new_inventory[item_key] = value
            player_data['inventory'] = new_inventory

        if is_old_format:
            print(f"Nâng cấp dữ liệu inventory cho người chơi {user_id_str}...")
            player_data['inventory'] = new_inventory

    
    return player_data


# --- HÀM CHÍNH ĐỂ CHẠY DI CHUYỂN DỮ LIỆU ---
def run_migration():
    print("Bắt đầu quá trình di chuyển dữ liệu từ player_data.json sang MongoDB...")

    if not os.path.exists('player_data.json'):
        print("Lỗi: Không tìm thấy file player_data.json. Không có gì để di chuyển.")
        return

    with open('player_data.json', 'r') as f:
        try:
            old_data = json.load(f)
        except json.JSONDecodeError:
            print("Lỗi: File player_data.json bị hỏng.")
            return
            
    total_migrated = 0
    for user_id, player_data in old_data.items():
        print(f"--- Đang xử lý người chơi: {user_id} ---")
        
        # 1. Chạy qua hàm nâng cấp dữ liệu
        migrated_data = _migrate_player_data_from_json(user_id, player_data)
        
        # 2. Đẩy dữ liệu đã nâng cấp lên MongoDB
        try:
            player_collection.update_one(
                {'_id': user_id},
                {'$set': migrated_data},
                upsert=True
            )
            print(f"Đã di chuyển thành công dữ liệu cho người chơi {user_id}.")
            total_migrated += 1
        except Exception as e:
            print(f"Lỗi khi đẩy dữ liệu của người chơi {user_id} lên MongoDB: {e}")

    print(f"\n✅ Hoàn tất! Đã di chuyển dữ liệu cho {total_migrated} người chơi.")

if __name__ == "__main__":
    run_migration()