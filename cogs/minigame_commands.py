# cogs/minigame_commands.py

import discord
from discord.ext import commands
from discord import app_commands
import random, asyncio
import data_manager, config, utils

class FishView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=3.0) # Người chơi có 3 giây để phản ứng
        self.author = author
        self.caught = False
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Đây không phải cần câu của bạn!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        # Hàm này được gọi khi 3 giây kết thúc mà người dùng chưa bấm nút
        if not self.caught and self.message:
            for item in self.children:
                item.disabled = True
            try:
                # Cố gắng chỉnh sửa tin nhắn để thông báo cá đã chạy mất
                await self.message.edit(content="Ôi không, cá đã chạy mất rồi! 🎣", view=self)
            except discord.NotFound:
                # Bỏ qua nếu tin nhắn đã bị xóa
                pass
            except Exception as e:
                # In ra lỗi nếu có vấn đề khác, nhưng không làm bot crash
                print(f"Lỗi khi xử lý timeout của FishView: {e}")

    @discord.ui.button(label="Kéo lên!", style=discord.ButtonStyle.primary, emoji="❗")
    async def reel_in(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.caught = True
        self.stop()

        fish_list = list(config.FISH.keys())
        rarity_weights = [config.FISH[f]['rarity'] for f in fish_list]
        chosen_fish_id = random.choices(fish_list, weights=rarity_weights, k=1)[0]
        fish_info = config.FISH[chosen_fish_id]

        user_data = data_manager.get_player_data(self.author.id)
        inventory_key = f"fish_{chosen_fish_id}"
        quality = utils.determine_quality()
        quality_str = str(quality)
        
        user_data['inventory'].setdefault(inventory_key, {})[quality_str] = user_data['inventory'].setdefault(inventory_key, {}).get(quality_str, 0) + 1
        data_manager.save_player_data()
        
        star_emoji = config.STAR_EMOJIS.get(quality, "")
        
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(content=f"Chúc mừng! Bạn đã câu được một con **{fish_info['display_name']}{star_emoji}** {fish_info['emoji']}!", view=self)

class MinigameCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="fish", description="Thử vận may câu cá!")
    @app_commands.checks.cooldown(1, config.FISHING_COOLDOWN, key=lambda i: i.user.id)
    async def fish(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_message("Bạn đã quăng câu và đang kiên nhẫn chờ đợi... 🎣")
            message = await interaction.original_response()
            await asyncio.sleep(random.uniform(2.0, 7.0))
            view = FishView(interaction.user)
            await message.edit(content="**CẮN CÂU!!!**", view=view)
            view.message = message
        except Exception as e:
            print(f"Lỗi trong lệnh /fish: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("Đã có lỗi xảy ra.", ephemeral=True)

    @fish.error
    async def on_fish_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(f"Cần câu cần được nghỉ ngơi! Vui lòng thử lại sau **{round(error.retry_after, 1)} giây**.", ephemeral=True)
        else:
            print(f"Error in /fish command: {error}")
            if not interaction.response.is_done():
                await interaction.response.send_message("Đã có lỗi xảy ra.", ephemeral=True)
            else:
                await interaction.followup.send("Đã có lỗi xảy ra.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(MinigameCommands(bot))