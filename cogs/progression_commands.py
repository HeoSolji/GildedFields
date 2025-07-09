# cogs/progression_commands.py

import discord
from discord.ext import commands
import data_manager
import config

class Progression(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='profile', aliases=['info', 'prof'])
    async def profile(self, ctx, member: discord.Member = None):
        """Xem hồ sơ nông trại của bạn hoặc của người khác."""
        target_user = member or ctx.author
        user_data = data_manager.get_player_data(target_user.id)

        if not user_data:
            return await ctx.send(f"Người chơi {target_user.mention} chưa đăng ký game!")

        level = user_data.get('level', 1)
        xp = user_data.get('xp', 0)
        xp_needed = config.get_xp_for_level(level)
        
        # Tạo thanh tiến trình XP
        progress = int((xp / xp_needed) * 20) # 20 là chiều dài của thanh
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
        
        await ctx.send(embed=embed)

    @commands.command(name='leaderboard', aliases=['lb', 'top'])
    async def leaderboard(self, ctx):
        """Hiển thị bảng xếp hạng những người chơi giàu nhất."""
        all_players = data_manager.GAME_DATA
        if not all_players:
            return await ctx.send("Chưa có người chơi nào để xếp hạng!")
            
        # Sắp xếp người chơi theo số tiền giảm dần
        sorted_players = sorted(
            all_players.items(), 
            key=lambda item: item[1].get('balance', 0), 
            reverse=True
        )

        embed = discord.Embed(title="🏆 Bảng Xếp Hạng Nông Dân Giàu Có 🏆", color=discord.Color.gold())
        
        description = []
        for i, (user_id, data) in enumerate(sorted_players[:10]): # Lấy top 10
            try:
                user = await self.bot.fetch_user(int(user_id))
                user_name = user.name
            except discord.NotFound:
                user_name = f"Người chơi (ID: {user_id})"
            
            rank_emoji = ["🥇", "🥈", "🥉"]
            if i < 3:
                rank = rank_emoji[i]
            else:
                rank = f"**#{i+1}**"

            description.append(f"{rank} **{user_name}**: {data.get('balance', 0)} {config.CURRENCY_SYMBOL}")
        
        embed.description = "\n".join(description)
        await ctx.send(embed=embed)

    @commands.command(name='achievements', aliases=['ac', 'thanh_tuu'])
    async def achievements(self, ctx):
        """Xem danh sách thành tựu và tiến độ của bạn."""
        user_data = data_manager.get_player_data(ctx.author.id)
        if not user_data: return await ctx.send("Bạn chưa đăng ký!")

        user_achievements = user_data.get('achievements', {"unlocked": [], "progress": {}})
        embed = discord.Embed(title=f"Bảng thành tựu của {ctx.author.name}", color=discord.Color.dark_gold())
        
        unlocked_lines = []
        locked_lines = []

        for ach_id, ach_info in config.ACHIEVEMENTS.items():
            if ach_id in user_achievements['unlocked']:
                unlocked_lines.append(f"✅ {ach_info['emoji']} **{ach_info['display_name']}**")
            else:
                progress = user_achievements['progress'].get(ach_id, 0)
                target = ach_info['target_amount']
                # Với balance, tiến độ là số tiền hiện tại
                if ach_info['type'] == 'balance':
                    progress = user_data.get('balance', 0)
                
                locked_lines.append(f"❌ {ach_info['emoji']} **{ach_info['display_name']}** - _{ach_info['description']}_ ({progress}/{target})")
        
        if unlocked_lines:
            embed.add_field(name="Đã mở khóa", value="\n".join(unlocked_lines), inline=False)
        if locked_lines:
            embed.add_field(name="Chưa mở khóa", value="\n".join(locked_lines), inline=False)
        
        await ctx.send(embed=embed)
async def setup(bot):
    await bot.add_cog(Progression(bot))