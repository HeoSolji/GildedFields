# cogs/progression_commands.py

import discord
from discord.ext import commands
from discord import app_commands # <-- Thêm import này
import data_manager
import config

class Progression(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="Xem hồ sơ nông trại của bạn hoặc của người khác.")
    @app_commands.describe(member="Người chơi bạn muốn xem hồ sơ. Bỏ trống để xem của chính bạn.")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        """Xem hồ sơ nông trại của bạn hoặc của người khác."""
        # Nếu không tag ai, target_user là người dùng lệnh. Ngược lại là người được tag.
        target_user = member or interaction.user
        user_data = data_manager.get_player_data(target_user.id)

        if not user_data:
            await interaction.response.send_message(f"Người chơi {target_user.mention} chưa đăng ký game!", ephemeral=True)
            return

        level = user_data.get('level', 1)
        xp = user_data.get('xp', 0)
        xp_needed = config.get_xp_for_level(level)
        
        progress = int((xp / xp_needed) * 20) if xp_needed > 0 else 20
        progress_bar = '█' * progress + '─' * (20 - progress)

        embed = discord.Embed(
            title=f"Hồ sơ của {target_user.name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.add_field(name="Cấp độ", value=f"```{level}```", inline=True)
        embed.add_field(name="Tiền", value=f"```{user_data['balance']} {config.CURRENCY_SYMBOL}```", inline=True)
        embed.add_field(
            name=f"Kinh nghiệm (XP)",
            value=f"`{xp} / {xp_needed}`\n`[{progress_bar}]`",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Hiển thị bảng xếp hạng những người chơi giàu nhất.")
    async def leaderboard(self, interaction: discord.Interaction):
        """Hiển thị bảng xếp hạng những người chơi giàu nhất."""
        all_players = data_manager.GAME_DATA
        if not all_players:
            await interaction.response.send_message("Chưa có người chơi nào để xếp hạng!")
            return
            
        sorted_players = sorted(
            all_players.items(), 
            key=lambda item: item[1].get('balance', 0), 
            reverse=True
        )

        embed = discord.Embed(title="🏆 Bảng Xếp Hạng Nông Dân Giàu Có 🏆", color=discord.Color.gold())
        
        description = []
        # Dùng interaction.guild.get_member để lấy thông tin trong server hiện tại
        for i, (user_id, data) in enumerate(sorted_players[:10]):
            user = interaction.guild.get_member(int(user_id))
            user_name = user.name if user else f"Người chơi (ID: {user_id})"
            
            rank_emoji = ["🥇", "🥈", "🥉"]
            rank = rank_emoji[i] if i < 3 else f"**#{i+1}**"

            description.append(f"{rank} **{user_name}**: {data.get('balance', 0)} {config.CURRENCY_SYMBOL}")
        
        embed.description = "\n".join(description)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Progression(bot))