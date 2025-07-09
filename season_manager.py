# season_manager.py

import datetime

SEASONS = {
    0: {"name": "spring", "display": "Mùa Xuân", "emoji": "🌷"},
    1: {"name": "summer", "display": "Mùa Hạ", "emoji": "☀️"},
    2: {"name": "fall", "display": "Mùa Thu", "emoji": "🍂"},
    3: {"name": "winter", "display": "Mùa Đông", "emoji": "❄️"},
}

def get_current_season():
    """Xác định mùa hiện tại dựa trên tuần trong tháng."""
    today = datetime.date.today()
    day_of_month = today.day

    # Tính toán tuần trong tháng (Tuần 1: ngày 1-7, Tuần 2: ngày 8-14, etc.)
    week_of_month = (day_of_month - 1) // 7 + 1
    season_index = (week_of_month - 1) % 4
    
    return SEASONS[season_index]

def get_season_emoji(season_name):
    """Lấy emoji cho một mùa cụ thể."""
    for s_id, s_info in SEASONS.items():
        if s_info['name'] == season_name:
            return s_info['emoji']
    return ""