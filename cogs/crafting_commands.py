# cogs/crafting_commands.py

import discord
from discord.ext import commands
import data_manager
import config
import achievement_manager

class CraftingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_ingredient_string(self, ingredients):
        """Hàm trợ giúp để hiển thị danh sách nguyên liệu."""
        lines = []
        for item_key, quantity in ingredients.items():
            item_type, item_id = item_key.split('_', 1)
            emoji, name = "❓", "Vật phẩm không xác định"

            if item_type == 'harvest':
                emoji = config.CROPS[item_id]['emoji']
                name = config.CROPS[item_id]['display_name']
            elif item_type == 'product':
                emoji = config.PRODUCTS[item_id]['emoji']
                name = config.PRODUCTS[item_id]['display_name']
            
            lines.append(f"{emoji} {name}: {quantity}")
        return ", ".join(lines)

    @commands.command(name='craftlist', aliases=['recipes'])
    async def craft_list(self, ctx):
        """Xem danh sách tất cả các công thức chế tạo có sẵn."""
        embed = discord.Embed(title="📜 Sổ tay Công thức Chế tạo", color=discord.Color.orange())

        if not config.RECIPES:
            embed.description = "Hiện chưa có công thức nào."
            return await ctx.send(embed=embed)
        
        description_lines = []
        for index, (recipe_id, recipe_info) in enumerate(config.RECIPES.items()):
            ingredient_str = self.get_ingredient_string(recipe_info['ingredients'])
            line = (
                f"**{index + 1}.** {recipe_info['emoji']} **{recipe_info['display_name']}**\n"
                f"   **Cần:** {ingredient_str}\n"
                f"   **Giá bán:** {recipe_info['sell_price']} {config.CURRENCY_SYMBOL}"
            )
            description_lines.append(line)
        
        embed.description = "\n\n".join(description_lines)
        embed.set_footer(text="Dùng !craft [số] [lượng] để chế tạo")
        await ctx.send(embed=embed)

    @commands.command(name='craft')
    async def craft(self, ctx, recipe_index: int, amount: int = 1):
        """Chế tạo vật phẩm từ công thức."""
        user_data = data_manager.get_player_data(ctx.author.id)
        if not user_data: return await ctx.send("Bạn chưa đăng ký!")
        if amount <= 0: return await ctx.send("Số lượng phải lớn hơn 0.")

        recipes = list(config.RECIPES.items())
        index = recipe_index - 1
        if not (0 <= index < len(recipes)):
            return await ctx.send(f"Số thứ tự công thức `{recipe_index}` không hợp lệ.")

        recipe_id, recipe_info = recipes[index]
        ingredients_needed = recipe_info['ingredients']
        user_inventory = user_data['inventory']

        # Kiểm tra xem có đủ nguyên liệu không
        missing_ingredients = []
        for item_key, required_quantity in ingredients_needed.items():
            total_required = required_quantity * amount
            if user_inventory.get(item_key, 0) < total_required:
                missing_ingredients.append(item_key)
        
        if missing_ingredients:
            return await ctx.send(f"Bạn không đủ nguyên liệu! Vui lòng kiểm tra lại kho đồ.")

        # Trừ nguyên liệu
        for item_key, required_quantity in ingredients_needed.items():
            total_to_remove = required_quantity * amount
            user_inventory[item_key] -= total_to_remove
            if user_inventory[item_key] == 0:
                del user_inventory[item_key]
        
        # Thêm vật phẩm đã chế tạo
        crafted_item_key = f"crafted_{recipe_id}"
        user_inventory[crafted_item_key] = user_inventory.get(crafted_item_key, 0) + amount
        
        await achievement_manager.check_achievements(ctx, user_data, "craft", event_id=recipe_id, amount=amount)
        await ctx.send(f"Bạn đã chế tạo thành công {amount} {recipe_info['emoji']} **{recipe_info['display_name']}**!")

        data_manager.save_player_data()


async def setup(bot):
    await bot.add_cog(CraftingCommands(bot))