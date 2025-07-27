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

BARN_UPGRADES = {
    # new_capacity: {"cost": chi_phí, "level_required": cấp_độ_yêu_cầu}
    10: {"cost": 15000, "level_required": 15}, # Nâng lên sức chứa 10
    20: {"cost": 60000, "level_required": 30}  # Nâng lên sức chứa 20
}
MAX_BARN_CAPACITY = 20

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
    "ancient_fruit": "<:ancient_fruit:1398639919869722786>",
    "starfruit": "<:starfruit:1398639835711017012>",
    "crystal_fruit": "<:crystal_fruit:1398851638114127904>",
    "snowdrop": "<:snowdrop:1398851601841520650>",
    "winter_root": "<:winter_root:1398851676009533482>",
}

# Tỉ lệ ra cấp sao (cơ hội để đạt được cấp đó HOẶC CAO HƠN)
# 0 = Thường, 1 = Bạc, 2 = Vàng, 3 = Tím (Iridium)
STAR_QUALITY_CHANCE = {
    1: 0.30,  # 30% cơ hội để ra ít nhất 1 sao (Bạc)
    2: 0.15,  # 15% cơ hội để ra ít nhất 2 sao (Vàng)
    3: 0.05,  # 5% cơ hội để ra ít nhất 3 sao (Tím)
    5: 0.01   # 1% cơ hội để ra 5 sao (Khổng lồ)
}

# Hệ số nhân giá trị cho từng cấp sao
STAR_QUALITY_MULTIPLIER = {
    0: 1.0,   # Thường
    1: 1.25,  # Bạc: +25% giá trị
    2: 1.5,   # Vàng: +50% giá trị
    3: 2.0,   # Tím: +100% giá trị
    5: 9.0    # Khổng lồ (5 sao)
}

# Ra khơi config
EXPLORATION_CONFIG = {
    "cost": 1000, # Chi phí cho mỗi chuyến đi
    "cooldown": 600, # Thời gian chờ (12 giờ)
    "rewards": {
        "nothing_chance": 0.69, # 50% không tìm thấy gì
        "money_chance": 0.3,   # 30% tìm thấy tiền
        "seed_chance": 0.01,    # 20% tìm thấy hạt giống bí ẩn
        "min_money": 500,
        "max_money": 3000
    }
}
# Emoji cho từng cấp sao
STAR_EMOJIS = {
    1: "⭐", # Bạc
    2: "🌟", # Vàng
    3: "✨", # Tím
    5: "👑",  # Khổng lồ
    0: ""
}

