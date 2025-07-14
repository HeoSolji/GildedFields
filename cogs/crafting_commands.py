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

    @app_commands.command(name="craftlist", description="Xem danh sách tất cả các công thức chế tạo.")
    async def craft_list(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📜 Sổ tay Công thức Chế tạo", color=discord.Color.orange())
        if not config.RECIPES:
            embed.description = "Hiện chưa có công thức nào."
            return await interaction.response.send_message(embed=embed)
        
        recipes = list(config.RECIPES.items())
        description_lines = []
        for index, (recipe_id, recipe_info) in enumerate(recipes):
            ingredient_str = self.get_ingredient_string(recipe_info['ingredients'])
            line = (f"**{index + 1}.** {recipe_info['emoji']} **{recipe_info['display_name']}**\n"
                    f"   **Cần:** {ingredient_str}\n"
                    f"   **Giá bán:** {recipe_info['sell_price']} {config.CURRENCY_SYMBOL}")
            description_lines.append(line)
        
        embed.description = "\n\n".join(description_lines)
        embed.set_footer(text="Dùng /craft [số] [lượng] để chế tạo")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="craft", description="Chế tạo vật phẩm từ công thức (chất lượng phụ thuộc vào nguyên liệu).")
    @app_commands.describe(số_thứ_tự="Số thứ tự của công thức trong /craftlist.", số_lượng="Số lượng bạn muốn chế tạo.")
    async def craft(self, interaction: discord.Interaction, số_thứ_tự: int, số_lượng: int = 1):
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.response.send_message("Bạn chưa đăng ký!", ephemeral=True)
        if số_lượng <= 0: return await interaction.response.send_message("Số lượng phải lớn hơn 0.", ephemeral=True)

        recipes = list(config.RECIPES.items())
        index = số_thứ_tự - 1
        if not (0 <= index < len(recipes)): return await interaction.response.send_message(f"STT `{số_thứ_tự}` không hợp lệ.", ephemeral=True)

        recipe_id, recipe_info = recipes[index]
        ingredients_needed = recipe_info['ingredients']
        user_inventory = user_data['inventory']

        # --- KIỂM TRA VÀ SỬ DỤNG NGUYÊN LIỆU THEO CHẤT LƯỢNG ---
        
        # 1. Kiểm tra xem có đủ tổng số lượng không
        for item_key, required_quantity in ingredients_needed.items():
            total_owned = sum(user_inventory.get(item_key, {}).values())
            if total_owned < required_quantity * số_lượng:
                return await interaction.response.send_message(f"Bạn không đủ nguyên liệu! Cần {required_quantity * số_lượng} {item_key.replace('_', ' ')}.", ephemeral=True)
        
        # 2. Sử dụng nguyên liệu và tính tổng điểm chất lượng
        total_quality_points = 0
        total_ingredients_count = 0
        
        for _ in range(số_lượng): # Lặp lại cho mỗi vật phẩm muốn chế tạo
            for item_key, required_quantity in ingredients_needed.items():
                amount_to_consume = required_quantity
                
                # Luôn ưu tiên dùng nguyên liệu chất lượng thấp trước (0 -> 1 -> 2 -> 3)
                for quality in sorted(user_inventory.get(item_key, {}).keys(), key=int):
                    if amount_to_consume == 0: break
                    
                    available_amount = user_inventory[item_key][quality]
                    consume = min(amount_to_consume, available_amount)
                    
                    total_quality_points += int(quality) * consume
                    total_ingredients_count += consume
                    
                    user_inventory[item_key][quality] -= consume
                    if user_inventory[item_key][quality] == 0:
                        del user_inventory[item_key][quality]
                    
                    amount_to_consume -= consume
                
                if not user_inventory[item_key]: # Dọn dẹp nếu không còn cấp sao nào
                    del user_inventory[item_key]

        # 3. Quyết định chất lượng sản phẩm
        # Làm tròn chất lượng trung bình
        final_quality = round(total_quality_points / total_ingredients_count) if total_ingredients_count > 0 else 0
        quality_str = str(final_quality)
        
        # 4. Thêm vật phẩm đã chế tạo vào kho
        crafted_item_key = f"crafted_{recipe_id}"
        user_inventory.setdefault(crafted_item_key, {})[quality_str] = user_inventory.setdefault(crafted_item_key, {}).get(quality_str, 0) + số_lượng
        
        star_emoji = config.STAR_EMOJIS.get(final_quality, "")
        await interaction.response.send_message(f"Bạn đã chế tạo thành công {số_lượng} {recipe_info['emoji']} **{recipe_info['display_name']}{star_emoji}**!")
        
        await achievement_manager.check_achievements(interaction, user_data, "craft", event_id=recipe_id, amount=số_lượng)
        data_manager.save_player_data()


async def setup(bot):
    await bot.add_cog(CraftingCommands(bot))