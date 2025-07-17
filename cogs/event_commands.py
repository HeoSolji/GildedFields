# cogs/event_commands.py

import discord
from discord.ext import commands
from discord import app_commands
import random
import data_manager
import config

class EventCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Tạo một nhóm lệnh cha cho /event
    event = app_commands.Group(name="event", description="Các lệnh để quản lý sự kiện trong game (chỉ dành cho chủ bot).")

    @event.command(name="storm", description="Tạo ra một cơn bão phá hủy một phần cây trồng.")
    @commands.is_owner() # <-- SỬA LỖI: Dùng decorator đúng từ 'commands'
    @app_commands.describe(damage_percentage="Tỉ lệ cây trồng bị phá hủy (ví dụ: 20 cho 20%).")
    async def event_storm(self, interaction: discord.Interaction, damage_percentage: app_commands.Range[int, 1, 100]):
        await interaction.response.send_message(f"⏳ Đang thực thi sự kiện **Cơn Bão** với tỉ lệ phá hủy {damage_percentage}%...", ephemeral=True)

        # Gửi thông báo sự kiện tới kênh chung
        announcement_channel_id = config.MARKET_EVENT_CHANNEL_ID
        if announcement_channel_id:
            try:
                channel = await self.bot.fetch_channel(announcement_channel_id)
                embed = discord.Embed(
                    title="🌪️ TIN KHẨN CẤP: BÃO ĐỔ BỘ!",
                    description="Một cơn bão bất ngờ đang quét qua khu vực! Một số cây trồng có thể đã bị hư hại. Hãy kiểm tra lại nông trại của bạn!",
                    color=discord.Color.dark_grey()
                )
                await channel.send(embed=embed)
            except Exception as e:
                print(f"Không thể gửi thông báo sự kiện bão: {e}")

        # Logic phá hủy cây trồng
        all_players_data = data_manager.GAME_DATA
        total_destroyed_plots = 0
        affected_farms = 0

        for user_id, user_data in all_players_data.items():
            farm_plots = user_data.get('farm', {}).get('plots', {})
            
            planted_plots_keys = [key for key, plot in farm_plots.items() if plot is not None and "crop" in plot]
            
            if not planted_plots_keys:
                continue

            num_to_destroy = round(len(planted_plots_keys) * (damage_percentage / 100))
            if num_to_destroy == 0 and len(planted_plots_keys) > 0 and damage_percentage > 0:
                num_to_destroy = 1

            if num_to_destroy > 0:
                plots_to_destroy = random.sample(planted_plots_keys, k=min(num_to_destroy, len(planted_plots_keys)))

                if plots_to_destroy:
                    affected_farms += 1
                    for plot_key in plots_to_destroy:
                        farm_plots[plot_key] = None
                        total_destroyed_plots += 1
        
        data_manager.save_player_data()

        await interaction.followup.send(f"✅ Sự kiện **Cơn Bão** đã kết thúc! Tổng cộng **{total_destroyed_plots}** cây trồng trên **{affected_farms}** nông trại đã bị phá hủy.", ephemeral=True)

    # Bắt lỗi nếu người dùng không phải chủ bot
    @event_storm.error
    async def on_storm_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        # SỬA LỖI: Bắt đúng loại lỗi CheckFailure
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
        else:
            await interaction.response.send_message("Đã có lỗi xảy ra.", ephemeral=True)
            print(error)


async def setup(bot):
    await bot.add_cog(EventCommands(bot))