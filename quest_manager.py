# quest_manager.py
import time, random, math
import config, data_manager, season_manager

SECONDS_IN_A_DAY = 86400

def get_new_quests(user_data):
    """Làm mới nhiệm vụ hàng ngày cho người chơi một cách thông minh theo mùa."""
    user_quests = user_data.setdefault('quests', {})
    last_updated = user_quests.get('last_updated', 0)
    
    if time.time() - last_updated < SECONDS_IN_A_DAY:
    # if False:
        return

    print(f"Làm mới nhiệm vụ cho người chơi...")
    
    # --- LOGIC MỚI: NHẬN BIẾT MÙA ---
    current_season = season_manager.get_current_season()['name']
    
    # Lọc kho nhiệm vụ hàng ngày để chỉ lấy các nhiệm vụ hợp lệ với mùa hiện tại
    available_daily_pool = []
    for quest_template in config.QUEST_POOL['daily']:
        quest_type = quest_template.get('type')
        target_id = quest_template.get('target_id')
        
        # Nếu là nhiệm vụ thu thập, kiểm tra xem vật phẩm có kiếm được trong mùa không
        if quest_type == 'collect' and target_id:
            item_type = target_id.split('_', 1)[0]
            item_name = target_id.split('_', 1)[1]
            
            if item_type == 'harvest': # Nếu là nông sản
                crop_info = config.CROPS.get(item_name)
                if crop_info and current_season in crop_info.get('seasons', []):
                    available_daily_pool.append(quest_template)
            
            # (Có thể thêm logic tương tự cho cá, etc. nếu cần)
            else: # Mặc định cho phép các loại khác như trứng, sữa...
                 available_daily_pool.append(quest_template)
        
        else: # Nếu là nhiệm vụ hành động (action), luôn cho phép
            available_daily_pool.append(quest_template)
    
    # --------------------------------

    user_quests['daily'] = []
    
    # Xóa nhiệm vụ đặc biệt đã hết hạn
    special = user_quests.get('special')
    if special and time.time() >= special.get('expires_at', float('inf')):
        user_quests['special'] = None

    # Tạo nhiệm vụ hàng ngày mới
    if available_daily_pool:
        chosen_quests = random.sample(available_daily_pool, k=min(config.QUEST_CONFIG['daily_quest_count'], len(available_daily_pool)))
        for quest_data in chosen_quests:
            new_quest = quest_data.copy()
            new_quest['progress'] = 0
            user_quests['daily'].append(new_quest)

    # Cơ hội tạo nhiệm vụ đặc biệt mới (nếu chưa có)
    if not user_quests.get('special') and random.random() < config.QUEST_CONFIG['special_bounty_chance']:
        special_pool = config.QUEST_POOL['special']
        chosen_bounty = random.choice(special_pool).copy()
        chosen_bounty['progress'] = 0
        chosen_bounty['expires_at'] = time.time() + (chosen_bounty['duration_days'] * SECONDS_IN_A_DAY)
        user_quests['special'] = chosen_bounty

    user_quests['last_updated'] = time.time()

def check_reputation_rewards(user_data, npc_id):
    """
    Kiểm tra các mốc phần thưởng, cập nhật dữ liệu và trả về danh sách các phần thưởng vừa mở khóa.
    Hàm này không còn là async và không gửi tin nhắn.
    """
    newly_unlocked_rewards = []
    user_quests = user_data.setdefault('quests', {})
    user_rep = user_quests.setdefault('reputation', {}).get(npc_id, 0)
    
    npc_rewards = config.REPUTATION_REWARDS.get(npc_id, {})
    
    for rep_level, reward_info in npc_rewards.items():
        if user_rep >= rep_level:
            reward_type = reward_info['type']
            
            if reward_type == 'recipe':
                reward_id = reward_info.get('id')
                unlocked_list = user_quests.setdefault('unlocked_recipes', [])
                if reward_id not in unlocked_list:
                    unlocked_list.append(reward_id)
                    newly_unlocked_rewards.append(reward_info) # Thêm vào danh sách báo cáo
            
            elif reward_type == 'gift':
                reward_id = f"gift_{npc_id}_{rep_level}"
                unlocked_list = user_quests.setdefault('unlocked_gifts', [])
                if reward_id not in unlocked_list:
                    unlocked_list.append(reward_id)
                    item_key = reward_info.get('item_key')
                    amount = reward_info.get('amount', 1)
                    user_data['inventory'].setdefault(item_key, {})['0'] = user_data['inventory'].setdefault(item_key, {}).get('0', 0) + amount
                    newly_unlocked_rewards.append(reward_info) # Thêm vào danh sách báo cáo

    return newly_unlocked_rewards

