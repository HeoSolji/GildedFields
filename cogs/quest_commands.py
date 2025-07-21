# cogs/quest_commands.py
import discord
from discord.ext import commands
from discord import app_commands
import time, datetime
import data_manager, config, quest_manager

class QuestCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    quests_group = app_commands.Group(name="quests", description="Các lệnh liên quan đến nhiệm vụ.")


    def format_quest_embed(self, user_data, interaction):
        """Tạo embed hiển thị bảng nhiệm vụ (phiên bản hiển thị đầy đủ phần thưởng)."""
        user_quests = user_data.get('quests', {})
        embed = discord.Embed(title=f"📜 Bảng Nhiệm vụ của {interaction.user.name}", color=discord.Color.dark_gold())
        
        economy_cog = self.bot.get_cog('Economy')
        if not economy_cog:
            embed.description = "Lỗi: Không thể tải module kinh tế."
            return embed

        # --- Xử lý Nhiệm vụ hàng ngày ---
        daily_quests = user_quests.get('daily', [])
        daily_lines = []
        if daily_quests:
            for i, saved_quest in enumerate(daily_quests):
                quest_id = saved_quest.get('id')
                quest_template = next((q for q in config.QUEST_POOL['daily'] if q['id'] == quest_id), None)
                if not quest_template: continue
                
                npc_info = config.QUEST_NPCS.get(quest_template.get('npc'), {})
                target = quest_template.get('target_amount', '?')
                title = quest_template.get('title', 'N/A')
                
                # Logic lấy tiến độ thông minh
                progress = 0
                quest_type = quest_template.get('type')

                if quest_type in ['collect', 'collect_quality']:
                    target_id = quest_template.get('target_id')
                    inventory_bucket = user_data.get('inventory', {}).get(target_id, {})
                    
                    if quest_type == 'collect_quality':
                        target_quality_str = str(quest_template.get('target_quality', 0))
                        progress = inventory_bucket.get(target_quality_str, 0)
                    else: # 'collect'
                        progress = sum(inventory_bucket.values())
                else: # Nhiệm vụ hành động
                    progress = saved_quest.get('progress', 0)
                
                # Tạo dòng mô tả mục tiêu
                objective_text = quest_template.get('objective', 'Không có mô tả chi tiết.')
                try:
                    if quest_template.get('type') in ['collect', 'collect_quality']:
                        item_name, item_emoji, _ = economy_cog._get_item_info(quest_template['target_id'], str(quest_template.get('target_quality', 0)))
                        objective_text = objective_text.format(amount=target, name=item_name, emoji=item_emoji)
                    else:
                        objective_text = objective_text.format(amount=target)
                except Exception as e:
                    print(f"Lỗi khi định dạng objective text cho quest {quest_id}: {e}")
                    objective_text = "Lỗi hiển thị mục tiêu."

                reward = quest_template.get('reward', {})
                reward_parts = []
                if reward.get('money', 0) > 0:
                    reward_parts.append(f"{reward['money']}{config.CURRENCY_SYMBOL}")
                if reward.get('xp', 0) > 0:
                    reward_parts.append(f"{reward['xp']} XP")
                if reward.get('rep', 0) > 0:
                    reward_parts.append(f"{reward['rep']}❤️") # Dùng emoji trái tim cho điểm thân thiện
                reward_str = " | ".join(reward_parts)

                status = "✅ **Hoàn thành!**" if progress >= target else f"Tiến độ: {progress}/{target}"
                daily_lines.append(
                    f"**{i+1}. {npc_info.get('emoji', '')} {title}**\n"
                    f"*└ {objective_text}*\n"
                    f"`{status}`\n"
                    f"`🎁 Phần thưởng: {reward_str}`"
                )

            time_left = (user_quests.get('last_updated', 0) + quest_manager.SECONDS_IN_A_DAY) - time.time()
            td = datetime.timedelta(seconds=int(time_left)) if time_left > 0 else "0:00:00"
            embed.add_field(name=f"Nhiệm vụ Hàng ngày (làm mới sau `{str(td)}`)", value="\n\n".join(daily_lines), inline=False)
        else:
            embed.add_field(name="Nhiệm vụ Hàng ngày", value="Bạn chưa có nhiệm vụ mới cho hôm nay hoặc đã hoàn thành hết!", inline=False)

        # --- Xử lý Nhiệm vụ đặc biệt ---
        special_quest = user_quests.get('special')
        special_quest = user_quests.get('special')
        if special_quest:
            # Số thứ tự của nhiệm vụ đặc biệt sẽ là số lượng nhiệm vụ hàng ngày + 1
            special_quest_index = len(daily_quests) + 1
            
            quest_id = special_quest.get('id')
            quest_template = next((q for q in config.QUEST_POOL['special'] if q['id'] == quest_id), None)

            if quest_template:
                npc_info = config.QUEST_NPCS.get(quest_template.get('npc'), {})
                target = quest_template.get('target_amount', '?')
                title = quest_template.get('title', 'N/A')
                
                # Logic lấy tiến độ cho nhiệm vụ đặc biệt
                progress = 0
                quest_type = quest_template.get('type')
                if quest_type in ['collect', 'collect_quality']:
                    target_id = quest_template.get('target_id')
                    inventory_bucket = user_data.get('inventory', {}).get(target_id, {})
                    if quest_type == 'collect_quality':
                        target_quality_str = str(quest_template.get('target_quality', 0))
                        progress = inventory_bucket.get(target_quality_str, 0)
                    else:
                        progress = sum(inventory_bucket.values())
                else:
                    progress = special_quest.get('progress', 0)

                objective_text = quest_template.get('objective', 'Không có mô tả chi tiết.')
                try:
                    if quest_template.get('type') in ['collect', 'collect_quality']:
                        item_name, item_emoji, _ = economy_cog._get_item_info(quest_template['target_id'], str(quest_template.get('target_quality', 0)))
                        objective_text = objective_text.format(amount=target, name=item_name, emoji=item_emoji)
                    else:
                        objective_text = objective_text.format(amount=target)
                except Exception:
                    objective_text = "Lỗi hiển thị mục tiêu."
                
                reward = quest_template.get('reward', {})
                reward_parts = []
                if reward.get('money', 0) > 0: reward_parts.append(f"{reward['money']}{config.CURRENCY_SYMBOL}")
                if reward.get('xp', 0) > 0: reward_parts.append(f"{reward['xp']} XP")
                if reward.get('rep', 0) > 0: reward_parts.append(f"{reward['rep']}❤️")
                reward_str = " | ".join(reward_parts)
                # ==========================================
                
                status = "✅ **Hoàn thành!**" if progress >= target else f"Tiến độ: {progress}/{target}"
                
                special_line = (
                    f"**{special_quest_index}. {npc_info.get('emoji', '')} {title}**\n"
                    f"*└ {objective_text}*\n"
                    f"`{status}`\n"
                    f"`🎁 Phần thưởng: {reward_str}`"
                )
                
                time_left = special_quest.get('expires_at', 0) - time.time()
                td = datetime.timedelta(seconds=int(time_left)) if time_left > 0 else "Hết hạn"
                embed.add_field(name=f"✨ Nhiệm vụ Đặc biệt (kết thúc sau `{str(td)}`)", value=special_line, inline=False)
        
        embed.set_footer(text="Dùng /quests complete [số] để trả nhiệm vụ thu thập.")
        return embed

    @quests_group.command(name="view", description="Xem bảng nhiệm vụ hàng ngày và đặc biệt của bạn.")
    async def quests_view(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            user_data = data_manager.get_player_data(interaction.user.id)
            if not user_data: 
                return await interaction.followup.send("Bạn chưa đăng ký!")

            # Làm mới nhiệm vụ nếu cần
            quest_manager.get_new_quests(user_data)
            
            embed = self.format_quest_embed(user_data, interaction)
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"Lỗi trong lệnh /quests view: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("Có lỗi xảy ra khi xem nhiệm vụ.", ephemeral=True)
            else:
                await interaction.followup.send("Có lỗi xảy ra khi xem nhiệm vụ.", ephemeral=True)

    @quests_group.command(name="complete", description="Trả nhiệm vụ thu thập đã hoàn thành.")
    @app_commands.describe(số_thứ_tự="Số thứ tự của nhiệm vụ bạn muốn trả.")
    async def quests_complete(self, interaction: discord.Interaction, số_thứ_tự: int):
        try:
            await interaction.response.defer(ephemeral=True)
            user_data = data_manager.get_player_data(interaction.user.id)
            if not user_data: return await interaction.followup.send("Bạn chưa đăng ký!")

            user_quests = user_data.get('quests', {})
            all_active_quests = user_quests.get('daily', []) + ([user_quests.get('special')] if user_quests.get('special') else [])
            
            index = số_thứ_tự - 1
            if not (0 <= index < len(all_active_quests)):
                return await interaction.followup.send("Số thứ tự nhiệm vụ không hợp lệ.")

            quest_to_complete = all_active_quests[index]
            quest_id = quest_to_complete.get('id')
            
            # Tìm lại template của quest trong config để lấy thông tin đầy đủ
            quest_pool = config.QUEST_POOL.get('daily', []) + config.QUEST_POOL.get('special', [])
            quest_template = next((q for q in quest_pool if q['id'] == quest_id), None)
            if not quest_template:
                return await interaction.followup.send("Lỗi: Không tìm thấy thông tin gốc của nhiệm vụ này.")

            quest_type = quest_template.get('type')
            if quest_type not in ['collect', 'collect_quality']:
                return await interaction.followup.send("Bạn không thể trả nhiệm vụ loại này theo cách thủ công.")

            # Kiểm tra xem đã đủ vật phẩm chưa
            target_id = quest_template.get('target_id')
            target_amount = quest_template.get('target_amount', 0)
            inventory_bucket = user_data.get('inventory', {}).get(target_id, {})
            
            current_amount = 0
            if quest_type == 'collect_quality':
                target_quality_str = str(quest_template.get('target_quality', 0))
                current_amount = inventory_bucket.get(target_quality_str, 0)
            else: # 'collect'
                current_amount = sum(inventory_bucket.values())

            if current_amount < target_amount:
                return await interaction.followup.send(f"Bạn chưa thu thập đủ vật phẩm! Cần {target_amount}, bạn đang có {current_amount}.")

            # --- Nếu đủ, tiến hành trả nhiệm vụ ---
            
            # 1. Trừ vật phẩm (ưu tiên chất lượng thấp trước)
            amount_to_remove = target_amount
            if quest_type == 'collect_quality':
                target_quality_str = str(quest_template.get('target_quality', 0))
                user_data['inventory'][target_id][target_quality_str] -= amount_to_remove
                if user_data['inventory'][target_id][target_quality_str] <= 0: del user_data['inventory'][target_id][target_quality_str]
            else: # 'collect'
                for quality_str in sorted(inventory_bucket.keys(), key=int):
                    if amount_to_remove <= 0: break
                    can_remove = min(amount_to_remove, inventory_bucket[quality_str])
                    inventory_bucket[quality_str] -= can_remove
                    if inventory_bucket[quality_str] <= 0: del inventory_bucket[quality_str]
                    amount_to_remove -= can_remove
            
            if not user_data['inventory'][target_id]: del user_data['inventory'][target_id]

            # 2. Xóa nhiệm vụ khỏi danh sách active
            if quest_to_complete in user_quests.get('daily', []):
                user_quests['daily'].remove(quest_to_complete)
            elif quest_to_complete == user_quests.get('special'):
                user_quests['special'] = None

            # 3. Trao thưởng
            reward = quest_template.get('reward', {})
            money_reward = reward.get('money', 0)
            xp_reward = reward.get('xp', 0)
            rep_reward = reward.get('rep', 0)
            npc_id = quest_template.get('npc')

            user_data['balance'] += money_reward
            user_data['xp'] += xp_reward
            if npc_id:
                user_quests.setdefault('reputation', {})[npc_id] = user_quests.setdefault('reputation', {}).get(npc_id, 0) + rep_reward
            
            # 4. Gửi thông báo
            npc_info = config.QUEST_NPCS.get(npc_id, {})
            embed = discord.Embed(title=f"✅ Trả Nhiệm vụ Thành công!", color=discord.Color.green())
            embed.description = f"Bạn đã hoàn thành nhiệm vụ **'{quest_template.get('title')}'** cho {npc_info.get('name')} {npc_info.get('emoji')}."
            embed.add_field(name="Phần thưởng nhận được", value=f"💰 {money_reward} | ✨ {xp_reward} XP | ❤️ {rep_reward} điểm thân thiện")
            
            await interaction.followup.send(embed=embed)
            data_manager.save_player_data()

        except Exception as e:
            print(f"Lỗi trong lệnh /quests complete: {e}")
            await interaction.followup.send("Có lỗi xảy ra khi trả nhiệm vụ.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(QuestCommands(bot))