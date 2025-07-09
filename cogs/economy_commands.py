# cogs/economy_commands.py

import discord
from discord.ext import commands
import time
import math
import data_manager
import config
import season_manager

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _get_sellable_items(self, user_data):
        sellable_items = []
        inventory = user_data.get("inventory", {})
        
        # Sắp xếp để thứ tự luôn ổn định: Nông sản -> Sản phẩm chăn nuôi -> Hạt giống
        for item_key in sorted(inventory.keys()):
            if inventory[item_key] > 0 and item_key.startswith("crafted_"):
                sellable_items.append(item_key)
        for item_key in sorted(inventory.keys()):
            if inventory[item_key] > 0 and item_key.startswith("harvest_"):
                sellable_items.append(item_key)
        for item_key in sorted(inventory.keys()):
            if inventory[item_key] > 0 and item_key.startswith("product_"):
                sellable_items.append(item_key)
        for item_key in sorted(inventory.keys()):
            if inventory[item_key] > 0 and item_key.startswith("seed_"):
                sellable_items.append(item_key)
                
        return sellable_items

    @commands.command(name='balance', aliases=['bal'])
    async def balance(self, ctx):
        user_data = data_manager.get_player_data(ctx.author.id)
        if not user_data:
            return await ctx.send('Bạn chưa đăng ký. Dùng `!register` để bắt đầu!')
        
        await ctx.send(f'{ctx.author.mention}, bạn có {user_data["balance"]} {config.CURRENCY_SYMBOL}.')

    @commands.command(name='inventory', aliases=['inv', 'i'])
    async def inventory(self, ctx):
        user_data = data_manager.get_player_data(ctx.author.id)
        if not user_data: return await ctx.send('Bạn chưa đăng ký!')

        sellable_items = self._get_sellable_items(user_data)
        if not sellable_items: return await ctx.send('Kho đồ của bạn trống rỗng.')

        embed = discord.Embed(title=f"Kho đồ của {ctx.author.name}", color=discord.Color.gold())
        lines = []
        for index, item_key in enumerate(sellable_items):
            quantity = user_data["inventory"][item_key]
            item_type, item_id = item_key.split('_', 1)
            
            name, emoji = "", "❓"
            if item_type == "crafted":
                recipe_info = config.RECIPES.get(item_id, {})
                name = recipe_info.get('display_name', 'Vật phẩm chế tạo')
                emoji = recipe_info.get('emoji', '🛠️')
            elif item_type == "seed":
                name = f"Hạt {config.CROPS[item_id]['display_name']}"
                emoji = config.CROPS[item_id]['emoji']
            elif item_type == "harvest":
                name = config.CROPS[item_id]['display_name']
                emoji = config.CROPS[item_id]['emoji']
            elif item_type == "product":
                name = config.PRODUCTS[item_id]['display_name']
                emoji = config.PRODUCTS[item_id]['emoji']
            
            lines.append(f"**{index + 1}.** {emoji} **{name}**: `{quantity}`")
        
        embed.description = "\n".join(lines)
        embed.set_footer(text="Dùng !sell [số] [lượng] để bán")
        await ctx.send(embed=embed)

    @commands.command(name='shop')
    async def shop(self, ctx):
        user_data = data_manager.get_player_data(ctx.author.id)
        if not user_data: return await ctx.send("Bạn chưa đăng ký!")

        current_season = season_manager.get_current_season()
        season_name = current_season['name']
        
        user_balance = user_data.get('balance', 0)
        desc = (f"**Mùa hiện tại:** {current_season['display']} {current_season['emoji']}\n"
                f"**Số tiền của bạn:** {user_balance} {config.CURRENCY_SYMBOL}")
        embed = discord.Embed(title="🛒 Cửa hàng Nông trại", description=desc, color=discord.Color.green())

        # Lọc và hiển thị hạt giống theo mùa
        seed_lines = []
        self.seasonal_seeds = []
        for crop_id, crop_info in config.CROPS.items():
            if season_name in crop_info['seasons']:
                self.seasonal_seeds.append((crop_id, crop_info))
                seed_lines.append(f"**{len(self.seasonal_seeds)}.** {crop_info['emoji']} Hạt {crop_info['display_name']} - {crop_info['seed_price']} {config.CURRENCY_SYMBOL}")
        
        if seed_lines:
            embed.add_field(name="Hạt Giống (Dùng: !buyseed [số])", value="\n".join(seed_lines), inline=False)
        else:
            embed.add_field(name="Hạt Giống", value="Không có hạt giống nào được bán trong mùa này.", inline=False)

        # Lọc và hiển thị vật nuôi theo mùa
        animal_lines = []
        self.seasonal_animals = []
        for animal_id, animal_info in config.ANIMALS.items():
            if season_name in animal_info['seasons']:
                self.seasonal_animals.append((animal_id, animal_info))
                animal_lines.append(f"**{len(self.seasonal_animals)}.** {animal_info['emoji']} {animal_info['display_name']} - {animal_info['buy_price']} {config.CURRENCY_SYMBOL}")
        
        if animal_lines:
            embed.add_field(name="Vật Nuôi (Dùng: !buyanimal [số])", value="\n".join(animal_lines), inline=False)
        else:
            embed.add_field(name="Vật Nuôi", value="Không có vật nuôi nào được bán trong mùa này.", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name='buyseed')
    async def buy_seed(self, ctx, item_index: int, amount: int = 1):
        """Mua hạt giống theo mùa từ cửa hàng."""
        # Lọc lại danh sách theo mùa để đảm bảo người dùng không mua sai
        current_season = season_manager.get_current_season()['name']
        seasonal_shop_items = [(cid, cinfo) for cid, cinfo in config.CROPS.items() if current_season in cinfo['seasons']]
        
        user_data = data_manager.get_player_data(ctx.author.id)
        if not user_data: return await ctx.send('Bạn chưa đăng ký!')
        if amount <= 0: return await ctx.send("Số lượng phải lớn hơn 0.")

        index = item_index - 1
        if not (0 <= index < len(seasonal_shop_items)): return await ctx.send(f'STT `{item_index}` không hợp lệ cho mùa này.')

        crop_id, crop_info = seasonal_shop_items[index]
        # ... (Phần logic mua còn lại giữ nguyên) ...
        total_cost = crop_info['seed_price'] * amount
        if user_data['balance'] < total_cost: return await ctx.send(f'Bạn không đủ tiền!')
        user_data['balance'] -= total_cost
        user_data['inventory'][f"seed_{crop_id}"] = user_data['inventory'].get(f"seed_{crop_id}", 0) + amount
        await ctx.send(f'Bạn đã mua {amount} {crop_info["emoji"]} Hạt {crop_info["display_name"]} với giá {total_cost} {config.CURRENCY_SYMBOL}.')
        data_manager.save_player_data()


    @commands.command(name='buyanimal')
    async def buy_animal(self, ctx, item_index: int, amount: int = 1):
        """Mua vật nuôi theo mùa từ cửa hàng."""
        current_season = season_manager.get_current_season()['name']
        seasonal_shop_items = [(aid, ainfo) for aid, ainfo in config.ANIMALS.items() if current_season in ainfo['seasons']]

        user_data = data_manager.get_player_data(ctx.author.id)
        if not user_data: return await ctx.send('Bạn chưa đăng ký!')
        if amount <= 0: return await ctx.send("Số lượng phải lớn hơn 0.")

        index = item_index - 1
        if not (0 <= index < len(seasonal_shop_items)): return await ctx.send(f'STT `{item_index}` không hợp lệ cho mùa này.')
        
        animal_id, animal_info = seasonal_shop_items[index]
        # ... (Phần logic mua còn lại giữ nguyên) ...
        barn = user_data['barn']
        current_animal_count = sum(len(animal_list) for animal_list in barn.get('animals', {}).values())
        if current_animal_count + amount > barn['capacity']:
            return await ctx.send(f"Chuồng không đủ chỗ! Chỗ trống: {barn['capacity'] - current_animal_count}.")
        total_cost = animal_info['buy_price'] * amount
        if user_data['balance'] < total_cost: return await ctx.send(f'Bạn không đủ tiền!')
        user_data['balance'] -= total_cost
        current_time = time.time()
        production_time = animal_info['production_time']
        new_ready_times = [current_time + production_time] * amount
        if animal_id in barn['animals']:
            barn['animals'][animal_id].extend(new_ready_times)
        else:
            barn['animals'][animal_id] = new_ready_times
        await ctx.send(f'Bạn đã mua {amount} {animal_info["emoji"]} {animal_info["display_name"]} với giá {total_cost} {config.CURRENCY_SYMBOL}.')
        data_manager.save_player_data()

    @commands.command(name='sell', aliases=['s'])
    async def sell(self, ctx, item_index: int, amount: int = 1):
        try:
            user_data = data_manager.get_player_data(ctx.author.id)
            if not user_data: return await ctx.send('Bạn chưa đăng ký!')
            if amount <= 0: return await ctx.send("Số lượng phải lớn hơn 0.")

            sellable_items = self._get_sellable_items(user_data)
            index = item_index - 1
            if not (0 <= index < len(sellable_items)): return await ctx.send(f'STT `{item_index}` không hợp lệ.')

            item_key = sellable_items[index]
            if user_data['inventory'].get(item_key, 0) < amount: return await ctx.send("Bạn không có đủ vật phẩm để bán.")

            item_type, item_id = item_key.split('_', 1)
            price_per_item, name, emoji = 0, "", "❓"

            if item_type == 'crafted':
                recipe_info = config.RECIPES.get(item_id, {})
                price_per_item = recipe_info.get('sell_price', 0)
                name, emoji = recipe_info.get('display_name', '?'), recipe_info.get('emoji', '🛠️')
            elif item_type == 'harvest':
                price_per_item = config.CROPS[item_id]['sell_price']
                name, emoji = config.CROPS[item_id]['display_name'], config.CROPS[item_id]['emoji']
            elif item_type == 'seed':
                price_per_item = math.floor(config.CROPS[item_id]['seed_price'] * config.SEED_SELL_MULTIPLIER)
                name, emoji = f"Hạt {config.CROPS[item_id]['display_name']}", config.CROPS[item_id]['emoji']
            elif item_type == 'product':
                price_per_item = config.PRODUCTS[item_id]['sell_price']
                name, emoji = config.PRODUCTS[item_id]['display_name'], config.PRODUCTS[item_id]['emoji']

            if price_per_item <= 0: return await ctx.send(f"Không thể bán {name}!")

            total_earned = price_per_item * amount
            user_data['inventory'][item_key] -= amount
            if user_data['inventory'][item_key] == 0: del user_data['inventory'][item_key]
            user_data['balance'] += total_earned

            await ctx.send(f"Bạn đã bán {amount} {emoji} {name} và kiếm được {total_earned} {config.CURRENCY_SYMBOL}.")
            data_manager.save_player_data()
        except Exception as e:
            print(f"Lỗi trong lệnh !sell: {e}")
            await ctx.send("Có lỗi xảy ra khi thực hiện lệnh bán.")

    @commands.command(name='daily')
    async def daily(self, ctx):
        user_data = data_manager.get_player_data(ctx.author.id)
        if not user_data:
            return await ctx.send('Bạn chưa đăng ký. Dùng `!register` để bắt đầu!')
            
        last_claim = user_data.get('last_daily_claim')
        current_time = time.time()

        if last_claim and (current_time - last_claim) < config.SECONDS_IN_A_DAY:
            time_left = config.SECONDS_IN_A_DAY - (current_time - last_claim)
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            return await ctx.send(f'Bạn đã nhận thưởng rồi. Vui lòng quay lại sau {hours} giờ {minutes} phút.')
        
        user_data['balance'] += config.DAILY_REWARD
        user_data['last_daily_claim'] = current_time
        
        await ctx.send(f'Bạn đã nhận thưởng hàng ngày {config.DAILY_REWARD} {config.CURRENCY_SYMBOL}! Số dư hiện tại: {user_data["balance"]}.')
        data_manager.save_player_data()


async def setup(bot):
    await bot.add_cog(Economy(bot))