PLOT_EMPTY_EMOJI = "🟫"
# PLOT_READY_EMOJI = "✅"
PLOT_FROZEN_EMOJI = "🧊"
SEEDLING_EMOJI = "🌱" # Giai đoạn mầm
SAPLING_EMOJI = "🌿"  # Giai đoạn cây non
# --- DỮ LIỆU CÂY TRỒNG ---
CROPS = {
    # Mùa Xuân
    "wheat": {"grow_time": 120, "sell_price": 10, "seed_price": 5, "display_name": "Lúa mì", "emoji": CROP_EMOJIS["wheat"], "seasons": ["spring", "summer", "fall", "winter"]}, # 2 phút
    "parsnip": {"grow_time": 240, "sell_price": 18, "seed_price": 8, "display_name": "Củ cải vàng", "emoji": CROP_EMOJIS["parsnip"], "seasons": ["spring"]}, # 4 phút
    "carrot": {"grow_time": 480, "sell_price": 25, "seed_price": 10, "display_name": "Cà rốt", "emoji": CROP_EMOJIS["carrot"], "seasons": ["spring"]}, # 8 phút
    "kale": {"grow_time": 600, "sell_price": 55, "seed_price": 25, "display_name": "Cải xoăn", "emoji": CROP_EMOJIS["kale"], "seasons": ["spring"]}, # 10 phút
    "potato": {"grow_time": 900, "sell_price": 80, "seed_price": 30, "display_name": "Khoai tây", "emoji": CROP_EMOJIS["potato"], "seasons": ["spring"]}, # 15 phút
    "cauliflower": {"grow_time": 1500, "sell_price": 90, "seed_price": 40, "display_name": "Súp lơ trắng", "emoji": CROP_EMOJIS["cauliflower"], "seasons": ["spring"]}, # 25 phút
    "strawberry": {"grow_time": 1800, "sell_price": 60, "seed_price": 50, "display_name": "Dâu tây", "emoji": CROP_EMOJIS["strawberry"], "seasons": ["spring"]}, # 30 phút

    # Mùa Hạ
    "hot_pepper": {"grow_time": 300, "sell_price": 20, "seed_price": 10, "display_name": "Ớt cay", "emoji": CROP_EMOJIS["hot_pepper"], "seasons": ["summer"]}, # 5 phút
    "onion": {"grow_time": 600, "sell_price": 30, "seed_price": 12, "display_name": "Hành tây", "emoji": CROP_EMOJIS["onion"], "seasons": ["summer"]}, # 10 phút
    "radish": {"grow_time": 900, "sell_price": 45, "seed_price": 20, "display_name": "Củ cải đỏ", "emoji": CROP_EMOJIS["radish"], "seasons": ["summer"]}, # 15 phút
    "tomato": {"grow_time": 1200, "sell_price": 30, "seed_price": 25, "display_name": "Cà chua", "emoji": CROP_EMOJIS["tomato"], "seasons": ["summer"]}, # 20 phút
    "corn": {"grow_time": 1500, "sell_price": 50, "seed_price": 20, "display_name": "Ngô", "emoji": CROP_EMOJIS["corn"], "seasons": ["summer", "fall"]}, # 25 phút
    "watermelon": {"grow_time": 1800, "sell_price": 180, "seed_price": 60, "display_name": "Dưa hấu", "emoji": CROP_EMOJIS["watermelon"], "seasons": ["summer"]}, # 30 phút

    # Mùa Thu
    "cranberries": {"grow_time": 420, "sell_price": 40, "seed_price": 60, "display_name": "Nam việt quất", "emoji": CROP_EMOJIS["cranberries"], "seasons": ["fall"]}, # 7 phút
    "yam": {"grow_time": 900, "sell_price": 80, "seed_price": 30, "display_name": "Khoai lang", "emoji": CROP_EMOJIS["yam"], "seasons": ["fall"]}, # 15 phút
    "broccoli": {"grow_time": 1200, "sell_price": 95, "seed_price": 35, "display_name": "Bông cải xanh", "emoji": CROP_EMOJIS["broccoli"], "seasons": ["fall"]}, # 20 phút
    "eggplant": {"grow_time": 1500, "sell_price": 110, "seed_price": 40, "display_name": "Cà tím", "emoji": CROP_EMOJIS["eggplant"], "seasons": ["fall"]}, # 25 phút
    "pumpkin": {"grow_time": 1800, "sell_price": 160, "seed_price": 50, "display_name": "Bí ngô", "emoji": CROP_EMOJIS["pumpkin"], "seasons": ["fall"]}, # 30 phút

    # Mùa Đông
    "snowdrop": {"grow_time": 600, "sell_price": 35, "seed_price": 15, "display_name": "Hoa Tuyết", "emoji": CROP_EMOJIS["snowdrop"], "seasons": ["winter"]}, # 10 phút
    "winter_root": {"grow_time": 900, "sell_price": 60, "seed_price": 25, "display_name": "Củ Mùa Đông", "emoji": CROP_EMOJIS["winter_root"], "seasons": ["winter"]}, # 15 phút
    "crystal_fruit": {"grow_time": 1800, "sell_price": 70, "seed_price": 30, "display_name": "Quả Pha Lê", "emoji": CROP_EMOJIS["crystal_fruit"], "seasons": ["winter"]}, # 30 phút

    # Cây đặc biệt (trên 30 phút)
    "starfruit": {"grow_time": 28800, "sell_price": 5000, "seed_price": 0, "display_name": "Quả Khế", "emoji": CROP_EMOJIS["starfruit"], "seasons": ["summer"]}, # 8 giờ
    "ancient_fruit": {"grow_time": 86400, "sell_price": 10000, "seed_price": 0, "display_name": "Quả Cổ Đại", "emoji": CROP_EMOJIS["ancient_fruit"], "seasons": ["spring", "summer", "fall"]}, # 24 giờ
}

