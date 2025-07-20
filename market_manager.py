# market_manager.py

import random
import config
import operator

# --- DỮ LIỆU MỚI ĐỂ THEO DÕI ---
sales_volume = {} # Ví dụ: {"harvest_wheat": 150}
current_modifiers = {}
current_event_message = "Thị trường hôm nay bình ổn."

def record_sale(item_key, amount):
    """Ghi nhận lại một giao dịch bán vật phẩm."""
    if item_key.startswith("harvest_") or item_key.startswith("product_"):
        sales_volume[item_key] = sales_volume.get(item_key, 0) + amount
        print(f"Ghi nhận bán: {amount} {item_key}. Tổng: {sales_volume[item_key]}")

def generate_supply_demand_events():
    """Tự động tạo sự kiện dựa trên dữ liệu Cung & Cầu một cách thông minh hơn."""
    global current_modifiers, current_event_message, sales_volume
    current_modifiers.clear()

    if not sales_volume:
        current_event_message = "Thị trường hôm nay tĩnh lặng do không có giao dịch nào được ghi nhận."
        # Reset lại sales_volume ở cuối hàm, không cần return sớm
    else:
        # Tìm vật phẩm được bán nhiều nhất (Dư thừa)
        surplus_item_key = max(sales_volume.items(), key=operator.itemgetter(1))[0]
        current_modifiers[surplus_item_key] = config.PRICE_MODIFIERS["surplus"]
        
        # Tạo thông báo cho vật phẩm dư thừa
        surplus_type, surplus_id = surplus_item_key.split('_', 1)
        surplus_info = (config.CROPS if surplus_type == 'harvest' else config.PRODUCTS).get(surplus_id)
        msg1 = f"Do nguồn cung dồi dào, giá của {surplus_info['emoji']} **{surplus_info['display_name']}** tạm thời **giảm**."

        # Tạo danh sách các ứng viên cho vật phẩm khan hiếm (loại trừ vật phẩm dư thừa)
        rare_candidates = {key: value for key, value in sales_volume.items() if key != surplus_item_key}

        # Chỉ tạo sự kiện khan hiếm nếu có ít nhất một ứng viên khác
        if rare_candidates:
            # Sắp xếp các ứng viên theo số lượng bán tăng dần
            sorted_rare = sorted(rare_candidates.items(), key=operator.itemgetter(1))
            # Chọn ngẫu nhiên trong 3 vật phẩm bán ít nhất (hoặc ít hơn nếu không đủ 3)
            rare_item_key = random.choice(sorted_rare[:3])[0]
            
            current_modifiers[rare_item_key] = config.PRICE_MODIFIERS["high_demand"]
            
            rare_type, rare_id = rare_item_key.split('_', 1)
            rare_info = (config.CROPS if rare_type == 'harvest' else config.PRODUCTS).get(rare_id)
            msg2 = f"Trong khi đó, {rare_info['emoji']} **{rare_info['display_name']}** đang trở nên khan hiếm, khiến giá **tăng vọt**!"
            
            current_event_message = f"{msg1}\n{msg2}"
        else:
            # Nếu chỉ có một loại vật phẩm được bán, chỉ thông báo giảm giá
            current_event_message = msg1
            
    # Reset lại dữ liệu bán hàng cho ngày tiếp theo
    sales_volume.clear()

def get_price_modifier(item_key):
    """Lấy hệ số nhân giá cho một vật phẩm."""
    return current_modifiers.get(item_key, 1.0)