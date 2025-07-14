# data_manager.py

import json
import os
import config # Import file cấu hình

# Biến toàn cục để lưu trữ dữ liệu trong bộ nhớ
GAME_DATA = {}

def _migrate_player_data(user_id_str, player_data):
    """Kiểm tra và nâng cấp cấu trúc dữ liệu của người chơi nếu cần."""
    # Nâng cấp cấu trúc Farm (Giữ nguyên)
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

def load_player_data():
    """Tải dữ liệu và tự động nâng cấp cấu trúc cho người chơi cũ."""
    global GAME_DATA
    if os.path.exists(config.PLAYER_DATA_FILE):
        with open(config.PLAYER_DATA_FILE, 'r') as f:
            loaded_data = json.load(f)
            # Chạy qua từng người chơi để nâng cấp nếu cần
            for user_id, player_data in loaded_data.items():
                GAME_DATA[user_id] = _migrate_player_data(user_id, player_data)
    else:
        GAME_DATA = {}
    print(f"Đã tải dữ liệu của {len(GAME_DATA)} người chơi.")

def save_player_data():
    """Lưu dữ liệu người chơi từ bộ nhớ vào file JSON."""
    with open(config.PLAYER_DATA_FILE, 'w') as f:
        json.dump(GAME_DATA, f, indent=4)
    # print(f"Đã lưu dữ liệu của {len(GAME_DATA)} người chơi.") # Có thể bỏ comment để debug

def get_player_data(user_id):
    """Lấy dữ liệu của một người chơi. Trả về None nếu chưa đăng ký."""
    return GAME_DATA.get(str(user_id))

def initialize_player(user_id):
    """Khởi tạo dữ liệu cho người chơi mới với cấu trúc farm mới."""
    user_id_str = str(user_id)
    if user_id_str not in GAME_DATA:
        initial_farm_plots = {
            f"{r}_{c}": None 
            for r in range(config.FARM_GRID_SIZE) 
            for c in range(config.FARM_GRID_SIZE)
        }

        GAME_DATA[user_id_str] = {
            "balance": config.INITIAL_BALANCE,
            "inventory": {},
            # --- CẤU TRÚC FARM MỚI ---
            "farm": {
                "size": config.FARM_GRID_SIZE,
                "plots": initial_farm_plots,
                "notification_sent": True
            },

            "barn": {
                "capacity": config.INITIAL_BARN_CAPACITY,
                "animals": {},
                "notification_sent": True
            },
            # --------------------------
            "last_daily_claim": None,
            "level": 1,
            "xp": 0,
            "achievements": {
            "unlocked": [], # Danh sách ID các thành tựu đã mở khóa
            "progress": {}  # Dữ liệu theo dõi tiến độ, ví dụ: {"harvest_wheat": 50}
            }
        }
        print(f"Đã khởi tạo dữ liệu cho người chơi {user_id_str}")
        save_player_data() 
        return True 
    return False 