# --- CẤU HÌNH CÂY KHỔNG LỒ ---
GIANT_CROP_CANDIDATES = ["cauliflower", "watermelon", "pumpkin"] # Các loại cây có thể thành khổng lồ
GIANT_CROP_CHANCE = 0.01  # 1% tỉ lệ
GIANT_CROP_YIELD_MULTIPLIER = 9 # Sản lượng nhận được

# --- DỮ LIỆU VẬT NUÔI ---
ANIMALS = {
    "chicken": {"display_name": "Gà", "emoji": "🐔", "buy_price": 200, "product_id": "egg", "production_time": 900, "seasons": ["spring", "summer", "fall", "winter"]},       # 15 phút
    "duck": {"display_name": "Vịt", "emoji": "🦆", "buy_price": 600, "product_id": "duck_egg", "production_time": 1200, "seasons": ["spring", "summer", "fall", "winter"]},    # 20 phút
    "sheep": {"display_name": "Cừu", "emoji": "🐑", "buy_price": 2500, "product_id": "wool", "production_time": 1500, "seasons": ["spring", "summer", "fall", "winter"]},   # 25 phút
    "goat": {"display_name": "Dê", "emoji": "🐐", "buy_price": 2000, "product_id": "goat_milk", "production_time": 1800, "seasons": ["spring", "summer", "fall", "winter"]}, # 30 phút
    "cow": {"display_name": "Bò", "emoji": "🐮", "buy_price": 1000, "product_id": "milk", "production_time": 1800, "seasons": ["spring", "summer", "fall", "winter"]},    # 30 phút
    "pig": {"display_name": "Heo", "emoji": "🐷", "buy_price": 5000, "product_id": "truffle", "production_time": 1800, "seasons": ["spring", "summer", "fall","winter"]},   # 30 phút
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
    "eggplant": 50, "broccoli": 45, "snowdrop": 15, "winter_root": 25,
    "crystal_fruit": 30,
}

# --- DỮ LIỆU CÔNG THỨC ---
RECIPES = {
    "bread": {"display_name": "Bánh mì", "emoji": "🍞", "sell_price": 50, "ingredients": {"harvest_wheat": 3, "product_egg": 1}},
    "mayonnaise": {"display_name": "Sốt Mayonnaise", "emoji": "🧴", "sell_price": 100, "ingredients": {"product_egg": 2}},
    "cheese": {"display_name": "Phô mai bò", "emoji": "🧀", "sell_price": 300, "ingredients": {"product_milk": 2}},
    "goat_cheese": {"display_name": "Phô mai dê", "emoji": "🧀", "sell_price": 450, "ingredients": {"product_goat_milk": 1}},
    "seed_maker": {
    "display_name": "Máy Tạo Hạt Giống",
    "emoji": "🖨️",
    "sell_price": 0,
    "ingredients": {
        "harvest_wheat": 50,
        "harvest_corn": 25 
    },
    "type": "machine"
    },
    "pumpkin_pie": {
        "display_name": "Bánh Bí Ngô", "emoji": "🥧", "sell_price": 350,
        "ingredients": {"harvest_pumpkin": 1, "harvest_wheat": 1, "product_egg": 1},
        "type": "item",
        "unlocked_by": "rep_johnson_1" # Đánh dấu là công thức cần mở khóa
    },
    "quality_bait": {
        "display_name": "Mồi Câu Xịn", "emoji": "🐛", "sell_price": 20,
        "ingredients": {"fish_carp": 2},
        "type": "item",
        "unlocked_by": "rep_barry_1"
    }
}

