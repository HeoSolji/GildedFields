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

    achievements_group = app_commands.Group(name="achievements", description="Xem các thành tựu của bạn.")

    @achievements_group.command(name="view", description="Xem tiến độ tất cả các thành tựu có thể đạt được.")
    async def achievements_view(self, interaction: discord.Interaction):
        """Xem danh sách thành tựu và tiến độ của bạn."""
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.response.send_message("Bạn chưa đăng ký!", ephemeral=True)

        user_achievements = user_data.get('achievements', {"unlocked": [], "progress": {}})
        embed = discord.Embed(title=f"Bảng thành tựu của {interaction.user.name}", color=discord.Color.dark_gold())
        
        unlocked_lines = []
        locked_lines = []

        for ach_id, ach_info in config.ACHIEVEMENTS.items():
            # Nếu đã mở khóa, luôn hiển thị
            if ach_id in user_achievements['unlocked']:
                unlocked_lines.append(f"✅ {ach_info['emoji']} **{ach_info['display_name']}** - _{ach_info['description']}_")
            
            # --- SỬA LỖI LOGIC TẠI ĐÂY ---
            # Nếu chưa mở khóa VÀ không phải là thành tựu ẩn, thì mới hiển thị
            elif not ach_info.get("hidden", False):
                progress = user_achievements['progress'].get(ach_id, 0)
                target = ach_info.get('target_amount', 0)

                # Xử lý các loại tiến độ khác nhau
                if ach_info['type'] == 'balance':
                    progress = user_data.get('balance', 0)
                elif ach_info['type'] == 'farm_size':
                    progress = user_data.get('farm', {}).get('size', 0)
                elif ach_info['type'] == 'collection':
                    progress = len(user_achievements['progress'].get(ach_id, []))
                
                locked_lines.append(f"❌ {ach_info['emoji']} **{ach_info['display_name']}** - ({progress}/{target})")
        
        if unlocked_lines:
            embed.add_field(name="Đã Mở Khóa", value="\n".join(unlocked_lines), inline=False)
        if locked_lines:
            embed.add_field(name="Chưa Mở Khóa", value="\n".join(locked_lines), inline=False)
        
        embed.set_footer(text="Một số thành tựu sẽ bị ẩn cho đến khi bạn mở khóa được chúng!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @achievements_group.command(name="unlocked", description="Hiển thị tủ cúp của bạn - những thành tựu đã đạt được.")
    async def achievements_unlocked(self, interaction: discord.Interaction):
        """Hiển thị các thành tựu đã mở khóa một cách đẹp mắt."""
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.response.send_message("Bạn chưa đăng ký!", ephemeral=True)
        
        unlocked_ids_list = user_data.get('achievements', {}).get('unlocked', [])
        
        # --- SUPER DEBUG ---
        print("\n--- [SUPER DEBUG] Bắt đầu /achievements unlocked ---")
        print(f"Dữ liệu gốc từ file data: {unlocked_ids_list}")
        print(f"Kiểu dữ liệu của nó là: {type(unlocked_ids_list)}")
        # ---------------------

        unique_unlocked_ids = set(unlocked_ids_list)
        
        # --- SUPER DEBUG ---
        print(f"Dữ liệu sau khi loại bỏ trùng lặp: {unique_unlocked_ids}")
        print(f"Số lượng thành tựu duy nhất: {len(unique_unlocked_ids)}")
        print("------------------------------------------------\n")
        # ---------------------
        
        embed = discord.Embed(title=f"🏆 Tủ Cúp của {interaction.user.name} 🏆", color=discord.Color.gold())

        if not unique_unlocked_ids:
            embed.description = "Bạn chưa mở khóa được thành tựu nào. Hãy tiếp tục cố gắng!"
        else:
            total_achievements = len(config.ACHIEVEMENTS)
            embed.description = f"Bạn đã mở khóa **{len(unique_unlocked_ids)}** trên tổng số **{total_achievements}** thành tựu!"
            
            for ach_id in unique_unlocked_ids:
                ach_info = config.ACHIEVEMENTS.get(ach_id)
                if ach_info:
                    embed.add_field(
                        name=f"{ach_info['emoji']} {ach_info['display_name']}",
                        value=f"_{ach_info['description']}_",
                        inline=True
                    )
        
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="reputation", description="Xem điểm thân thiện của bạn với các dân làng.")
    async def reputation(self, interaction: discord.Interaction):
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.response.send_message("Bạn chưa đăng ký!", ephemeral=True)

        reputation_data = user_data.get('quests', {}).get('reputation', {})
        embed = discord.Embed(title=f"❤️ Bảng Thân thiện của {interaction.user.name}", color=discord.Color.pink())
        
        if not reputation_data:
            embed.description = "Bạn chưa làm quen với ai cả."
        else:
            lines = []
            for npc_id, points in reputation_data.items():
                npc_info = config.QUEST_NPCS.get(npc_id, {})
                lines.append(f"**{npc_info.get('emoji', '')} {npc_info.get('name', '???')}**: {points} điểm")
            embed.description = "\n".join(lines)
        
        await interaction.response.send_message(embed=embed)
async def setup(bot):
    await bot.add_cog(Progression(bot))