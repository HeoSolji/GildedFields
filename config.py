# config.py

import math

# --- Cài đặt chung ---
PLAYER_DATA_FILE = 'player_data.json'
CURRENCY_SYMBOL = "💰"
SECONDS_IN_A_DAY = 86400
SEED_SELL_MULTIPLIER = 0.5

# --- Cài đặt nông trại ---
FARM_GRID_SIZE = 3
INITIAL_PLOTS = FARM_GRID_SIZE * FARM_GRID_SIZE
FARM_UPGRADES = {
    4: {"cost": 10000, "level_required": 10},
    5: {"cost": 50000, "level_required": 25}
}
MAX_FARM_SIZE = 5

# --- Cài đặt chăn nuôi ---
INITIAL_BARN_CAPACITY = 5

# --- Cài đặt phần thưởng ---
DAILY_REWARD = 50
INITIAL_BALANCE = 100
REWARD_PER_LEVEL_UP = 200

# --- Biểu tượng (Emojis) ---
CROP_EMOJIS = {
    "wheat": "🌾", "carrot": "🥕", "corn": "🌽", "potato": "🥔",
    "strawberry": "🍓", "tomato": "🍅", "eggplant": "🍆", "broccoli": "🥦",
    "watermelon": "🍉", "onion": "🧅", "parsnip": "🥕", "cauliflower": "🥦",
    "kale": "🥬", "hot_pepper": "🌶️", "radish": "🥕", "pumpkin": "🎃",
    "bok_choy": "🥬", "yam": "🍠", "cranberries": "🍒",
}

PLOT_EMPTY_EMOJI = "🟫"
PLOT_READY_EMOJI = "✅"

# --- DỮ LIỆU CÂY TRỒNG ---
CROPS = {
    # Cây cũ đã được gán mùa
    "wheat": {"grow_time": 300, "sell_price": 10, "seed_price": 5, "display_name": "Lúa mì", "emoji": CROP_EMOJIS["wheat"], "seasons": ["spring", "summer", "fall"]},
    "carrot": {"grow_time": 600, "sell_price": 25, "seed_price": 10, "display_name": "Cà rốt", "emoji": CROP_EMOJIS["carrot"], "seasons": ["spring"]},
    "potato": {"grow_time": 1800, "sell_price": 80, "seed_price": 30, "display_name": "Khoai tây", "emoji": CROP_EMOJIS["potato"], "seasons": ["spring"]},
    "onion": {"grow_time": 750, "sell_price": 30, "seed_price": 12, "display_name": "Hành tây", "emoji": CROP_EMOJIS["onion"], "seasons": ["summer"]},
    "corn": {"grow_time": 1200, "sell_price": 50, "seed_price": 20, "display_name": "Ngô", "emoji": CROP_EMOJIS["corn"], "seasons": ["summer", "fall"]},
    "eggplant": {"grow_time": 2400, "sell_price": 110, "seed_price": 40, "display_name": "Cà tím", "emoji": CROP_EMOJIS["eggplant"], "seasons": ["fall"]},
    "broccoli": {"grow_time": 2100, "sell_price": 95, "seed_price": 35, "display_name": "Bông cải xanh", "emoji": CROP_EMOJIS["broccoli"], "seasons": ["fall"]},

    # Cây mới theo mùa
    "parsnip": {"grow_time": 400, "sell_price": 18, "seed_price": 8, "display_name": "Củ cải vàng", "emoji": CROP_EMOJIS["parsnip"], "seasons": ["spring"]},
    "cauliflower": {"grow_time": 1000, "sell_price": 90, "seed_price": 40, "display_name": "Súp lơ trắng", "emoji": CROP_EMOJIS["cauliflower"], "seasons": ["spring"]},
    "kale": {"grow_time": 600, "sell_price": 55, "seed_price": 25, "display_name": "Cải xoăn", "emoji": CROP_EMOJIS["kale"], "seasons": ["spring"]},
    "strawberry": {"grow_time": 900, "sell_price": 60, "seed_price": 50, "display_name": "Dâu tây", "emoji": CROP_EMOJIS["strawberry"], "seasons": ["spring"]},
    
    "tomato": {"grow_time": 1500, "sell_price": 30, "seed_price": 25, "display_name": "Cà chua", "emoji": CROP_EMOJIS["tomato"], "seasons": ["summer"]},
    "hot_pepper": {"grow_time": 500, "sell_price": 20, "seed_price": 10, "display_name": "Ớt cay", "emoji": CROP_EMOJIS["hot_pepper"], "seasons": ["summer"]},
    "radish": {"grow_time": 700, "sell_price": 45, "seed_price": 20, "display_name": "Củ cải đỏ", "emoji": CROP_EMOJIS["radish"], "seasons": ["summer"]},
    "watermelon": {"grow_time": 3600, "sell_price": 180, "seed_price": 60, "display_name": "Dưa hấu", "emoji": CROP_EMOJIS["watermelon"], "seasons": ["summer"]},
    
    "pumpkin": {"grow_time": 2800, "sell_price": 160, "seed_price": 50, "display_name": "Bí ngô", "emoji": CROP_EMOJIS["pumpkin"], "seasons": ["fall"]},
    "yam": {"grow_time": 1300, "sell_price": 80, "seed_price": 30, "display_name": "Khoai lang", "emoji": CROP_EMOJIS["yam"], "seasons": ["fall"]},
    "cranberries": {"grow_time": 700, "sell_price": 40, "seed_price": 60, "display_name": "Nam việt quất", "emoji": CROP_EMOJIS["cranberries"], "seasons": ["fall"]},
}