ACHIEVEMENTS = {
    # ID thành tựu: { thông tin }
    "level_10": {
        "display_name": "Nông dân tập sự", "emoji": "🧑‍🌾",
        "description": "Đạt cấp độ 10.",
        "type": "level", "target_amount": 10,
        "reward": {"money": 1000, "xp": 500},
        "hidden": False
    },
    "level_25": {
        "display_name": "Lão nông tri điền", "emoji": "👨‍🌾",
        "description": "Đạt cấp độ 25.",
        "type": "level", "target_amount": 25,
        "reward": {"money": 5000, "xp": 2000},
        "hidden": False
    },
    "farm_upgrade_1": {
        "display_name": "Mở rộng lãnh thổ", "emoji": "🏞️",
        "description": "Nâng cấp nông trại lên 4x4.",
        "type": "farm_size", "target_amount": 4,
        "reward": {"money": 2500},
        "hidden": False
    },
    "earn_100000_money": {
        "display_name": "Triệu phú nông dân", "emoji": "💰",
        "description": "Tích lũy được 100,000 tiền trong ví.",
        "type": "balance", "target_amount": 100000,
        "reward": {"xp": 5000},
        "hidden": False
    },
    
    # --- Thành tựu Trồng trọt ---
    "harvest_total_500": {
        "display_name": "Bàn tay vàng", "emoji": "🧤",
        "description": "Thu hoạch tổng cộng 500 nông sản.",
        "type": "harvest_total", "target_amount": 500,
        "reward": {"money": 2000},
        "hidden": False
    },
    "harvest_100_wheat": {
        "display_name": "Vựa lúa", "emoji": "🌾",
        "description": "Thu hoạch 100 Lúa mì.",
        "type": "harvest", "target_id": "wheat", "target_amount": 100,
        "reward": {"money": 500},
        "hidden": False
    },
    "harvest_giant_crop": {
        "display_name": "Thần nông đãi", "emoji": "👑",
        "description": "Thu hoạch được một cây trồng khổng lồ.",
        "type": "harvest_quality", "target_quality": 5, "target_amount": 1,
        "reward": {"money": 10000},
        "hidden": True
    },
    "harvest_all_crops": {
        "display_name": "Bách khoa toàn thư Nông nghiệp", "emoji": "📚",
        "description": "Thu hoạch được ít nhất một lần mỗi loại cây trồng.",
        "type": "collection", "category": "harvest", "target_amount": len(CROPS), # Tự động đếm
        "reward": {"xp": 10000},
        "hidden": False
    },

    # --- Thành tựu Chăn nuôi ---
    "collect_total_250": {
        "display_name": "Nhà chăn nuôi", "emoji": "🏡",
        "description": "Thu thập tổng cộng 250 sản phẩm từ vật nuôi.",
        "type": "collect_total", "target_amount": 250,
        "reward": {"money": 2500},
        "hidden": False
    },
    "collect_50_milk": {
        "display_name": "Chuyên gia vắt sữa", "emoji": "🥛",
        "description": "Thu thập 50 Sữa bò.",
        "type": "collect", "target_id": "milk", "target_amount": 50,
        "reward": {"money": 1500},
        "hidden": False
    },

    # --- Thành tựu Chế tạo & Câu cá ---
    "craft_25_bread": {
        "display_name": "Thợ làm bánh", "emoji": "🍞",
        "description": "Chế tạo 25 Bánh mì.",
        "type": "craft", "target_id": "bread", "target_amount": 25,
        "reward": {"money": 1000},
        "hidden": False
    },
    "fish_100_total": {
        "display_name": "Cần thủ", "emoji": "🎣",
        "description": "Câu được 100 con cá.",
        "type": "fish_total", "target_amount": 100,
        "reward": {"money": 2000},
        "hidden": False
    },
    "fish_legendary": {
        "display_name": "Huyền thoại biển cả", "emoji": "🏆",
        "description": "Câu được một con Cá Thần.",
        "type": "fish", "target_id": "legendary_fish", "target_amount": 1,
        "reward": {"money": 20000, "xp": 10000},
        "hidden": True
    },

    # --- Thành tựu Xã hội ---
    "gift_sent": {
        "display_name": "Người bạn hào phóng", "emoji": "🎁",
        "description": "Tặng một món quà cho người chơi khác.",
        "type": "gift", "target_amount": 1,
        "reward": {"xp": 500},
        "hidden": True
    }
}

