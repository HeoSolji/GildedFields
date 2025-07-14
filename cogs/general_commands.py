# cogs/general_commands.py

import discord
from discord.ext import commands
from discord import app_commands # <-- Thêm import này
import data_manager
import config
import season_manager

# Thay vì commands.Cog, ta có thể dùng nó như một class bình thường
# hoặc vẫn giữ Cog để dễ quản lý
class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Lệnh PING phiên bản Slash Command ---
    @app_commands.command(name="ping", description="Kiểm tra độ trễ của bot.")
    async def ping(self, interaction: discord.Interaction):
        # Dùng interaction.response.send_message thay vì ctx.send
        await interaction.response.send_message(f'Pong! Độ trễ: {round(self.bot.latency * 1000)}ms')

    # --- Lệnh REGISTER phiên bản Slash Command ---
    @app_commands.command(name="register", description="Đăng ký để bắt đầu chơi game nông trại.")
    async def register(self, interaction: discord.Interaction):
        # Dùng interaction.user thay vì ctx.author
        if data_manager.initialize_player(interaction.user.id):
            await interaction.response.send_message(
                f'Chào mừng {interaction.user.mention} đến với nông trại! '
                f'Bạn đã nhận được {config.INITIAL_BALANCE} {config.CURRENCY_SYMBOL} và {config.INITIAL_PLOTS} ô đất để bắt đầu.'
            )
        else:
            await interaction.response.send_message(f'Bạn đã đăng ký rồi, {interaction.user.mention}!')

    # --- Lệnh SEASON phiên bản Slash Command ---
    @app_commands.command(name="season", description="Kiểm tra mùa hiện tại trong game.")
    async def season(self, interaction: discord.Interaction):
        current_season = season_manager.get_current_season()
        season_name = current_season['display']
        season_emoji = current_season['emoji']
        
        embed = discord.Embed(
            title=f"Bây giờ là {season_name} {season_emoji}",
            description="Mỗi mùa trong game kéo dài 1 tuần (ngoài đời thực).\nCác loại cây trồng và vật nuôi có thể mua sẽ thay đổi theo mùa.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Hiển thị danh sách tất cả các lệnh có sẵn.")
    async def help(self, interaction: discord.Interaction):
        """Hiển thị bảng trợ giúp lệnh."""
        # Defer a réponse pour donner au bot un peu de temps pour rassembler les commandes
        await interaction.response.defer(ephemeral=True, thinking=True)

        embed = discord.Embed(
            title="Bảng Trợ Giúp Lệnh",
            description="Dưới đây là danh sách tất cả các lệnh bạn có thể sử dụng, được nhóm theo chức năng.",
            color=discord.Color.blurple()
        )

        cog_map = {
            "Farm": "Nông Trại 🧑‍🌾",
            "AnimalCommands": "Chăn Nuôi 🐔",
            "Economy": "Kinh Tế 💰",
            "CraftingCommands": "Chế Tạo 🛠️",
            "Progression": "Tiến Trình 🏆",
            "SocialCommands": "Xã Hội 🤝",
            "General": "Chung ⚙️"
        }

        for cog_name, cog in self.bot.cogs.items():
            # Bỏ qua các lệnh của developer
            if cog_name == "Developer":
                continue

            command_list = cog.get_app_commands()
            if not command_list:
                continue

            # Chuẩn bị danh sách lệnh cho cog này
            command_details = []
            for command in command_list:
                # Xử lý nhóm lệnh (ví dụ /farm view, /farm upgrade)
                if isinstance(command, app_commands.Group):
                    sub_commands = [f"`{sub.name}`" for sub in command.commands]
                    detail_str = f"**`/{command.name}`**: {command.description} (Lệnh con: {', '.join(sub_commands)})"
                    command_details.append(detail_str)
                else:
                    command_details.append(f"**`/{command.name}`**: {command.description}")

            if command_details:
                # Lấy tên hiển thị của cog từ map, nếu không có thì dùng tên gốc
                display_name = cog_map.get(cog_name, cog_name)
                embed.add_field(name=f"--- {display_name} ---", value="\n".join(command_details), inline=False)
        
        # Dùng followup vì đã defer
        await interaction.followup.send(embed=embed)

async def setup(bot):
    # Thêm Cog và đồng bộ các lệnh trong Cog này
    await bot.add_cog(General(bot))