# --- DỮ LIỆU VẬT NUÔI ---
ANIMALS = {
    "chicken": {"display_name": "Gà", "emoji": "🐔", "buy_price": 200, "product_id": "egg", "production_time": 3600, "seasons": ["spring", "summer", "fall"]},
    "duck": {"display_name": "Vịt", "emoji": "🦆", "buy_price": 600, "product_id": "duck_egg", "production_time": 7200, "seasons": ["spring", "summer", "fall"]},
    "cow": {"display_name": "Bò", "emoji": "🐮", "buy_price": 1000, "product_id": "milk", "production_time": 14400, "seasons": ["spring", "summer", "fall", "winter"]},
    "goat": {"display_name": "Dê", "emoji": "🐐", "buy_price": 2000, "product_id": "goat_milk", "production_time": 28800, "seasons": ["spring", "summer", "fall", "winter"]},
    "sheep": {"display_name": "Cừu", "emoji": "🐑", "buy_price": 2500, "product_id": "wool", "production_time": 43200, "seasons": ["spring", "summer", "fall"]},
    "pig": {"display_name": "Heo", "emoji": "🐷", "buy_price": 5000, "product_id": "truffle", "production_time": 86400, "seasons": ["spring", "summer", "fall"]},
}

# --- DỮ LIỆU SẢN PHẨM ---
PRODUCTS = {
    "egg": {"display_name": "Trứng gà", "emoji": "🥚", "sell_price": 25},
    "duck_egg": {"display_name": "Trứng vịt", "emoji": "🥚", "sell_price": 50},
    "milk": {"display_name": "Sữa bò", "emoji": "🥛", "sell_price": 120},
    "goat_milk": {"display_name": "Sữa dê", "emoji": "🥛", "sell_price": 180},
    "wool": {"display_name": "Lông Cừu", "emoji": "🧶", "sell_price": 300},
    "truffle": {"display_name": "Nấm Truffle", "emoji": "🍄", "sell_price": 600},
}

# --- DỮ LIỆU XP ---
XP_PER_CROP = {
    "wheat": 5, "corn": 20, "parsnip": 8, "cauliflower": 35, "kale": 12, "strawberry": 18,
    "tomato": 15, "hot_pepper": 8, "radish": 20, "watermelon": 80, "pumpkin": 65,
    "yam": 30, "cranberries": 15, "carrot": 10, "potato": 35, "onion": 15,
    "eggplant": 50, "broccoli": 45
}

# --- DỮ LIỆU CÔNG THỨC ---
RECIPES = {
    "bread": {"display_name": "Bánh mì", "emoji": "🍞", "sell_price": 50, "ingredients": {"harvest_wheat": 3, "product_egg": 1}},
    "mayonnaise": {"display_name": "Sốt Mayonnaise", "emoji": "🧴", "sell_price": 100, "ingredients": {"product_egg": 2}},
    "cheese": {"display_name": "Phô mai bò", "emoji": "🧀", "sell_price": 300, "ingredients": {"product_milk": 2}},
    "goat_cheese": {"display_name": "Phô mai dê", "emoji": "🧀", "sell_price": 450, "ingredients": {"product_goat_milk": 1}},
}

ACHIEVEMENTS = {
    # ID thành tựu: { thông tin }
    "level_10": {
        "display_name": "Nông dân tập sự", "emoji": "🧑‍🌾",
        "description": "Đạt cấp độ 10.",
        "type": "level", "target_amount": 10,
        "reward": {"money": 1000, "xp": 500}
    },
    "level_25": {
        "display_name": "Lão nông tri điền", "emoji": "👨‍🌾",
        "description": "Đạt cấp độ 25.",
        "type": "level", "target_amount": 25,
        "reward": {"money": 5000, "xp": 2000}
    },
    "harvest_100_wheat": {
        "display_name": "Vựa lúa", "emoji": "🌾",
        "description": "Thu hoạch tổng cộng 100 Lúa mì.",
        "type": "harvest", "target_id": "wheat", "target_amount": 100,
        "reward": {"money": 500}
    },
    "harvest_50_corn": {
        "display_name": "Vua Ngô", "emoji": "🌽",
        "description": "Thu hoạch tổng cộng 50 Ngô.",
        "type": "harvest", "target_id": "corn", "target_amount": 50,
        "reward": {"money": 1000}
    },
    "craft_10_bread": {
        "display_name": "Thợ làm bánh", "emoji": "🍞",
        "description": "Chế tạo 10 Bánh mì.",
        "type": "craft", "target_id": "bread", "target_amount": 10,
        "reward": {"money": 750}
    },
    "earn_10000_money": {
        "display_name": "Tiểu phú nông", "emoji": "💰",
        "description": "Tích lũy được 10,000 tiền trong ví.",
        "type": "balance", "target_amount": 10000,
        "reward": {"xp": 1000}
    },
    "collect_50_eggs": {
        "display_name": "Người nuôi gà", "emoji": "🥚",
        "description": "Thu thập 50 Trứng gà.",
        "type": "collect", "target_id": "egg", "target_amount": 50,
        "reward": {"money": 1500}
    }
}


def get_grow_time_string(seconds):
    """Chuyển đổi giây sang chuỗi 'x phút y giây'."""
    if seconds < 3600:
        minutes = math.ceil(seconds / 60)
        return f"{minutes} phút"
    hours = math.floor(seconds / 3600)
    minutes = math.ceil((seconds % 3600) / 60)
    return f"{hours} giờ {minutes} phút"

def get_xp_for_level(level):
    """Tính toán lượng XP cần thiết để lên cấp độ tiếp theo."""
    # Công thức: 150 * (level ^ 1.5)
    return int(150 * (level ** 1.5))