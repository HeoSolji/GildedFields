# cogs/developer_commands.py

import discord
from discord.ext import commands
from discord import app_commands
import os, time
import data_manager, config
import achievement_manager

import importlib
import quest_manager

class Developer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- LỆNH PREFIX CŨ VẪN GIỮ LẠI ĐỂ TIỆN SỬ DỤNG ---
    @commands.command(name='reload')
    @commands.is_owner()
    async def reload_cogs(self, ctx: commands.Context, *, cog: str):
        """Tải lại một cog và các module phụ quan trọng."""
        try:
            # Luôn luôn buộc tải lại quest_manager để đảm bảo nó là mới nhất
            print("--- Bắt buộc tải lại module quest_manager... ---")
            importlib.reload(quest_manager)
            print("-> Đã tải lại quest_manager thành công.")
            
            if cog.lower() == 'all':
                reloaded_cogs = []
                for filename in os.listdir('./cogs'):
                    if filename.endswith('.py'):
                        await self.bot.reload_extension(f'cogs.{filename[:-3]}')
                        reloaded_cogs.append(f"`{filename[:-3]}`")
                await ctx.send(f"Đã tải lại thành công các cog: {', '.join(reloaded_cogs)}")
            else:
                await self.bot.reload_extension(f"cogs.{cog}")
                await ctx.send(f"Cog `{cog}` và module quest_manager đã được tải lại!")
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
    
    @dev.command(name="resetmachines", description="Reset tất cả máy móc của một người chơi về trạng thái 'rảnh rỗi'.")
    @app_commands.describe(member="Người chơi muốn reset (mặc định là bạn).")
    async def reset_machines(self, interaction: discord.Interaction, member: discord.Member = None):
        if not await self.bot.is_owner(interaction.user):
            return await interaction.response.send_message("Bạn không có quyền dùng lệnh này!", ephemeral=True)

        target_user = member or interaction.user
        user_data = data_manager.get_player_data(target_user.id)
        if not user_data:
            return await interaction.response.send_message(f"Người chơi {target_user.mention} chưa đăng ký.", ephemeral=True)
            
        if 'machines' in user_data and 'seed_maker' in user_data['machines']:
            for machine in user_data['machines']['seed_maker']:
                machine['state'] = 'idle'
                machine.pop('input_key', None)
                machine.pop('input_qty', None)
                machine.pop('finish_time', None)
            
            data_manager.save_player_data()
            await interaction.response.send_message(f"Đã reset tất cả Máy Tạo Hạt Giống của {target_user.mention} về trạng thái rảnh rỗi.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Không tìm thấy dữ liệu máy móc để reset cho {target_user.mention}.", ephemeral=True)

    @dev.command(name="addrep", description="Cộng điểm thân thiện cho một người chơi.")
    @app_commands.describe(npc="NPC bạn muốn tăng điểm thân thiện.", amount="Số điểm muốn cộng.", member="Người chơi muốn tác động.")
    @app_commands.choices(npc=[
        discord.app_commands.Choice(name=npc_info['name'], value=npc_id)
        for npc_id, npc_info in config.QUEST_NPCS.items()
    ])
    async def add_rep(self, interaction: discord.Interaction, npc: str, amount: int, member: discord.Member = None):
        if not await self.bot.is_owner(interaction.user):
            return await interaction.response.send_message("Bạn không có quyền dùng lệnh này!", ephemeral=True)

        target_user = member or interaction.user
        user_data = data_manager.get_player_data(target_user.id)
        if not user_data:
            return await interaction.response.send_message(f"Người chơi {target_user.mention} chưa đăng ký.", ephemeral=True)
            
        user_quests = user_data.setdefault('quests', {})
        reputation_data = user_quests.setdefault('reputation', {})
        
        # Cộng điểm
        current_rep = reputation_data.get(npc, 0)
        reputation_data[npc] = current_rep + amount
        
        # 1. Gọi hàm kiểm tra và nhận lại kết quả
        newly_unlocked = quest_manager.check_reputation_rewards(user_data, npc)
        
        # 2. Lưu dữ liệu ngay lập tức
        data_manager.save_player_data()
        
        # 3. Gửi tin nhắn xác nhận ban đầu
        await interaction.response.send_message(f"Đã cộng {amount} điểm thân thiện với '{config.QUEST_NPCS[npc]['name']}' cho {target_user.mention}. Tổng điểm: {reputation_data[npc]}", ephemeral=True)
        
        # 4. Gửi các tin nhắn thông báo phần thưởng (nếu có)
        for reward_info in newly_unlocked:
            npc_name = config.QUEST_NPCS.get(npc, {}).get('name', 'Một người bạn')
            embed = discord.Embed(color=discord.Color.green())
            
            if reward_info['type'] == 'recipe':
                recipe_name = config.RECIPES.get(reward_info['id'], {}).get('display_name', 'bí mật')
                embed.title=f"📬 Bạn có thư từ {npc_name}!"
                embed.description = f"\"_{reward_info['message']}_\"\n\nBạn đã học được công thức chế tạo **{recipe_name}**!"
            
            elif reward_info['type'] == 'gift':
                item_key = reward_info.get('item_key')
                item_type, item_id = item_key.split('_', 1)
                item_info = config.CROPS.get(item_id) if item_type == 'seed' else config.PRODUCTS.get(item_id)
                item_name = f"Hạt {item_info['display_name']}" if item_type == 'seed' else item_info['display_name']
                embed.title=f"🎁 Bạn có quà từ {npc_name}!"
                embed.description = f"\"_{reward_info['message']}_\"\n\nBạn nhận được **{reward_info['amount']} {item_info['emoji']} {item_name}**!"
            
            try:
                # Gửi DM đến người dùng được tác động
                await target_user.send(embed=embed)
            except discord.Forbidden:
                # Nếu không gửi được, báo ở kênh hiện tại
                await interaction.channel.send(f"{target_user.mention}, bạn có thư mới nhưng tôi không thể gửi tin nhắn riêng cho bạn!")

    @dev.command(name="resetquests", description="Reset toàn bộ dữ liệu nhiệm vụ và điểm thân thiện của người chơi.")
    @app_commands.describe(member="Người chơi muốn reset (mặc định là bạn).")
    async def reset_quests(self, interaction: discord.Interaction, member: discord.Member = None):
        if not await self.bot.is_owner(interaction.user):
            return await interaction.response.send_message("Bạn không có quyền dùng lệnh này!", ephemeral=True)

        target_user = member or interaction.user
        user_data = data_manager.get_player_data(target_user.id)
        if not user_data:
            return await interaction.response.send_message(f"Người chơi {target_user.mention} chưa đăng ký.", ephemeral=True)
            
        # Reset lại dictionary về trạng thái ban đầu
        user_data['quests'] = {
            "daily": [],
            "special": None,
            "last_updated": 0,
            "reputation": {"johnson": 0, "barry": 0},
            "unlocked_recipes": []
        }
        
        data_manager.save_player_data()
        await interaction.response.send_message(f"Đã reset toàn bộ dữ liệu nhiệm vụ và thân thiện của {target_user.mention}.", ephemeral=True)
async def setup(bot):
    await bot.add_cog(Developer(bot))