# cogs/general_commands.py

import discord
from discord.ext import commands
import data_manager
import config
import season_manager

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping')
    async def ping(self, ctx):
        """Kiểm tra độ trễ của bot."""
        await ctx.send(f'Pong! Độ trễ: {round(self.bot.latency * 1000)}ms')

    @commands.command(name='register')
    async def register(self, ctx):
        """Đăng ký để bắt đầu chơi game nông trại."""
        if data_manager.initialize_player(ctx.author.id):
            await ctx.send(
                f'Chào mừng {ctx.author.mention} đến với nông trại! '
                f'Bạn đã nhận được {config.INITIAL_BALANCE} {config.CURRENCY_SYMBOL} và {config.INITIAL_PLOTS} ô đất để bắt đầu.'
            )
        else:
            await ctx.send(f'Bạn đã đăng ký rồi, {ctx.author.mention}!')

    @commands.command(name='season')
    async def season(self, ctx):
        """Kiểm tra mùa hiện tại trong game."""
        current_season = season_manager.get_current_season()
        season_name = current_season['display']
        season_emoji = current_season['emoji']
        
        embed = discord.Embed(
            title=f"Bây giờ là {season_name} {season_emoji}",
            description="Mỗi mùa trong game kéo dài 1 tuần (ngoài đời thực).\nCác loại cây trồng và vật nuôi có thể mua sẽ thay đổi theo mùa.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))