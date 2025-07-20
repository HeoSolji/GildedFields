# cogs/exploration_commands.py

import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import data_manager, config

class ExplorationCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="explore", description="Ra khơi tìm kiếm những vùng đất mới và kho báu!")
    @app_commands.checks.cooldown(1, config.EXPLORATION_CONFIG['cooldown'], key=lambda i: i.user.id)
    async def explore(self, interaction: discord.Interaction):
        try:
            user_data = data_manager.get_player_data(interaction.user.id)
            if not user_data: return await interaction.response.send_message("Bạn cần `/register` trước!", ephemeral=True)

            cost = config.EXPLORATION_CONFIG['cost']
            if user_data['balance'] < cost:
                return await interaction.response.send_message(f"Bạn không đủ tiền để ra khơi! Cần {cost} {config.CURRENCY_SYMBOL}.", ephemeral=True)

            user_data['balance'] -= cost
            await interaction.response.send_message(f"Bạn đã chi {cost} {config.CURRENCY_SYMBOL} để chuẩn bị cho một chuyến thám hiểm. Thuyền đang ra khơi...")


            # Quay số may mắn
            roll = random.random()
            rewards = config.EXPLORATION_CONFIG['rewards']
            
            embed = discord.Embed(title=f"Kết quả chuyến thám hiểm của {interaction.user.name}", color=discord.Color.blue())

            if roll < rewards['nothing_chance']:
                embed.description = "Sau nhiều ngày lênh đênh trên biển, đoàn thám hiểm của bạn quay về tay trắng. Chúc may mắn lần sau!"
            elif roll < rewards['nothing_chance'] + rewards['money_chance']:
                money_found = random.randint(rewards['min_money'], rewards['max_money'])
                user_data['balance'] += money_found
                embed.description = f"Trong một hang động ven biển, bạn đã tìm thấy một rương kho báu nhỏ chứa **{money_found} {config.CURRENCY_SYMBOL}**!"
                embed.color = discord.Color.gold()
            else:
                mystery_seeds = [crop_id for crop_id, crop_info in config.CROPS.items() if crop_info.get('seed_price', -1) == 0]
                if not mystery_seeds:
                    embed.description = "Bạn đã tìm thấy một hòn đảo hoang, nhưng không có gì quý giá."
                else:
                    found_seed_id = random.choice(mystery_seeds)
                    crop_info = config.CROPS[found_seed_id]
                    seed_key = f"seed_{found_seed_id}"
                    user_data['inventory'].setdefault(seed_key, {})['0'] = user_data['inventory'].setdefault(seed_key, {}).get('0', 0) + 1
                    embed.description = (f"Trên một hòn đảo bí ẩn, bạn đã tìm thấy một loại hạt giống cổ xưa chưa từng thấy!\n\n"
                                         f"Bạn nhận được: 1 {crop_info['emoji']} **Hạt {crop_info['display_name']}**")
                    embed.color = discord.Color.purple()

            await asyncio.sleep(3)
            await interaction.followup.send(embed=embed) 
            data_manager.save_player_data()
        
        except Exception as e:
            print(f"Lỗi trong lệnh /explore: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("Đã có lỗi xảy ra.", ephemeral=True)
            else:
                await interaction.followup.send("Đã có lỗi xảy ra.", ephemeral=True)

    @explore.error
    async def on_explore_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(f"Đoàn thám hiểm của bạn cần nghỉ ngơi! Vui lòng thử lại sau **{round(error.retry_after / 3600, 1)} giờ**.", ephemeral=True)
        else:
            print(f"Error in /explore command: {error}")
            if not interaction.response.is_done():
                await interaction.response.send_message("Đã có lỗi xảy ra.", ephemeral=True)
async def setup(bot):
    await bot.add_cog(ExplorationCommands(bot))