MARKET_EVENT_CHANNEL_ID =1395769117944053780 
# 1393757875964215377

PRICE_MODIFIERS = {
    "high_demand": 1.5,  # Tăng 50%
    "surplus": 0.7,      # Giảm 30%
    "stable": 1.0        # Bình ổn
}


# Dữ liệu các loại cá
# { "tên_hệ_thống": { "tên_hiển_thị": ..., "emoji": ..., "giá_bán": ..., "độ_hiếm": ... } }
FISHING_COOLDOWN = 30 # Thời gian chờ giữa mỗi lần câu (giây)

FISH = {
    "carp": {"display_name": "Cá Chép", "emoji": "🐟", "sell_price": 30, "rarity": 0.5},
    "bream": {"display_name": "Cá Vền", "emoji": "🐠", "sell_price": 45, "rarity": 0.3},
    "catfish": {"display_name": "Cá Trê", "emoji": "🐡", "sell_price": 200, "rarity": 0.1},
    "legendary_fish": {"display_name": "Cá Thần", "emoji": "👑", "sell_price": 5000, "rarity": 0.01},
}

# --- THÊM CẤU HÌNH MỚI CHO XEN CANH ---

# Danh sách các cặp cây có thể xen canh và phần thưởng
# Cấu trúc: { "id_cây_1": {"partner": "id_cây_2", "bonus": phần_trăm_giảm} }
# Phần thưởng sẽ được áp dụng cho cả hai cây.
COMPANION_PLANTS = {
    "corn": {"partner": "wheat", "bonus": 0.40},  # Ngô và Lúa mì: giảm 15% thời gian
    "tomato": {"partner": "carrot", "bonus": 0.40} # Cà chua và Cà rốt: giảm 20% thời gian
}
COMPANION_BONUS_EMOJI = "✨"

# --- THÊM CẤU HÌNH MỚI CHO MÁY TẠO HẠT GIỐNG ---
SEED_MAKER_CONFIG = {
    "time_per_item": 60,
    "blacklist": ["starfruit", "ancient_fruit"],
    "chance_same_seed": 0.95,  # 95% ra hạt giống cùng loại
    "min_same_seed": 1,
    "max_same_seed": 2,
    "chance_mixed_seeds": 0.04, # 4% ra hạt hỗn hợp
    "min_mixed_seeds": 1,
    "max_mixed_seeds": 3,
    # 1% còn lại sẽ là cơ hội ra hạt hiếm
}

# --- THÊM CẤU HÌNH MỚI CHO HỆ THỐNG NHIỆM VỤ ---

QUEST_CONFIG = {
    "daily_quest_count": 2,       # Số nhiệm vụ hàng ngày mỗi người chơi nhận được
    "special_bounty_chance": 0.25 # 25% cơ hội xuất hiện nhiệm vụ đặc biệt mỗi ngày
}

# Định nghĩa các NPC
QUEST_NPCS = {
    "johnson": {"name": "Lão nông Johnson", "emoji": "🧑‍🌾"},
    "barry": {"name": "Thuyền trưởng Barry", "emoji": "🎣"}
}

