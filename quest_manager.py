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

async def update_quest_progress(interaction, event_type, **kwargs):
    """
    Cập nhật tiến độ nhiệm vụ hành động và tự động hoàn thành nếu đủ điều kiện.
    Trả về True nếu có nhiệm vụ được tự động hoàn thành.
    """
    user_data = data_manager.get_player_data(interaction.user.id)
    if not user_data: return False

    user_quests = user_data.get('quests', {})
    active_quests = user_quests.get('daily', []) + ([user_quests.get('special')] if user_quests.get('special') else [])
    
    quest_completed = False
    for quest in active_quests:
        if quest and quest.get('type') == event_type:
            # Tăng tiến độ
            quest['progress'] = quest.get('progress', 0) + kwargs.get('amount', 1)
            
            # Kiểm tra hoàn thành
            if quest['progress'] >= quest.get('target_amount', float('inf')):
                quest_completed = True
                
                # Xóa nhiệm vụ khỏi danh sách active
                if quest in user_quests.get('daily', []):
                    user_quests['daily'].remove(quest)
                elif quest == user_quests.get('special'):
                    user_quests['special'] = None
                
                # Trao thưởng
                reward = quest.get('reward', {})
                user_data['balance'] += reward.get('money', 0)
                user_data['xp'] += reward.get('xp', 0)
                npc_id = quest.get('npc')
                if npc_id:
                    user_quests.setdefault('reputation', {})[npc_id] = user_quests.setdefault('reputation', {}).get(npc_id, 0) + reward.get('rep', 0)
                
                # Gửi thông báo
                npc_info = config.QUEST_NPCS.get(npc_id, {})
                embed = discord.Embed(title=f"✅ Nhiệm vụ Hoàn thành!", color=discord.Color.green())
                embed.description = f"Bạn đã hoàn thành nhiệm vụ **'{quest.get('title')}'** cho {npc_info.get('name')} {npc_info.get('emoji')}."
                await interaction.channel.send(embed=embed)
    
    if quest_completed:
        data_manager.save_player_data()
        return True
    return False