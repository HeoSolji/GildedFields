# achievement_manager.py

import discord
import config

async def check_achievements(ctx, user_data, event_type, event_id=None, amount=1):
    """Kiểm tra và xử lý các thành tựu dựa trên một sự kiện trong game."""
    user_achievements = user_data.get('achievements', {"unlocked": [], "progress": {}})
    
    for ach_id, ach_info in config.ACHIEVEMENTS.items():
        # Bỏ qua nếu thành tựu đã được mở khóa
        if ach_id in user_achievements['unlocked']:
            continue

        # Nếu loại sự kiện khớp với loại thành tựu
        if ach_info['type'] == event_type:
            progress_key = ach_id
            current_progress = 0

            # Xử lý các loại thành tựu khác nhau
            if event_type in ["harvest", "craft", "collect"]:
                # Chỉ tăng tiến độ nếu đúng loại vật phẩm
                if ach_info['target_id'] == event_id:
                    current_progress = user_achievements['progress'].get(progress_key, 0) + amount
                    user_achievements['progress'][progress_key] = current_progress
                else:
                    # Nếu không phải vật phẩm cần thiết, bỏ qua thành tựu này
                    continue
            
            elif event_type == "level":
                current_progress = user_data.get('level', 1)
                user_achievements['progress'][progress_key] = current_progress

            elif event_type == "balance":
                current_progress = user_data.get('balance', 0)
                # Không lưu tiến độ tiền, chỉ kiểm tra
            
            # Kiểm tra xem đã đạt mục tiêu chưa
            if current_progress >= ach_info['target_amount']:
                # Mở khóa thành tựu
                user_achievements['unlocked'].append(ach_id)
                
                # Gửi thông báo
                embed = discord.Embed(
                    title="🏆 Thành Tựu Mở Khóa! 🏆",
                    description=f"Chúc mừng {ctx.author.mention}, bạn đã đạt được thành tựu:",
                    color=discord.Color.gold()
                )
                embed.add_field(
                    name=f"{ach_info['emoji']} {ach_info['display_name']}",
                    value=f"_{ach_info['description']}_"
                )
                
                # Trao thưởng
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

                await ctx.send(embed=embed)