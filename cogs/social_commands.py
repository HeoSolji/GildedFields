# cogs/social_commands.py

import discord
from discord.ext import commands
from discord import app_commands
import data_manager
import config

# --- VIEW VỚI NÚT BẤM ĐỂ XÁC NHẬN ---
class ConfirmGiftView(discord.ui.View):
    def __init__(self, sender, receiver, item_key, amount, item_name, item_emoji):
        super().__init__(timeout=30.0) # Hết hạn sau 30 giây
        self.sender = sender
        self.receiver = receiver
        self.item_key = item_key
        self.amount = amount
        self.item_name = item_name
        self.item_emoji = item_emoji

    async def on_timeout(self):
        # Tự động vô hiệu hóa nút và cập nhật tin nhắn khi hết giờ
        for item in self.children:
            item.disabled = True
        await self.message.edit(content="Đã hết thời gian xác nhận. Giao dịch bị hủy.", view=self)

    # Nút xác nhận
    @discord.ui.button(label="Xác nhận", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Chỉ người gửi mới được bấm
        if interaction.user.id != self.sender.id:
            return await interaction.response.send_message("Đây không phải giao dịch của bạn!", ephemeral=True)

        sender_data = data_manager.get_player_data(self.sender.id)
        receiver_data = data_manager.get_player_data(self.receiver.id)

        # Kiểm tra lại lần cuối
        if sender_data['inventory'].get(self.item_key, 0) < self.amount:
            return await interaction.response.edit_message(content="Lỗi: Bạn không còn đủ vật phẩm để tặng.", view=None)

        # Thực hiện giao dịch
        sender_data['inventory'][self.item_key] -= self.amount
        if sender_data['inventory'][self.item_key] == 0: del sender_data['inventory'][self.item_key]
        receiver_data['inventory'][self.item_key] = receiver_data['inventory'].get(self.item_key, 0) + self.amount
        data_manager.save_player_data()

        await achievement_manager.check_achievements(interaction, sender_data, "gift")
        
        # Vô hiệu hóa các nút và cập nhật tin nhắn
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content=f"✅ Giao dịch thành công! Bạn đã tặng {self.amount} {self.item_emoji} {self.item_name} cho {self.receiver.mention}.", view=self)
        try:
            await self.receiver.send(f"🎁 Bạn vừa nhận được **{self.amount} {self.item_emoji} {self.item_name}** từ {self.sender.mention}!")
        except discord.Forbidden:
            pass

    # Nút hủy
    @discord.ui.button(label="Hủy", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.sender.id:
            return await interaction.response.send_message("Đây không phải giao dịch của bạn!", ephemeral=True)
        
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="Đã hủy giao dịch.", view=self)


class SocialCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _get_inventory_items(self, user_data): # Hàm trợ giúp
        # ... (Sao chép lại hàm _get_inventory_items từ economy_commands)
        items = []
        inv = user_data.get("inventory", {})
        for k in sorted(inv.keys()):
            if inv[k] > 0: items.append(k)
        return items

    def _get_item_info(self, item_key): # Hàm trợ giúp
        item_type, item_id = item_key.split('_', 1)
        name, emoji = "?", "❓"
        if item_type == "crafted": r = config.RECIPES.get(item_id, {}); name, emoji = r.get('display_name'), r.get('emoji')
        elif item_type == "seed": c = config.CROPS.get(item_id, {}); name, emoji = f"Hạt {c.get('display_name')}", c.get('emoji')
        elif item_type == "harvest": c = config.CROPS.get(item_id, {}); name, emoji = c.get('display_name'), c.get('emoji')
        elif item_type == "product": p = config.PRODUCTS.get(item_id, {}); name, emoji = p.get('display_name'), p.get('emoji')
        return name, emoji

    @app_commands.command(name="gift", description="Tặng vật phẩm trong kho đồ cho người khác.")
    @app_commands.describe(người_nhận="Người bạn muốn tặng quà.", số_thứ_tự="Số thứ tự của vật phẩm trong /inventory.", số_lượng="Số lượng bạn muốn tặng.")
    async def gift(self, interaction: discord.Interaction, người_nhận: discord.Member, số_thứ_tự: int, số_lượng: int):
        sender = interaction.user
        if sender == người_nhận: return await interaction.response.send_message("Bạn không thể tặng quà cho chính mình!", ephemeral=True)
        if số_lượng <= 0: return await interaction.response.send_message("Số lượng quà tặng phải lớn hơn 0.", ephemeral=True)

        sender_data = data_manager.get_player_data(sender.id)
        if not data_manager.get_player_data(người_nhận.id): return await interaction.response.send_message(f"Người chơi {người_nhận.mention} chưa đăng ký game.", ephemeral=True)

        inventory_items = self._get_inventory_items(sender_data)
        index = số_thứ_tự - 1

        if not (0 <= index < len(inventory_items)): return await interaction.response.send_message(f"STT `{số_thứ_tự}` không hợp lệ.", ephemeral=True)

        item_key = inventory_items[index]
        item_name, item_emoji = self._get_item_info(item_key)
        
        if sender_data['inventory'].get(item_key, 0) < số_lượng: return await interaction.response.send_message(f"Bạn không có đủ {số_lượng} {item_emoji} {item_name} để tặng.", ephemeral=True)
        
        view = ConfirmGiftView(sender, người_nhận, item_key, số_lượng, item_name, item_emoji)
        
        message_content = f"{sender.mention}, bạn có chắc muốn tặng **{số_lượng} {item_emoji} {item_name}** cho {người_nhận.mention} không?"
        await interaction.response.send_message(message_content, view=view)
        view.message = await interaction.original_response() # Lưu lại tin nhắn để view có thể edit


async def setup(bot):
    await bot.add_cog(SocialCommands(bot))