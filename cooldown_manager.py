# cooldown_manager.py
import time
import config

# Dùng dict để lưu cooldown trong bộ nhớ
# Cấu trúc: { "command_name": { user_id: last_used_timestamp } }
_cooldowns = {}

# Mapping tên lệnh tới thời gian chờ đã định nghĩa trong config
COMMAND_COOLDOWNS = {
    "fish": config.FISHING_COOLDOWN,
    "explore": config.EXPLORATION_CONFIG['cooldown']
}

def check_cooldown(user_id, command_name):
    """Kiểm tra cooldown. Trả về 0 nếu sẵn sàng, hoặc số giây còn lại."""
    cooldown_duration = COMMAND_COOLDOWNS.get(command_name)
    if not cooldown_duration:
        return 0 # Lệnh không có cooldown

    last_used = _cooldowns.get(command_name, {}).get(user_id)
    if not last_used:
        return 0 # Chưa dùng bao giờ

    time_since_last_use = time.time() - last_used
    if time_since_last_use >= cooldown_duration:
        return 0 # Đã hết cooldown
    
    return cooldown_duration - time_since_last_use

def set_cooldown(user_id, command_name):
    """Đặt cooldown cho người dùng sau khi dùng lệnh."""
    if command_name not in _cooldowns:
        _cooldowns[command_name] = {}
    _cooldowns[command_name][user_id] = time.time()

def reset_cooldown(user_id, command_name):
    """Xóa cooldown cho người dùng."""
    if command_name in _cooldowns and user_id in _cooldowns[command_name]:
        del _cooldowns[command_name][user_id]
        return True # Xóa thành công
    return False # Không có gì để xóa