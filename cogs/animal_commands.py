# cogs/animal_commands.py

import discord
from discord.ext import commands
import time
import datetime
import data_manager
import config
import achievement_manager

class AnimalCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='barn', aliases=['chuong'])
    async def barn(self, ctx):
        """Xem chuồng nuôi và tình trạng sản phẩm của từng con vật."""
        user_data = data_manager.get_player_data(ctx.author.id)
        if not user_data: return await ctx.send('Bạn chưa đăng ký!')

        barn = user_data.get('barn', {'animals': {}, 'capacity': config.INITIAL_BARN_CAPACITY})
        animals_in_barn = barn.get('animals', {})
        capacity = barn.get('capacity', config.INITIAL_BARN_CAPACITY)
        current_animal_count = sum(len(animal_list) for animal_list in animals_in_barn.values())

        title = f"Chuồng nuôi của {ctx.author.name} ({current_animal_count}/{capacity})"
        embed = discord.Embed(title=title, color=discord.Color.from_rgb(188, 143, 143))

        if not animals_in_barn:
            embed.description = "Chuồng của bạn trống trơn. Dùng `!shop` để mua vật nuôi."
            return await ctx.send(embed=embed)
        
        description_lines = []
        current_time = time.time()
        for animal_id, ready_times in animals_in_barn.items():
            if not ready_times: continue # Bỏ qua nếu không có con vật nào

            animal_info = config.ANIMALS.get(animal_id)
            if not animal_info: continue

            product_info = config.PRODUCTS.get(animal_info['product_id'])
            
            ready_count = 0
            waiting_list = []

            for ready_time in ready_times:
                if current_time >= ready_time:
                    ready_count += 1
                else:
                    time_left = ready_time - current_time
                    td = datetime.timedelta(seconds=int(time_left))
                    waiting_list.append(str(td))

            line = f"**{len(ready_times)}x** {animal_info['emoji']} **{animal_info['display_name']}** -> {product_info['emoji']} {product_info['display_name']}\n"
            if ready_count > 0:
                line += f"✅ **{ready_count}** sản phẩm đã sẵn sàng!\n"
            if waiting_list:
                # Hiển thị thời gian của 3 con vật sắp tới để tránh spam
                line += f"⏳ `{len(waiting_list)}` con khác đang chờ: `{'`, `'.join(waiting_list[:3])}`..."

            description_lines.append(line)
        
        embed.description = "\n\n".join(description_lines)
        embed.set_footer(text="Dùng !collect để thu hoạch tất cả sản phẩm đã sẵn sàng.")
        await ctx.send(embed=embed)

    @commands.command(name='collect')
    async def collect(self, ctx):
        """Thu hoạch tất cả sản phẩm từ vật nuôi đã sẵn sàng."""
        user_data = data_manager.get_player_data(ctx.author.id)
        if not user_data: return await ctx.send('Bạn chưa đăng ký!')
        
        animals_in_barn = user_data.get('barn', {}).get('animals', {})
        if not animals_in_barn: return await ctx.send("Bạn không có con vật nào để thu hoạch.")

        collected_products = {}
        current_time = time.time()
        something_collected = False

        for animal_id, ready_times in animals_in_barn.items():
            animal_info = config.ANIMALS.get(animal_id)
            if not animal_info: continue

            still_producing_times = [] # Danh sách các con vật chưa xong
            
            for ready_time in ready_times:
                if current_time >= ready_time:
                    # Thu hoạch con vật này
                    something_collected = True
                    product_id = animal_info['product_id']
                    collected_products[product_id] = collected_products.get(product_id, 0) + 1
                    
                    # Tạo đồng hồ mới cho con vật vừa thu hoạch
                    new_ready_time = current_time + animal_info['production_time']
                    still_producing_times.append(new_ready_time)
                else:
                    # Giữ lại con vật chưa xong
                    still_producing_times.append(ready_time)
            
            # Cập nhật lại danh sách của loại vật nuôi này
            animals_in_barn[animal_id] = still_producing_times

        if not something_collected:
            return await ctx.send("Chưa có sản phẩm nào sẵn sàng để thu hoạch.")

        lines = []
        for product_id, quantity in collected_products.items():
            inventory_key = f"product_{product_id}"
            user_data['inventory'][inventory_key] = user_data['inventory'].get(inventory_key, 0) + quantity
            product_info = config.PRODUCTS[product_id]
            lines.append(f"{quantity} {product_info['emoji']} {product_info['display_name']}")
            await achievement_manager.check_achievements(ctx, user_data, "collect", event_id=product_id, amount=quantity)
        
        await ctx.send(f"Bạn đã thu hoạch thành công: {', '.join(lines)}.\nCác con vật vừa thu hoạch đã bắt đầu một chu trình sản xuất mới.")
        data_manager.save_player_data()


async def setup(bot):
    await bot.add_cog(AnimalCommands(bot))