async def update_quest_progress(interaction, event_type, **kwargs):
    """
    Cập nhật tiến độ nhiệm vụ hành động và tự động hoàn thành nếu đủ điều kiện.
    """
    user_data = data_manager.get_player_data(interaction.user.id)
    if not user_data: return

    user_quests = user_data.setdefault('quests', {})
    active_quests = user_quests.get('daily', []) + ([user_quests.get('special')] if user_quests.get('special') else [])
    
    quest_completed_this_action = False
    for quest in active_quests:
        # Dùng quest_id để tra cứu thông tin gốc từ config, đảm bảo luôn mới nhất
        quest_id = quest.get('id')
        quest_template = next((q for q_list in config.QUEST_POOL.values() for q in q_list if q['id'] == quest_id), None)
        
        # Bỏ qua nếu không tìm thấy quest trong config hoặc không phải loại hành động
        if not quest_template or quest_template.get('type') != event_type:
            continue

        # Tăng tiến độ
        quest['progress'] = quest.get('progress', 0) + kwargs.get('amount', 1)
        
        # Kiểm tra hoàn thành
        if quest['progress'] >= quest_template.get('target_amount', float('inf')):
            quest_completed_this_action = True
            
            # Xóa nhiệm vụ khỏi danh sách đang hoạt động
            if quest in user_quests.get('daily', []):
                user_quests['daily'].remove(quest)
            elif quest == user_quests.get('special'):
                user_quests['special'] = None
            
            # Trao thưởng
            reward = quest_template.get('reward', {})
            user_data['balance'] += reward.get('money', 0)
            user_data['xp'] += reward.get('xp', 0)
            npc_id = quest_template.get('npc')

            if npc_id:
                rep_data = user_quests.setdefault('reputation', {})
                rep_data[npc_id] = rep_data.get(npc_id, 0) + reward.get('rep', 0)
                
                # Kiểm tra phần thưởng thân thiện và gửi thông báo nếu có
                newly_unlocked = check_reputation_rewards(user_data, npc_id)
                for reward_info in newly_unlocked:
                    npc_name = config.QUEST_NPCS.get(npc_id, {}).get('name', 'Một người bạn')
                    embed = discord.Embed(color=discord.Color.green())
                    
                    if reward_info['type'] == 'recipe':
                        recipe_name = config.RECIPES.get(reward_info['id'], {}).get('display_name', 'bí mật')
                        embed.title=f"📬 Bạn có thư từ {npc_name}!"
                        embed.description = f"\"_{reward_info['message']}_\"\n\nBạn đã học được công thức chế tạo **{recipe_name}**!"
                    
                    elif reward_info['type'] == 'gift':
                        item_key = reward_info.get('item_key')
                        item_type, item_id = item_key.split('_', 1)
                        item_info = config.CROPS.get(item_id) if item_type == 'seed' else config.PRODUCTS.get(item_id, {})
                        item_name = f"Hạt {item_info['display_name']}" if item_type == 'seed' else item_info.get('display_name', '?')
                        item_emoji = item_info.get('emoji', '🎁')
                        embed.title=f"🎁 Bạn có quà từ {npc_name}!"
                        embed.description = f"\"_{reward_info['message']}_\"\n\nBạn nhận được **{reward_info['amount']} {item_emoji} {item_name}**!"
                        embed.color = discord.Color.blue()
                    
                    try:
                        await interaction.user.send(embed=embed)
                    except discord.Forbidden:
                        await interaction.channel.send(f"{interaction.user.mention}, bạn có thư mới nhưng tôi không thể gửi tin nhắn riêng cho bạn!")

            # Gửi thông báo hoàn thành nhiệm vụ
            npc_info = config.QUEST_NPCS.get(npc_id, {})
            completion_embed = discord.Embed(title=f"✅ Nhiệm vụ Hoàn thành!", color=discord.Color.green())
            completion_embed.description = f"Bạn đã tự động hoàn thành nhiệm vụ **'{quest_template.get('title')}'** cho {npc_info.get('name')} {npc_info.get('emoji')}."
            await interaction.channel.send(embed=completion_embed)
    
    if quest_completed_this_action:
        data_manager.save_player_data()