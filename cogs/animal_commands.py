# cogs/animal_commands.py

import discord
from discord.ext import commands
from discord import app_commands
import time, datetime, uuid, math
import data_manager, config, utils, achievement_manager, quest_manager

class BarnView(discord.ui.View):
    """View chứa nút 'Xem thời gian' cho lệnh /barn view."""
    def __init__(self, user_id, timeout=180):
        super().__init__(timeout=timeout)
        self.user_id = user_id

    @discord.ui.button(label="Xem thời gian chi tiết", style=discord.ButtonStyle.secondary, emoji="⏰")
    async def show_times(self, interaction: discord.Interaction, button: discord.ui.Button):
        # SỬA LỖI: Thêm defer() để tránh timeout
        await interaction.response.defer(ephemeral=True)

        if interaction.user.id != self.user_id:
            return await interaction.followup.send("Đây không phải chuồng của bạn!")

        user_data = data_manager.get_player_data(self.user_id)
        if not user_data: return await interaction.followup.send("Không tìm thấy dữ liệu.")
        
        barn_animals = user_data.get('barn', {}).get('animals', {})
        if not any(barn_animals.values()): return await interaction.followup.send("Chuồng của bạn trống trơn.")
        
        current_time = time.time()
        lines = []
        for animal_id, animal_list in barn_animals.items():
            if not animal_list: continue
            animal_info = config.ANIMALS.get(animal_id, {})
            lines.append(f"**{animal_info.get('emoji', '')} {animal_info.get('display_name', '?')}:**")
            
            for animal in animal_list:
                time_left = animal.get('ready_time', 0) - current_time
                if time_left > 0:
                    lines.append(f"  • **{animal.get('name', 'N/A')}**: Còn lại `{str(datetime.timedelta(seconds=int(time_left)))}`")
                else:
                    lines.append(f"  • **{animal.get('name', 'N/A')}**: ✅ Đã sẵn sàng!")
        
        content = "\n".join(lines)
        await interaction.followup.send(content)

