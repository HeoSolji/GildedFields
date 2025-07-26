# cogs/crafting_commands.py

import discord
from discord.ext import commands
from discord import app_commands
import data_manager
import config
import achievement_manager
import math
import utils

class CraftingCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_ingredient_string(self, ingredients):
        lines = []
        for item_key, quantity in ingredients.items():
            item_type, item_id = item_key.split('_', 1)
            emoji, name = "❓", "?"
            if item_type == 'harvest':
                emoji, name = config.CROPS[item_id]['emoji'], config.CROPS[item_id]['display_name']
            elif item_type == 'product':
                emoji, name = config.PRODUCTS[item_id]['emoji'], config.PRODUCTS[item_id]['display_name']
            lines.append(f"{emoji} {name}: {quantity}")
        return ", ".join(lines)

    @app_commands.command(name="craftlist", description="Xem danh sách tất cả các công thức chế tạo bạn đã biết.")
    async def craft_list(self, interaction: discord.Interaction):
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: 
            return await interaction.response.send_message("Bạn chưa đăng ký!", ephemeral=True)

        unlocked_recipes_list = user_data.get('quests', {}).get('unlocked_recipes', [])
        
        embed = discord.Embed(title="📜 Sổ tay Công thức Chế tạo", color=discord.Color.orange())
        
        # Lọc ra danh sách các công thức người chơi có thể thấy
        available_recipes = []
        for recipe_id, recipe_info in config.RECIPES.items():
            unlock_key = recipe_info.get("unlocked_by")
            # Điều kiện hiển thị: không cần mở khóa, HOẶC đã được mở khóa
            if not unlock_key or recipe_id in unlocked_recipes_list:
                available_recipes.append((recipe_id, recipe_info))

        if not available_recipes:
            embed.description = "Bạn chưa biết công thức chế tạo nào cả. Hãy thử làm nhiệm vụ để tăng thân thiện với dân làng nhé!"
            return await interaction.response.send_message(embed=embed)
        
        description_lines = []
        # Lặp qua danh sách đã được lọc
        for index, (recipe_id, recipe_info) in enumerate(available_recipes):
            ingredient_str = self.get_ingredient_string(recipe_info['ingredients'])
            line = (
                f"**{index + 1}.** {recipe_info['emoji']} **{recipe_info['display_name']}**\n"
                f"   **Cần:** {ingredient_str}\n"
                f"   **Giá bán:** {recipe_info['sell_price']} {config.CURRENCY_SYMBOL}"
            )
            description_lines.append(line)
        
        embed.description = "\n\n".join(description_lines)
        embed.set_footer(text="Dùng /craft [số] [lượng] để chế tạo")
        await interaction.response.send_message(embed=embed)

    
    @app_commands.command(name="craft", description="Chế tạo vật phẩm từ công thức (chất lượng phụ thuộc vào nguyên liệu).")
    @app_commands.describe(số_thứ_tự="Số thứ tự của công thức trong /craftlist.", số_lượng="Số lượng bạn muốn chế tạo.")
    async def craft(self, interaction: discord.Interaction, số_thứ_tự: int, số_lượng: int = 1):
        try:
            # SỬA LỖI: Thêm defer() để tránh timeout
            await interaction.response.defer()

            user_data = data_manager.get_player_data(interaction.user.id)
            if not user_data: return await interaction.followup.send("Bạn chưa đăng ký!", ephemeral=True)
            if số_lượng <= 0: return await interaction.followup.send("Số lượng phải lớn hơn 0.", ephemeral=True)

            recipes = list(config.RECIPES.items())
            index = số_thứ_tự - 1
            if not (0 <= index < len(recipes)):
                return await interaction.followup.send(f"STT `{số_thứ_tự}` không hợp lệ.", ephemeral=True)

            recipe_id, recipe_info = recipes[index]
            ingredients_needed = recipe_info['ingredients']
            user_inventory = user_data['inventory']

            # --- LOGIC MỚI: TÁI CẤU TRÚC ĐỂ HIỆU QUẢ HƠN ---

            # 1. Tính toán tổng số nguyên liệu cần thiết
            total_ingredients_needed = {key: val * số_lượng for key, val in ingredients_needed.items()}

            # 2. Kiểm tra xem có đủ tổng số lượng không
            for item_key, needed_amount in total_ingredients_needed.items():
                total_owned = sum(user_inventory.get(item_key, {}).values())
                if total_owned < needed_amount:
                    return await interaction.followup.send(f"Bạn không đủ nguyên liệu! Cần {needed_amount} {item_key.replace('_', ' ')} nhưng chỉ có {total_owned}.", ephemeral=True)

            # 3. Sử dụng nguyên liệu và tính tổng điểm chất lượng
            total_quality_points = 0
            total_ingredients_count = 0
            for item_key, amount_to_consume in total_ingredients_needed.items():
                total_ingredients_count += amount_to_consume
                # Luôn ưu tiên dùng nguyên liệu chất lượng thấp trước (0 -> 1 -> 2 -> 3)
                for quality in sorted(user_inventory.get(item_key, {}).keys(), key=int):
                    if amount_to_consume <= 0: break
                    
                    available_in_bucket = user_inventory[item_key][quality]
                    consume = min(amount_to_consume, available_in_bucket)
                    
                    total_quality_points += int(quality) * consume
                    
                    user_inventory[item_key][quality] -= consume
                    if user_inventory[item_key][quality] == 0: del user_inventory[item_key][quality]
                    
                    amount_to_consume -= consume
                
                if not user_inventory.get(item_key): del user_inventory[item_key]

            # 4. Quyết định chất lượng sản phẩm và thêm vào kho
            final_quality = round(total_quality_points / total_ingredients_count) if total_ingredients_count > 0 else 0
            
            recipe_type = recipe_info.get("type", "item")

            if recipe_type == "machine":
                user_data.setdefault('machines', {}).setdefault(recipe_id, [])
                for _ in range(số_lượng):
                    user_data['machines'][recipe_id].append({"state": "idle"})
            else:
                quality_str = str(final_quality)
                crafted_item_key = f"crafted_{recipe_id}"
                user_inventory.setdefault(crafted_item_key, {})[quality_str] = user_inventory.setdefault(crafted_item_key, {}).get(quality_str, 0) + số_lượng
            
            star_emoji = config.STAR_EMOJIS.get(final_quality, "")
            await interaction.followup.send(f"Bạn đã chế tạo thành công {số_lượng} {recipe_info['emoji']} **{recipe_info['display_name']}{star_emoji}**!")
            
            await achievement_manager.check_achievements(interaction, user_data, "craft", event_id=recipe_id, amount=số_lượng)
            data_manager.save_player_data()

        except Exception as e:
            print(f"Lỗi nghiêm trọng trong lệnh /craft: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("Có lỗi xảy ra.", ephemeral=True)
            else:
                await interaction.followup.send("Có lỗi xảy ra.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(CraftingCommands(bot))