# Kho nhiệm vụ (Quest Pool)
QUEST_POOL = {
    "daily": [
        {"id": "d_collect_carrot", "npc": "johnson", "type": "collect", "target_id": "harvest_carrot", "target_amount": 15, "title": "Món hầm cho bữa tối", "objective": "Mang cho tôi **{amount}** {emoji} **{name}**.", "reward": {"money": 200, "xp": 50, "rep": 10}},
        {"id": "d_collect_wheat", "npc": "johnson", "type": "collect", "target_id": "harvest_wheat", "target_amount": 20, "title": "Nghiền bột làm bánh", "objective": "Tôi cần **{amount}** {emoji} **{name}** để chuẩn bị cho mẻ bánh mới.", "reward": {"money": 150, "xp": 40, "rep": 10}},
        {"id": "d_collect_egg", "npc": "johnson", "type": "collect", "target_id": "product_egg", "target_amount": 5, "title": "Bữa sáng thịnh soạn", "objective": "Hãy tìm giúp tôi **{amount}** {emoji} **{name}** chất lượng nhé.", "reward": {"money": 250, "xp": 60, "rep": 15}},
        {"id": "d_fish_carp", "npc": "barry", "type": "collect", "target_id": "fish_carp", "target_amount": 3, "title": "Mồi câu hảo hạng", "objective": "Các loài cá lớn rất thích ăn **{name}**, hãy câu **{amount}** con {emoji} **{name}** giúp tôi để làm mồi câu.", "reward": {"money": 300, "xp": 70, "rep": 15}},
        {"id": "d_action_harvest", "npc": "johnson", "type": "action_harvest", "target_amount": 20, "title": "Giúp một tay việc đồng áng", "objective": "Lưng tôi đau quá, cậu thu hoạch giúp tôi **{amount}** cây trồng bất kỳ được không?", "reward": {"money": 100, "xp": 100, "rep": 5}},
        {"id": "d_action_fish", "npc": "barry", "type": "action_fish", "target_amount": 10, "title": "Một ngày đi câu", "objective": "Hôm nay biển lặng, hãy thử tài câu **{amount}** con cá xem sao!", "reward": {"money": 150, "xp": 120, "rep": 10}},
    ],
    "special": [
        {"id": "s_collect_corn_large", "npc": "johnson", "type": "collect", "target_id": "harvest_corn", "target_amount": 100, "title": "Đơn hàng lớn cho lễ hội", "duration_days": 3, "objective": "Lễ hội sắp đến rồi! Hãy giúp tôi thu thập **{amount}** {emoji} **{name}**.", "reward": {"money": 5000, "xp": 1000, "rep": 50}},
        {"id": "s_collect_cheese_gold", "npc": "johnson", "type": "collect_quality", "target_id": "crafted_cheese", "target_quality": 2, "target_amount": 10, "title": "Đặc sản cho nhà hàng", "duration_days": 3, "objective": "Một nhà hàng 5 sao muốn đặt **{amount}** {emoji} **{name}** chất lượng Vàng 🌟.", "reward": {"money": 7500, "xp": 1500, "rep": 75}},
        {"id": "s_fish_catfish", "npc": "barry", "type": "collect", "target_id": "fish_catfish", "target_amount": 5, "title": "Treo thưởng Cá Trê", "duration_days": 3, "objective": "Tôi nghe đồn có một con {emoji} **{name}** rất lớn ở hồ. Cậu câu giúp tôi **{amount}** con được không?", "reward": {"money": 6000, "xp": 1200, "rep": 60}},
    ]
}

# Các mốc phần thưởng dựa trên điểm thân thiện
# Cấu trúc: { "npc_id": { level: {"type": "...", "data": ...} } }
REPUTATION_REWARDS = {
    "johnson": {
        50: {"type": "recipe", "id": "pumpkin_pie", "message": "Này cháu, ta thấy cháu rất chăm chỉ. Đây là công thức làm Bánh Bí Ngô gia truyền của ta, xem như là một món quà nhỏ!"},
        100: {"type": "gift", "item_key": "seed_starfruit", "amount": 1, "message": "Ta coi cháu như người nhà vậy. Ta tìm được một loại hạt giống rất hiếm trong chuyến đi vừa rồi, ta nghĩ cháu sẽ biết cách chăm sóc nó."}
    },
    "barry": {
        50: {"type": "recipe", "id": "quality_bait", "message": "Này nhóc, ta thấy tố chất của một tay câu cừ khôi trong cậu. Cầm lấy công thức làm Mồi Câu Xịn này, nó sẽ giúp cậu câu được cá to hơn đấy!"}
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