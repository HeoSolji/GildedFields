# cogs/economy_commands.py

import discord
from discord.ext import commands
from discord import app_commands
import time, math
import data_manager, config, season_manager, market_manager, achievement_manager


class ConfirmSellAllView(discord.ui.View):
    def __init__(self, sender_id, sell_summary, total_earnings):
        super().__init__(timeout=30.0)
        self.sender_id = sender_id
        self.sell_summary = sell_summary
        self.total_earnings = total_earnings
        self.confirmed = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.sender_id:
            await interaction.response.send_message("Đây không phải giao dịch của bạn!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if not self.confirmed:
            for item in self.children:
                item.disabled = True
            await self.message.edit(content="Đã hết thời gian xác nhận. Giao dịch bán tất cả đã bị hủy.", embed=None, view=self)

    @discord.ui.button(label="Bán tất cả", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        user_data = data_manager.get_player_data(self.sender_id)
        
        # Xóa tất cả vật phẩm có thể bán và cộng tiền
        sellable_keys_to_delete = []
        for item_key, qualities in user_data['inventory'].items():
            if not item_key.startswith('seed_'):
                sellable_keys_to_delete.append(item_key)
        
        for key in sellable_keys_to_delete:
            del user_data['inventory'][key]

        user_data['balance'] += self.total_earnings
        data_manager.save_player_data()

        for item in self.children:
            item.disabled = True
        
        final_embed = discord.Embed(
            title="✅ Giao dịch thành công!",
            description=f"Bạn đã bán tất cả vật phẩm và nhận được **{self.total_earnings} {config.CURRENCY_SYMBOL}**.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=final_embed, view=self)

    @discord.ui.button(label="Hủy", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="Đã hủy giao dịch bán tất cả.", embed=None, view=self)
class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_sellable_items(self, user_data):
        sellable_items = []
        inventory = user_data.get("inventory", {})
        type_order = ["crafted", "harvest", "product"]
        for item_type_prefix in type_order:
            for item_key in sorted(inventory.keys()):
                if item_key.startswith(item_type_prefix + "_"):
                    if isinstance(inventory.get(item_key), dict):
                        sorted_qualities = sorted(inventory[item_key].keys(), key=int, reverse=True)
                        for quality_str in sorted_qualities:
                            if inventory[item_key].get(quality_str, 0) > 0:
                                sellable_items.append((item_key, quality_str))
        return sellable_items

    def _get_item_info(self, item_key, quality_str):
        item_type, item_id = item_key.split('_', 1)
        quality = int(quality_str)
        base_name, emoji, base_price = "?", "❓", 0
        star = config.STAR_EMOJIS.get(quality, "") if quality != 5 else config.STAR_EMOJIS[5]

        if item_type == 'crafted': info = config.RECIPES.get(item_id, {}); base_name, emoji, base_price = info.get('display_name'), info.get('emoji', '🛠️'), info.get('sell_price', 0)
        elif item_type == 'harvest': info = config.CROPS.get(item_id, {}); base_name, emoji, base_price = info.get('display_name'), info.get('emoji'), info.get('sell_price', 0)
        # elif item_type == 'seed': info = config.CROPS.get(item_id, {}); base_name, emoji, base_price = f"Hạt {info.get('display_name')}", info.get('emoji'), math.floor(info.get('seed_price', 0) * config.SEED_SELL_MULTIPLIER)
        elif item_type == 'product': info = config.PRODUCTS.get(item_id, {}); base_name, emoji, base_price = info.get('display_name'), info.get('emoji'), info.get('sell_price', 0)
        
        final_price = math.floor(base_price * config.STAR_QUALITY_MULTIPLIER.get(quality, 1.0))
        display_name = f"{base_name}{star}"
        
        return display_name, emoji, final_price

    @app_commands.command(name="inventory", description="Kiểm tra kho đồ của bạn (hỗ trợ cấp sao).")
    async def inventory(self, interaction: discord.Interaction):
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.response.send_message('Bạn chưa đăng ký!', ephemeral=True)
        sellable_list = self._get_sellable_items(user_data)
        if not sellable_list: return await interaction.response.send_message('Kho đồ của bạn trống rỗng.')
        
        embed = discord.Embed(title=f"Kho đồ của {interaction.user.name}", color=discord.Color.gold())
        lines = []
        for index, (item_key, quality_str) in enumerate(sellable_list):
            quantity = user_data['inventory'][item_key][quality_str]
            name, emoji, _ = self._get_item_info(item_key, quality_str)
            lines.append(f"**{index + 1}.** {emoji} **{name}**: `{quantity}`")
        
        embed.description = "\n".join(lines)
        embed.set_footer(text="Dùng /sell [số] [lượng] để bán")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sell", description="Bán một hoặc nhiều vật phẩm từ kho đồ.")
    @app_commands.describe(danh_sách="Định dạng: 'số1 sl1, số2 sl2, ...'. Ví dụ: '1 10' hoặc '1 10, 3 5'")
    async def sell(self, interaction: discord.Interaction, danh_sách: str):
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.response.send_message('Bạn chưa đăng ký!', ephemeral=True)
        
        sellable_list = self._get_sellable_items(user_data)
        
        try:
            items_to_process = {}
            pairs = danh_sách.split(',')
            if not pairs or not pairs[0]: raise ValueError("Định dạng không hợp lệ.")

            for pair in pairs:
                parts = pair.strip().split()
                if len(parts) != 2: raise ValueError(f"Mục `{pair}` không đúng định dạng. Phải là 'STT số_lượng'.")
                
                item_index = int(parts[0]) - 1
                quantity = int(parts[1])
                
                if quantity <= 0: raise ValueError(f"Số lượng cho mục `{pair}` phải lớn hơn 0.")
                if not (0 <= item_index < len(sellable_list)): raise ValueError(f"Số thứ tự `{item_index + 1}` không hợp lệ.")
                
                item_tuple = sellable_list[item_index]
                items_to_process[item_tuple] = items_to_process.get(item_tuple, 0) + quantity

            # Kiểm tra số lượng một lần trước khi thực hiện
            for (item_key, quality_str), total_quantity in items_to_process.items():
                if user_data['inventory'][item_key].get(quality_str, 0) < total_quantity:
                    name, _, _ = self._get_item_info(item_key, quality_str)
                    raise ValueError(f"Không đủ số lượng để bán {total_quantity} {name}.")

            # Nếu mọi thứ hợp lệ, bắt đầu thực hiện bán
            await interaction.response.send_message("⏳ Đang xử lý giao dịch...", ephemeral=True)

            total_earnings = 0
            summary_lines = []
            for (item_key, quality_str), quantity in items_to_process.items():
                display_name, emoji, price_per_item = self._get_item_info(item_key, quality_str)
                modifier = market_manager.get_price_modifier(item_key)
                final_price = math.floor(price_per_item * modifier)
                total_earned_item = final_price * quantity
                total_earnings += total_earned_item

                # Trừ vật phẩm khỏi kho
                user_data['inventory'][item_key][quality_str] -= quantity
                if user_data['inventory'][item_key][quality_str] == 0: del user_data['inventory'][item_key][quality_str]
                if not user_data['inventory'][item_key]: del user_data['inventory'][item_key]
                
                summary_lines.append(f"• {quantity} {emoji} {display_name}")

            user_data['balance'] += total_earnings
            await achievement_manager.check_achievements(interaction, user_data, "balance")
            data_manager.save_player_data()

            embed = discord.Embed(title="✅ Giao dịch thành công!", color=discord.Color.green())
            embed.add_field(name="Đã bán:", value="\n".join(summary_lines), inline=False)
            embed.add_field(name="Tổng cộng nhận được:", value=f"**{total_earnings} {config.CURRENCY_SYMBOL}**")
            # Dùng followup.send vì đã có response ban đầu
            await interaction.followup.send(embed=embed)

        except ValueError as e:
            return await interaction.response.send_message(f"Lỗi cú pháp: {e}\nĐịnh dạng đúng: `/sell danh_sách: số1 sl1, số2 sl2`", ephemeral=True)
        except Exception as e:
            print(f"Lỗi trong lệnh /sell: {e}")
            await interaction.response.send_message("Có lỗi không xác định xảy ra.", ephemeral=True)

    @app_commands.command(name="sellall", description="Bán tất cả vật phẩm trong kho đồ (trừ hạt giống).")
    async def sellall(self, interaction: discord.Interaction):
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.response.send_message('Bạn chưa đăng ký!', ephemeral=True)

        sellable_list = self._get_sellable_items(user_data)
        if not sellable_list: return await interaction.response.send_message("Kho đồ của bạn không có gì để bán.", ephemeral=True)

        total_earnings = 0
        summary_lines = []
        for item_key, quality_str in sellable_list:
            quantity = user_data['inventory'][item_key][quality_str]
            display_name, emoji, price_per_item = self._get_item_info(item_key, quality_str)
            modifier = market_manager.get_price_modifier(item_key)
            final_price = math.floor(price_per_item * modifier)
            total_earned = final_price * quantity
            total_earnings += total_earned
            summary_lines.append(f"• {quantity} {emoji} {display_name} » {total_earned} {config.CURRENCY_SYMBOL}")
        
        embed = discord.Embed(title="🔍 Xác nhận Bán Tất cả", color=discord.Color.orange())
        embed.description = "Bạn có chắc muốn bán tất cả các vật phẩm sau đây không?"
        embed.add_field(name="Danh sách vật phẩm", value="\n".join(summary_lines), inline=False)
        embed.add_field(name="Tổng cộng", value=f"**Bạn sẽ nhận được: {total_earnings} {config.CURRENCY_SYMBOL}**")
        
        view = ConfirmSellAllView(interaction.user.id, summary_lines, total_earnings)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        view.message = await interaction.original_response()

    @app_commands.command(name="balance", description="Kiểm tra số dư tiền của bạn.")
    async def balance(self, interaction: discord.Interaction):
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data:
            return await interaction.response.send_message('Bạn chưa đăng ký. Dùng `/register` để bắt đầu!', ephemeral=True)
        
        await interaction.response.send_message(f'{interaction.user.mention}, bạn có {user_data["balance"]} {config.CURRENCY_SYMBOL}.')


    @app_commands.command(name="shop", description="Mở cửa hàng để xem và mua vật phẩm.")
    async def shop(self, interaction: discord.Interaction):
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.response.send_message("Bạn chưa đăng ký!", ephemeral=True)

        current_season = season_manager.get_current_season()
        season_name = current_season['name']
        
        user_balance = user_data.get('balance', 0)
        desc = (f"**Mùa hiện tại:** {current_season['display']} {current_season['emoji']}\n"
                f"**Số tiền của bạn:** {user_balance} {config.CURRENCY_SYMBOL}")
        embed = discord.Embed(title="🛒 Cửa hàng Nông trại", description=desc, color=discord.Color.green())

        seasonal_seeds = [(cid, cinfo) for cid, cinfo in config.CROPS.items() if season_name in cinfo['seasons']]
        seed_lines = [f"**{i+1}.** {info['emoji']} Hạt {info['display_name']} - {info['seed_price']} {config.CURRENCY_SYMBOL}" for i, (cid, info) in enumerate(seasonal_seeds)]
        embed.add_field(name="Hạt Giống (Dùng: /buyseed)", value="\n".join(seed_lines) if seed_lines else "Không có hạt giống nào được bán trong mùa này.", inline=False)

        seasonal_animals = [(aid, ainfo) for aid, ainfo in config.ANIMALS.items() if season_name in ainfo['seasons']]
        animal_lines = [f"**{i+1}.** {info['emoji']} {info['display_name']} - {info['buy_price']} {config.CURRENCY_SYMBOL}" for i, (aid, info) in enumerate(seasonal_animals)]
        embed.add_field(name="Vật Nuôi (Dùng: /buyanimal)", value="\n".join(animal_lines) if animal_lines else "Không có vật nuôi nào được bán trong mùa này.", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buyseed", description="Mua hạt giống từ cửa hàng.")
    @app_commands.describe(số_thứ_tự="Số thứ tự của hạt giống trong /shop.", số_lượng="Số lượng bạn muốn mua.")
    async def buy_seed(self, interaction: discord.Interaction, số_thứ_tự: int, số_lượng: int = 1):
        """Mua hạt giống từ cửa hàng."""
        # ... (phần code kiểm tra user, số lượng, mùa, index giữ nguyên)
        try:
            user_data = data_manager.get_player_data(interaction.user.id)
            if not user_data: return await interaction.response.send_message('Bạn chưa đăng ký!', ephemeral=True)
            if số_lượng <= 0: return await interaction.response.send_message("Số lượng phải lớn hơn 0.", ephemeral=True)

            current_season = season_manager.get_current_season()['name']
            seasonal_shop_items = [(cid, cinfo) for cid, cinfo in config.CROPS.items() if current_season in cinfo['seasons']]
            
            index = số_thứ_tự - 1
            if not (0 <= index < len(seasonal_shop_items)): return await interaction.response.send_message(f'STT `{số_thứ_tự}` không hợp lệ cho mùa này.', ephemeral=True)

            crop_id, crop_info = seasonal_shop_items[index]
            total_cost = crop_info['seed_price'] * số_lượng
            if user_data['balance'] < total_cost: return await interaction.response.send_message(f'Bạn không đủ tiền!', ephemeral=True)

            user_data['balance'] -= total_cost
            
            # --- LOGIC MỚI: LƯU HẠT GIỐNG VỚI ĐÚNG CẤU TRÚC ---
            seed_key = f"seed_{crop_id}"
            # setdefault sẽ tạo ra dict rỗng {} nếu seed_key chưa tồn tại
            user_data['inventory'].setdefault(seed_key, {})
            # Thêm số lượng vào bucket chất lượng "0" (vì hạt giống không có sao)
            user_data['inventory'][seed_key]['0'] = user_data['inventory'][seed_key].get('0', 0) + số_lượng
            # ---------------------------------------------------
            
            await interaction.response.send_message(f'Bạn đã mua {số_lượng} {crop_info["emoji"]} Hạt {crop_info["display_name"]} với giá {total_cost} {config.CURRENCY_SYMBOL}.')
            data_manager.save_player_data()
        except Exception as e:
            print(f"Lỗi trong lệnh /buyseed: {e}")
            await interaction.response.send_message("Có lỗi xảy ra khi mua hạt giống.", ephemeral=True)


    @app_commands.command(name="buyanimal", description="Mua vật nuôi từ cửa hàng.")
    @app_commands.describe(số_thứ_tự="Số thứ tự của vật nuôi trong /shop.", số_lượng="Số lượng bạn muốn mua.")
    async def buy_animal(self, interaction: discord.Interaction, số_thứ_tự: int, số_lượng: int = 1):
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.response.send_message('Bạn chưa đăng ký!', ephemeral=True)
        if số_lượng <= 0: return await interaction.response.send_message("Số lượng phải lớn hơn 0.", ephemeral=True)

        current_season = season_manager.get_current_season()['name']
        seasonal_shop_items = [(aid, ainfo) for aid, ainfo in config.ANIMALS.items() if current_season in ainfo['seasons']]
        index = số_thứ_tự - 1
        if not (0 <= index < len(seasonal_shop_items)): return await interaction.response.send_message(f'STT `{số_thứ_tự}` không hợp lệ cho mùa này.', ephemeral=True)
        
        animal_id, animal_info = seasonal_shop_items[index]
        barn = user_data['barn']
        current_animal_count = sum(len(animal_list) for animal_list in barn.get('animals', {}).values())
        if current_animal_count + số_lượng > barn['capacity']:
            return await interaction.response.send_message(f"Chuồng không đủ chỗ!", ephemeral=True)

        total_cost = animal_info['buy_price'] * số_lượng
        if user_data['balance'] < total_cost: return await interaction.response.send_message(f'Bạn không đủ tiền!', ephemeral=True)

        user_data['balance'] -= total_cost
        current_time = time.time()
        new_ready_times = [current_time + animal_info['production_time']] * số_lượng
        if animal_id in barn['animals']: barn['animals'][animal_id].extend(new_ready_times)
        else: barn['animals'][animal_id] = new_ready_times
        user_data['barn']['notification_sent'] = False
        
        await interaction.response.send_message(f'Bạn đã mua {số_lượng} {animal_info["emoji"]} {animal_info["display_name"]} với giá {total_cost} {config.CURRENCY_SYMBOL}.')
        data_manager.save_player_data()


    @app_commands.command(name="market", description="Kiểm tra các sự kiện thị trường đang diễn ra.")
    async def market(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📈 Bản Tin Thị Trường Nông Sản 📉",
            description=market_manager.current_event_message,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Nhận phần thưởng hàng ngày.")
    async def daily(self, interaction: discord.Interaction):
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.response.send_message('Bạn chưa đăng ký!', ephemeral=True)
            
        last_claim = user_data.get('last_daily_claim')
        current_time = time.time()

        if last_claim and (current_time - last_claim) < config.SECONDS_IN_A_DAY:
            time_left = config.SECONDS_IN_A_DAY - (current_time - last_claim)
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            return await interaction.response.send_message(f'Bạn đã nhận thưởng rồi. Vui lòng quay lại sau {hours} giờ {minutes} phút.', ephemeral=True)
        
        user_data['balance'] += config.DAILY_REWARD
        user_data['last_daily_claim'] = current_time
        
        await interaction.response.send_message(f'Bạn đã nhận thưởng hàng ngày {config.DAILY_REWARD} {config.CURRENCY_SYMBOL}! Số dư hiện tại: {user_data["balance"]}.')
        data_manager.save_player_data()

async def setup(bot):
    await bot.add_cog(Economy(bot))