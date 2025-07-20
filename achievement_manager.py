# achievement_manager.py

import discord
import config
import data_manager

async def check_achievements(interaction: discord.Interaction, user_data, event_type, **kwargs):
    """
    Kiểm tra và xử lý các thành tựu.
    Phiên bản này được tái cấu trúc để đảm bảo logic chính xác.
    """
    user_achievements = user_data.setdefault('achievements', {"unlocked": [], "progress": {}})
    
    for ach_id, ach_info in config.ACHIEVEMENTS.items():
        # Bỏ qua nếu thành tựu đã được mở khóa
        if ach_id in user_achievements['unlocked']:
            continue

        # Chỉ xử lý các thành tựu có cùng loại với sự kiện đang diễn ra
        if ach_info['type'] != event_type:
            continue

        # Từ đây, chúng ta biết ach_info['type'] == event_type
        
        completed = False
        target_amount = ach_info.get('target_amount', 0)
        progress_key = ach_id

        # Xử lý các loại sự kiện khác nhau
        if event_type in ["level", "balance", "farm_size"]:
            real_value = user_data.get(event_type, 0)
            if isinstance(real_value, dict): # Dành cho farm_size
                real_value = real_value.get('size', 0)
            if real_value >= target_amount:
                completed = True
        
        elif event_type in ["harvest", "craft", "collect", "fish"]:
            if ach_info.get('target_id') == kwargs.get('event_id'):
                amount = kwargs.get('amount', 1)
                current = user_achievements['progress'].setdefault(progress_key, 0)
                progress = current + amount
                user_achievements['progress'][progress_key] = progress
                if progress >= target_amount:
                    completed = True
        
        elif event_type in ["harvest_total", "collect_total", "fish_total", "gift"]:
            amount = kwargs.get('amount', 1)
            current = user_achievements['progress'].setdefault(progress_key, 0)
            progress = current + amount
            user_achievements['progress'][progress_key] = progress
            if progress >= target_amount:
                completed = True

        elif event_type == "harvest_quality":
            if kwargs.get('quality') == ach_info.get('target_quality'):
                amount = kwargs.get('amount', 1)
                current = user_achievements['progress'].setdefault(progress_key, 0)
                progress = current + amount
                user_achievements['progress'][progress_key] = progress
                if progress >= target_amount:
                    completed = True
        
        elif event_type == "collection":
            if ach_info.get('category') == kwargs.get('category'):
                progress_list = user_achievements['progress'].setdefault(progress_key, [])
                if kwargs.get('event_id') not in progress_list:
                    progress_list.append(kwargs.get('event_id'))
                if len(progress_list) >= target_amount:
                    completed = True

        # Mở khóa và trao thưởng nếu hoàn thành
        if completed:
            user_achievements['unlocked'].append(ach_id)
            
            embed = discord.Embed(
                title="🏆 Thành Tựu Mở Khóa! 🏆",
                description=f"Chúc mừng {interaction.user.mention}, bạn đã đạt được thành tựu:",
                color=discord.Color.gold()
            )
            embed.add_field(name=f"{ach_info['emoji']} {ach_info['display_name']}", value=f"_{ach_info['description']}_")
            
            reward = ach_info.get('reward')
            if reward:
                reward_lines = []
                if 'money' in reward:
                    user_data['balance'] += reward['money']
                    reward_lines.append(f"{reward['money']} {config.CURRENCY_SYMBOL}")
                if 'xp' in reward:
                    user_data['xp'] += reward['xp']
                    reward_lines.append(f"{reward['xp']} XP")
                embed.add_field(name="Phần thưởng:", value=", ".join(reward_lines), inline=False)

            await interaction.channel.send(embed=embed)
            data_manager.save_player_data()