class AnimalSellView(discord.ui.View):
    """Giao diện bán vật nuôi có bước xác nhận."""
    def __init__(self, author, animals_to_sell):
        super().__init__(timeout=60.0)
        self.author = author
        self.message = None
        self.selected_animal_value = None

        # Thêm menu chọn vào hàng đầu tiên
        self.select_menu = AnimalSellSelect(animals_to_sell)
        self.add_item(self.select_menu)

        # Thêm các nút bấm nhưng vô hiệu hóa chúng ban đầu
        self.confirm_button = discord.ui.Button(label="Xác nhận Bán", style=discord.ButtonStyle.green, disabled=True, row=1)
        self.confirm_button.callback = self.confirm_sale
        self.add_item(self.confirm_button)

        self.cancel_button = discord.ui.Button(label="Hủy", style=discord.ButtonStyle.red, row=1)
        self.cancel_button.callback = self.cancel
        self.add_item(self.cancel_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Đây không phải giao dịch của bạn!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if self.message:
            for item in self.children: item.disabled = True
            await self.message.edit(content="Đã hết thời gian. Giao dịch bị hủy.", view=self)

    async def process_selection(self, interaction: discord.Interaction, value: str):
        try:
            # Phản hồi ngay lập tức để tránh timeout
            await interaction.response.defer()

            if value == 'none':
                for item in self.children: item.disabled = True
                await interaction.edit_original_response(content="Không có vật nuôi nào để bán.", view=self)
                return

            self.selected_animal_value = value
            self.confirm_button.disabled = False

            animal_type_id, animal_id = value.split('|')
            user_data = data_manager.get_player_data(self.author.id)
            animal_list = user_data.get('barn', {}).get('animals', {}).get(animal_type_id, [])
            animal_name = "Không tìm thấy"
            for animal in animal_list:
                if animal.get('id') == animal_id:
                    animal_name = animal.get('name', 'N/A')
                    break
            
            await interaction.edit_original_response(content=f"Bạn đã chọn bán **{animal_name}**. Vui lòng xác nhận.", view=self)
        except Exception as e:
            print(f"Lỗi trong process_selection: {e}")
            await interaction.followup.send("Có lỗi xảy ra khi chọn vật phẩm.", ephemeral=True)

    # Hàm được gọi bởi nút Xác nhận
    async def confirm_sale(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        user_data = data_manager.get_player_data(self.author.id)
        barn_animals = user_data.get('barn', {}).get('animals', {})
        
        animal_type_id, animal_id_to_sell = self.selected_animal_value.split('|')
        animal_list = barn_animals.get(animal_type_id, [])
        
        sold_animal_info = None
        for animal in animal_list:
            if animal['id'] == animal_id_to_sell:
                sell_price = math.floor(config.ANIMALS[animal_type_id]['buy_price'] * config.ANIMAL_SELL_MULTIPLIER)
                user_data['balance'] += sell_price
                animal_list.remove(animal)
                sold_animal_info = {"name": animal['name'], "price": sell_price}
                break
        
        data_manager.save_player_data()
        for item in self.children: item.disabled = True

        if sold_animal_info:
            await interaction.edit_original_response(
                content=f"✅ Bạn đã bán thành công **{sold_animal_info['name']}** và nhận được {sold_animal_info['price']} {config.CURRENCY_SYMBOL}.",
                view=self
            )
        else:
            await interaction.edit_original_response(content="Lỗi: Không tìm thấy con vật để bán.", view=self)

    # Hàm được gọi bởi nút Hủy
    async def cancel(self, interaction: discord.Interaction):
        for item in self.children: item.disabled = True
        await interaction.response.edit_message(content="Đã hủy giao dịch.", view=self)

class AnimalSellSelect(discord.ui.Select):
    """Menu chọn con vật để bán."""
    def __init__(self, animals_to_sell):
        options = [discord.SelectOption(
            label=f"{animal['name']} ({animal['type_name']})",
            value=f"{animal['type_id']}|{animal['id']}",
            emoji=animal['emoji']
        ) for animal in animals_to_sell]
        
        if not options:
            options.append(discord.SelectOption(label="Không có gì để bán", value="none", emoji="❌"))

        super().__init__(placeholder="Chọn một con vật để bán...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # Khi người dùng chọn, gọi đến hàm xử lý trong View cha
        await self.view.process_selection(interaction, self.values[0])


class RenameAnimalModal(discord.ui.Modal, title="Đổi tên Vật nuôi"):
    """Cửa sổ pop-up để nhập tên mới."""
    new_name = discord.ui.TextInput(
        label="Tên mới cho vật nuôi",
        placeholder="Nhập tên bạn muốn đặt...",
        max_length=20
    )

    def __init__(self, animal_value: str):
        super().__init__()
        self.animal_value = animal_value

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_data = data_manager.get_player_data(interaction.user.id)
        barn_animals = user_data.get('barn', {}).get('animals', {})
        
        animal_type_id, animal_id_to_rename = self.animal_value.split('|')
        animal_list = barn_animals.get(animal_type_id, [])
        
        renamed = False
        for animal in animal_list:
            if animal.get('id') == animal_id_to_rename:
                old_name = animal.get('name', 'N/A')
                animal['name'] = self.new_name.value
                renamed = True
                break
        
        if renamed:
            data_manager.save_player_data()
            await interaction.followup.send(f"✅ Đã đổi tên thành công từ **{old_name}** thành **{self.new_name.value}**!", ephemeral=True)
        else:
            await interaction.followup.send("Lỗi: Không tìm thấy con vật để đổi tên.", ephemeral=True)

class RenameAnimalSelect(discord.ui.Select):
    """Menu chọn con vật để đổi tên."""
    def __init__(self, animals_to_rename):
        options = [discord.SelectOption(
            label=f"{animal['name']} ({animal['type_name']})",
            value=f"{animal['type_id']}|{animal['id']}",
            emoji=animal['emoji']
        ) for animal in animals_to_rename]
        super().__init__(placeholder="Chọn một con vật để đổi tên...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # Mở cửa sổ pop-up khi người dùng chọn
        await interaction.response.send_modal(RenameAnimalModal(self.values[0]))
class AnimalCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    barn = app_commands.Group(name="barn", description="Các lệnh liên quan đến chuồng nuôi của bạn.")

    @barn.command(name="rename", description="Đổi tên cho một con vật cưng của bạn.")
    async def barn_rename(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_data = data_manager.get_player_data(interaction.user.id)
        barn_animals = user_data.get('barn', {}).get('animals', {})
        
        animals_to_rename = []
        for animal_type, animal_list in barn_animals.items():
            for animal in animal_list:
                animals_to_rename.append({
                    "id": animal.get('id'), "name": animal.get('name'),
                    "type_id": animal_type,
                    "type_name": config.ANIMALS[animal_type]['display_name'],
                    "emoji": config.ANIMALS[animal_type]['emoji']
                })
        
        if not animals_to_rename:
            return await interaction.followup.send("Bạn không có con vật nào để đổi tên.", ephemeral=True)

        view = discord.ui.View(timeout=60.0)
        view.add_item(RenameAnimalSelect(animals_to_rename))
        await interaction.followup.send("Chọn con vật bạn muốn đổi tên:", view=view)


    @barn.command(name="sell", description="Bán một con vật từ chuồng của bạn.")
    async def barn_sell(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            user_data = data_manager.get_player_data(interaction.user.id)
            if not user_data:
                return await interaction.followup.send("Bạn chưa đăng ký!")

            barn_animals = user_data.get('barn', {}).get('animals', {})
            
            animals_to_sell = []
            for animal_type, animal_list in barn_animals.items():
                if not isinstance(animal_list, list): continue
                for animal in animal_list:
                    if isinstance(animal, dict):
                        animals_to_sell.append({
                            "id": animal.get('id'), "name": animal.get('name'),
                            "type_id": animal_type,
                            "type_name": config.ANIMALS[animal_type]['display_name'],
                            "emoji": config.ANIMALS[animal_type]['emoji']
                        })
            
            if not animals_to_sell:
                return await interaction.followup.send("Bạn không có con vật nào để bán.", ephemeral=True)

            message_content = "Chọn con vật bạn muốn bán từ menu dưới đây:"
            if len(animals_to_sell) > 25:
                message_content += "\n\n⚠️ **Lưu ý:** Bạn có quá nhiều vật nuôi! Chỉ 25 con đầu tiên được hiển thị."
                animals_to_sell = animals_to_sell[:25]

            # SỬA LỖI: Truyền `animals_to_sell` vào khi tạo View
            view = AnimalSellView(interaction.user, animals_to_sell)
            
            await interaction.followup.send(message_content, view=view)
            view.message = await interaction.original_response()
        except Exception as e:
            print(f"Lỗi trong lệnh /barn sell: {e}")
            await interaction.followup.send("Có lỗi xảy ra khi thực hiện lệnh bán.", ephemeral=True)
    
    @barn.command(name="view", description="Xem chuồng nuôi, tên và trạng thái của từng con vật.")
    async def barn_view(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.followup.send('Bạn chưa đăng ký!')

        barn_data = user_data.get('barn', {})
        animals_data = barn_data.get('animals', {})
        capacity = barn_data.get('capacity', config.INITIAL_BARN_CAPACITY)
        current_animal_count = sum(len(animal_list) for animal_list in animals_data.values())

        embed = discord.Embed(title=f"Chuồng nuôi của {interaction.user.name} ({current_animal_count}/{capacity})", color=discord.Color.dark_orange())
        
        if not current_animal_count:
            embed.description = "Chuồng của bạn trống trơn."
        else:
            current_time = time.time()
            for animal_id, animal_list in animals_data.items():
                if not animal_list: continue
                
                animal_info = config.ANIMALS.get(animal_id, {})
                field_lines = []
                for animal in animal_list:
                    # Thêm kiểm tra an toàn, nếu animal không phải dict thì bỏ qua
                    if not isinstance(animal, dict): continue
                    
                    time_left = animal.get('ready_time', 0) - current_time
                    status = "✅ Đã sẵn sàng!" if time_left <= 0 else f"⏳ Còn lại `{str(datetime.timedelta(seconds=int(time_left)))}`"
                    field_lines.append(f"• **{animal.get('name', 'N/A')}**: {status}")
                
                if field_lines:
                    embed.add_field(
                        name=f"{animal_info.get('emoji', '')} {animal_info.get('display_name', '?')} ({len(animal_list)})",
                        value="\n".join(field_lines),
                        inline=False
                    )
        
        embed.set_footer(text="Dùng /collect để thu hoạch và /barn sell để bán.")
        await interaction.followup.send(embed=embed, view=BarnView(user_id=interaction.user.id))

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
        await interaction.response.defer()
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.followup.send("Bạn chưa đăng ký!", ephemeral=True)
        
        animals_data = user_data.get('barn', {}).get('animals', {})
        collected_products = {}
        current_time = time.time()
        something_collected = False

        for animal_id, animal_list in animals_data.items():
            animal_info = config.ANIMALS.get(animal_id)
            if not animal_info: continue
            
            for animal in animal_list:
                if current_time >= animal.get('ready_time', float('inf')):
                    something_collected = True
                    product_id = animal_info['product_id']
                    quality = utils.determine_quality()
                    quality_str = str(quality)
                    
                    collected_products.setdefault(product_id, {})[quality_str] = collected_products.setdefault(product_id, {}).get(quality_str, 0) + 1
                    
                    # Reset lại thời gian cho chính con vật này
                    animal['ready_time'] = current_time + animal_info['production_time']
        
        if not something_collected:
            return await interaction.followup.send("Chưa có sản phẩm nào sẵn sàng để thu hoạch.", ephemeral=True)
        
        summary_lines = []
        total_collected_amount = 0
        for product_id, qualities in collected_products.items():
            inventory_key = f"product_{product_id}"
            user_data['inventory'].setdefault(inventory_key, {})
            for quality_str, quantity in qualities.items():
                user_data['inventory'][inventory_key][quality_str] = user_data['inventory'][inventory_key].get(quality_str, 0) + quantity
                total_collected_amount += quantity
                star_emoji = config.STAR_EMOJIS.get(int(quality_str), "")
                product_info = config.PRODUCTS[product_id]
                summary_lines.append(f"{quantity} {product_info['emoji']}{star_emoji}")
        
        await quest_manager.update_quest_progress(interaction, "collect_total", amount=total_collected_amount)
        
        user_data['barn']['notification_sent'] = True
        data_manager.save_player_data()
        await interaction.followup.send(f"Bạn đã thu hoạch thành công: {', '.join(summary_lines)}.")

async def setup(bot):
    await bot.add_cog(AnimalCommands(bot))