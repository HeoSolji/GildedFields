# cogs/developer_commands.py

import discord
from discord.ext import commands
from discord import app_commands
import os, time
import data_manager, config
import achievement_manager

class Developer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- LỆNH PREFIX CŨ VẪN GIỮ LẠI ĐỂ TIỆN SỬ DỤNG ---
    @commands.command(name='reload')
    @commands.is_owner()
    async def reload_cogs(self, ctx: commands.Context, *, cog: str):
        try:
            if cog.lower() == 'all':
                reloaded_cogs = []
                for filename in os.listdir('./cogs'):
                    if filename.endswith('.py'):
                        await self.bot.reload_extension(f'cogs.{filename[:-3]}')
                        reloaded_cogs.append(f"`{filename[:-3]}`")
                await ctx.send(f"Đã tải lại thành công các cog: {', '.join(reloaded_cogs)}")
            else:
                await self.bot.reload_extension(f"cogs.{cog}")
                await ctx.send(f"Cog `{cog}` đã được tải lại!")
        except Exception as e:
            await ctx.send(f"Lỗi khi tải lại cog: {e}")

    @commands.command(name='sync')
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        fmt = await ctx.bot.tree.sync()
        await ctx.send(f"Đã đồng bộ {len(fmt)} lệnh / thành công trên toàn cục.")

    # --- NHÓM LỆNH /DEV MỚI DÀNH CHO ADMIN ---
    dev = app_commands.Group(name="dev", description="Các lệnh gian lận để test game.")

    @dev.command(name="addmoney", description="Cộng tiền cho một người chơi.")
    @app_commands.describe(amount="Số tiền muốn cộng (có thể là số âm).", member="Người chơi muốn cộng tiền (mặc định là bạn).")
    async def add_money(self, interaction: discord.Interaction, amount: int, member: discord.Member = None):
        if not await self.bot.is_owner(interaction.user):
            return await interaction.response.send_message("Bạn không có quyền dùng lệnh này!", ephemeral=True)
        
        target_user = member or interaction.user
        user_data = data_manager.get_player_data(target_user.id)
        if not user_data:
            return await interaction.response.send_message(f"Người chơi {target_user.mention} chưa đăng ký.", ephemeral=True)
        
        user_data['balance'] += amount

        await achievement_manager.check_achievements(interaction, user_data, "balance")

        data_manager.save_player_data()
        await interaction.response.send_message(f"Đã cộng {amount} {config.CURRENCY_SYMBOL} cho {target_user.mention}. Số dư mới: {user_data['balance']}", ephemeral=True)

    @dev.command(name="addxp", description="Cộng điểm kinh nghiệm (XP) cho một người chơi.")
    @app_commands.describe(amount="Số XP muốn cộng.", member="Người chơi muốn cộng XP (mặc định là bạn).")
    async def add_xp(self, interaction: discord.Interaction, amount: int, member: discord.Member = None):
        if not await self.bot.is_owner(interaction.user):
            return await interaction.response.send_message("Bạn không có quyền dùng lệnh này!", ephemeral=True)

        target_user = member or interaction.user
        user_data = data_manager.get_player_data(target_user.id)
        if not user_data:
            return await interaction.response.send_message(f"Người chơi {target_user.mention} chưa đăng ký.", ephemeral=True)
        
        user_data['xp'] = user_data.get('xp', 0) + amount
        await interaction.response.send_message(f"Đã cộng {amount} XP cho {target_user.mention}.", ephemeral=True)
        
        farm_cog = self.bot.get_cog('Farm')
        if farm_cog and hasattr(farm_cog, 'check_for_level_up'):
            await farm_cog.check_for_level_up(interaction, user_data)
        
        data_manager.save_player_data()

    @dev.command(name="grow", description="Làm cho tất cả cây trồng trong farm chín ngay lập tức.")
    @app_commands.describe(member="Nông trại của người chơi muốn tác động (mặc định là bạn).")
    async def grow(self, interaction: discord.Interaction, member: discord.Member = None):
        if not await self.bot.is_owner(interaction.user):
            return await interaction.response.send_message("Bạn không có quyền dùng lệnh này!", ephemeral=True)

        target_user = member or interaction.user
        user_data = data_manager.get_player_data(target_user.id)
        if not user_data:
            return await interaction.response.send_message(f"Người chơi {target_user.mention} chưa đăng ký.", ephemeral=True)
            
        for plot_data in user_data['farm']['plots'].values():
            if plot_data and "ready_time" in plot_data:
                plot_data['ready_time'] = time.time() - 1
        
        data_manager.save_player_data()
        await interaction.response.send_message(f"Đã làm chín toàn bộ cây trong nông trại của {target_user.mention}!", ephemeral=True)

    @dev.command(name="collectnow", description="Làm cho tất cả sản phẩm trong chuồng sẵn sàng thu hoạch.")
    @app_commands.describe(member="Chuồng nuôi của người chơi muốn tác động (mặc định là bạn).")
    async def collect_now(self, interaction: discord.Interaction, member: discord.Member = None):
        if not await self.bot.is_owner(interaction.user):
            return await interaction.response.send_message("Bạn không có quyền dùng lệnh này!", ephemeral=True)

        target_user = member or interaction.user
        user_data = data_manager.get_player_data(target_user.id)
        if not user_data:
            return await interaction.response.send_message(f"Người chơi {target_user.mention} chưa đăng ký.", ephemeral=True)

        for animal_id, ready_times in user_data['barn']['animals'].items():
            user_data['barn']['animals'][animal_id] = [time.time() - 1] * len(ready_times)

        data_manager.save_player_data()
        await interaction.response.send_message(f"Đã làm cho tất cả sản phẩm trong chuồng của {target_user.mention} sẵn sàng!", ephemeral=True)

    # @dev.command(name="resetcooldown", description="Xóa thời gian chờ của một lệnh cho bạn.")
    # @app_commands.describe(command="Tên lệnh bạn muốn xóa thời gian chờ (ví dụ: fish, explore).")
    # async def reset_cooldown(self, interaction: discord.Interaction, command: str):
    #     if not await self.bot.is_owner(interaction.user):
    #         return await interaction.response.send_message("Bạn không có quyền dùng lệnh này!", ephemeral=True)
            
    #     cmd = self.bot.tree.get_command(command)
    #     if not cmd:
    #         return await interaction.response.send_message(f"Không tìm thấy lệnh có tên `/{command}`.", ephemeral=True)
        
    #     if cmd._attr_cooldown:
    #         cmd._attr_cooldown.reset(interaction)
    #         await interaction.response.send_message(f"Đã xóa thời gian chờ của lệnh `/{command}` cho bạn.", ephemeral=True)
    #     else:
    #         await interaction.response.send_message(f"Lệnh `/{command}` không có thời gian chờ.", ephemeral=True)

    @dev.command(name="resetachievements", description="Xóa toàn bộ dữ liệu thành tựu của một người chơi.")
    @app_commands.describe(member="Người chơi muốn reset (mặc định là bạn).")
    async def reset_achievements(self, interaction: discord.Interaction, member: discord.Member = None):
        if not await self.bot.is_owner(interaction.user):
            return await interaction.response.send_message("Bạn không có quyền dùng lệnh này!", ephemeral=True)

        target_user = member or interaction.user
        user_data = data_manager.get_player_data(target_user.id)
        if not user_data:
            return await interaction.response.send_message(f"Người chơi {target_user.mention} chưa đăng ký.", ephemeral=True)
            
        # Reset lại dictionary thành tựu về trạng thái ban đầu
        user_data['achievements'] = {
            "unlocked": [],
            "progress": {}
        }
        
        data_manager.save_player_data()
        await interaction.response.send_message(f"Đã xóa sạch dữ liệu thành tựu của {target_user.mention}.", ephemeral=True)
async def setup(bot):
    await bot.add_cog(Developer(bot))