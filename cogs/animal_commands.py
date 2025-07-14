# cogs/animal_commands.py

import discord
from discord.ext import commands
from discord import app_commands
import time
import datetime
import data_manager
import config
import utils

class BarnView(discord.ui.View):
    def __init__(self, user_id, timeout=180):
        super().__init__(timeout=timeout)
        self.user_id = user_id

    @discord.ui.button(label="Xem thời gian chi tiết", style=discord.ButtonStyle.secondary, emoji="⏰")
    async def show_times(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("Đây không phải chuồng của bạn!", ephemeral=True)

        user_data = data_manager.get_player_data(self.user_id)
        if not user_data: return await interaction.response.send_message("Không tìm thấy dữ liệu.", ephemeral=True)

        animals_in_barn = user_data.get('barn', {}).get('animals', {})
        if not animals_in_barn: return await interaction.response.send_message("Chuồng của bạn trống trơn.", ephemeral=True)
        
        current_time = time.time()
        lines = []
        for animal_id, ready_times in animals_in_barn.items():
            animal_info = config.ANIMALS.get(animal_id)
            if not animal_info or not ready_times: continue
            
            lines.append(f"**{animal_info['emoji']} {animal_info['display_name']}:**")
            
            # Lấy emoji của con vật để dùng trong danh sách
            animal_emoji = animal_info['emoji']

            for i, ready_time in enumerate(ready_times):
                time_left = ready_time - current_time
                # SỬA ĐỔI: Thay "Con #" bằng emoji của con vật
                if time_left > 0:
                    lines.append(f"  • {animal_emoji}{i+1}: Còn lại `{str(datetime.timedelta(seconds=int(time_left)))}`")
                else:
                    lines.append(f"  • {animal_emoji}{i+1}: ✅ Đã sẵn sàng!")
        
        content = "\n".join(lines)
        await interaction.response.send_message(content, ephemeral=True)

class AnimalCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    barn = app_commands.Group(name="barn", description="Các lệnh liên quan đến chuồng nuôi của bạn.")

    @barn.command(name="view", description="Xem chuồng nuôi và tình trạng sản phẩm.")
    async def barn_view(self, interaction: discord.Interaction):
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.response.send_message('Bạn chưa đăng ký!', ephemeral=True)

        barn = user_data.get('barn', {'animals': {}, 'capacity': config.INITIAL_BARN_CAPACITY})
        animals_in_barn = barn.get('animals', {})
        capacity = barn.get('capacity', config.INITIAL_BARN_CAPACITY)
        current_animal_count = sum(len(animal_list) for animal_list in animals_in_barn.values())

        title = f"Chuồng nuôi của {interaction.user.name} (Sức chứa: {current_animal_count}/{capacity})"
        embed = discord.Embed(title=title, color=discord.Color.from_rgb(188, 143, 143))

        if not animals_in_barn:
            embed.description = "Chuồng của bạn trống trơn. Dùng `/shop` để mua vật nuôi."
            return await interaction.response.send_message(embed=embed)
        
        description_lines = []
        current_time = time.time()
        for animal_id, ready_times in animals_in_barn.items():
            if not ready_times: continue
            animal_info = config.ANIMALS.get(animal_id)
            if not animal_info: continue
            product_info = config.PRODUCTS.get(animal_info['product_id'])
            
            ready_count = sum(1 for rt in ready_times if current_time >= rt)
            waiting_list = [rt for rt in ready_times if current_time < rt]

            line = f"**{len(ready_times)}x** {animal_info['emoji']} **{animal_info['display_name']}** -> {product_info['emoji']} {product_info['display_name']}\n"
            if ready_count > 0:
                line += f"✅ **{ready_count}** sản phẩm đã sẵn sàng!\n"
            if waiting_list:
                line += f"⏳ `{len(waiting_list)}` con khác đang chờ..."
            description_lines.append(line)
        
        embed.description = "\n\n".join(description_lines)
        embed.set_footer(text="Dùng /collect để thu hoạch. Dùng /barn upgrade để nâng cấp.")
        await interaction.response.send_message(embed=embed, view=BarnView(user_id=interaction.user.id))

    @barn.command(name="upgrade", description="Nâng cấp sức chứa chuồng nuôi của bạn.")
    async def barn_upgrade(self, interaction: discord.Interaction):
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.response.send_message("Bạn chưa đăng ký!", ephemeral=True)
            
        barn_data = user_data.get('barn', {})
        current_capacity = barn_data.get('capacity', config.INITIAL_BARN_CAPACITY)
        user_balance = user_data.get('balance', 0)
        user_level = user_data.get('level', 1)

        if current_capacity >= config.MAX_BARN_CAPACITY:
            return await interaction.response.send_message("Chuồng của bạn đã đạt sức chứa tối đa!", ephemeral=True)

        # Tìm cấp nâng cấp tiếp theo
        next_upgrade_level = None
        for capacity in sorted(config.BARN_UPGRADES.keys()):
            if capacity > current_capacity:
                next_upgrade_level = capacity
                break
        
        if next_upgrade_level is None:
            return await interaction.response.send_message("Không có thông tin nâng cấp nào cho chuồng của bạn.", ephemeral=True)

        upgrade_info = config.BARN_UPGRADES[next_upgrade_level]
        cost = upgrade_info['cost']
        level_required = upgrade_info['level_required']

        # Tạo tin nhắn xác nhận
        embed = discord.Embed(title="Xác nhận Nâng cấp Chuồng", color=discord.Color.blue())
        embed.description = (
            f"Bạn có chắc muốn nâng cấp sức chứa chuồng lên **{next_upgrade_level}** không?\n\n"
            f"**Chi phí:** {cost} {config.CURRENCY_SYMBOL}\n"
            f"**Yêu cầu:** Cấp {level_required}\n\n"
            f"**Số dư của bạn:** {user_balance} {config.CURRENCY_SYMBOL}"
        )

        if user_level < level_required:
            embed.description += f"\n\n❌ Bạn chưa đủ cấp độ!"
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        if user_balance < cost:
            embed.description += f"\n\n❌ Bạn không có đủ tiền!"
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # Nếu đủ điều kiện, thực hiện nâng cấp
        user_data['balance'] -= cost
        user_data['barn']['capacity'] = next_upgrade_level
        data_manager.save_player_data()
        
        await interaction.response.send_message(f"🎉 **Chúc mừng!** Bạn đã chi {cost} {config.CURRENCY_SYMBOL} để nâng cấp thành công sức chứa chuồng lên **{next_upgrade_level}**!")

    @app_commands.command(name="collect", description="Thu hoạch tất cả sản phẩm từ vật nuôi.")
    async def collect(self, interaction: discord.Interaction):
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.response.send_message('Bạn chưa đăng ký!', ephemeral=True)
        
        animals_in_barn = user_data.get('barn', {}).get('animals', {})
        if not animals_in_barn: return await interaction.response.send_message("Bạn không có con vật nào để thu hoạch.")

        await interaction.response.send_message("Đang kiểm tra và thu hoạch sản phẩm...")

        collected_products = {}
        current_time = time.time()
        something_collected = False

        for animal_id, ready_times in animals_in_barn.items():
            animal_info = config.ANIMALS.get(animal_id)
            if not animal_info: continue
            
            still_producing_times = []
            for ready_time in ready_times:
                if current_time >= ready_time:
                    something_collected = True
                    product_id = animal_info['product_id']
                    quality = utils.determine_quality()
                    quality_str = str(quality)
                    collected_products.setdefault(product_id, {})[quality_str] = collected_products.setdefault(product_id, {}).get(quality_str, 0) + 1
                    
                    still_producing_times.append(current_time + animal_info['production_time'])
                else:
                    still_producing_times.append(ready_time)
            
            animals_in_barn[animal_id] = still_producing_times

        if not something_collected:
            return await interaction.edit_original_response(content="Chưa có sản phẩm nào sẵn sàng để thu hoạch.")

        lines = []
        for product_id, qualities in collected_products.items():
            inventory_key = f"product_{product_id}"
            user_data['inventory'].setdefault(inventory_key, {})
            
            for quality_str, quantity in qualities.items():
                user_data['inventory'][inventory_key][quality_str] = user_data['inventory'][inventory_key].get(quality_str, 0) + quantity
                star_emoji = config.STAR_EMOJIS.get(int(quality_str), "")
                product_info = config.PRODUCTS[product_id]
                lines.append(f"{quantity} {product_info['emoji']}{star_emoji}")
        user_data['barn']['notification_sent'] = True
        await interaction.followup.send(f"Bạn đã thu hoạch thành công: {', '.join(lines)}.\nCác con vật vừa thu hoạch đã bắt đầu một chu trình sản xuất mới.")
        data_manager.save_player_data()


async def setup(bot):
    await bot.add_cog(AnimalCommands(bot))