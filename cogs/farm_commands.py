# cogs/farm_commands.py

import discord
from discord.ext import commands
from discord import app_commands
import time
import datetime
import data_manager
import config
import season_manager
import random
import achievement_manager
from utils import determine_quality

# --- CLASS VIEW ĐỂ CHỨA NÚT BẤM (Giữ nguyên) ---
class FarmView(discord.ui.View):
    def __init__(self, user_id, timeout=180):
        super().__init__(timeout=timeout)
        self.user_id = user_id

    @discord.ui.button(label="Xem thời gian", style=discord.ButtonStyle.secondary, emoji="⏰")
    async def show_times(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Đây không phải nông trại của bạn!", ephemeral=True)
            return
        user_data = data_manager.get_player_data(self.user_id)
        if not user_data:
            await interaction.response.send_message("Không tìm thấy dữ liệu của bạn.", ephemeral=True)
            return
        farm_plots = user_data["farm"]["plots"]
        current_time = time.time()
        growing_crops_details = []
        sorted_plots = sorted(farm_plots.items(), key=lambda item: (int(item[0].split('_')[0]), int(item[0].split('_')[1])))
        for plot_key, plot_data in sorted_plots:
            if plot_data and current_time < plot_data["ready_time"]:
                crop_info = config.CROPS.get(plot_data["crop"])
                if not crop_info: continue
                time_left_seconds = plot_data["ready_time"] - current_time
                td = datetime.timedelta(seconds=int(time_left_seconds))
                r, c = map(int, plot_key.split('_'))
                growing_crops_details.append(f"**Ô ({r+1},{c+1})** {crop_info['emoji']}: Còn lại `{str(td)}`")
        content = "\n".join(growing_crops_details) if growing_crops_details else "Bạn không có cây nào đang lớn cả!"
        await interaction.response.send_message(content, ephemeral=True)


class Farm(commands.Cog):
    # Định nghĩa một nhóm lệnh cha cho /farm
    farm = app_commands.Group(name="farm", description="Các lệnh liên quan đến nông trại của bạn.")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_plantable_seeds(self, user_data):
        plantable_seeds = []
        inventory = user_data.get("inventory", {})
        for item_key in sorted(inventory.keys()):
            if item_key.startswith("seed_") and inventory.get(item_key, {}).get("0", 0) > 0:
                plantable_seeds.append(item_key)
        return plantable_seeds

    async def check_for_level_up(self, interaction: discord.Interaction, user_data):
        level = user_data.get('level', 1)
        xp = user_data.get('xp', 0)
        user_data['level'], user_data['xp'] = level, xp
        xp_needed = config.get_xp_for_level(level)
        while xp >= xp_needed:
            user_data['level'] += 1
            user_data['xp'] -= xp_needed
            user_data['balance'] += config.REWARD_PER_LEVEL_UP
            level, xp = user_data['level'], user_data['xp']
            xp_needed = config.get_xp_for_level(level)
            msg = (f"🎉 **CHÚC MỪNG** {interaction.user.mention}! Bạn đã lên **Cấp {level}**! "
                   f"Bạn nhận được {config.REWARD_PER_LEVEL_UP} {config.CURRENCY_SYMBOL} tiền thưởng.")
            if interaction.response.is_done(): await interaction.followup.send(msg)
            else: await interaction.channel.send(msg)
            await achievement_manager.check_achievements(interaction, user_data, "level")


    # --- LỆNH CON CỦA NHÓM /FARM ---
    @farm.command(name="view", description="Xem nông trại của bạn hoặc của người khác.")
    @app_commands.describe(member="Người bạn muốn xem nông trại.")
    async def farm_view(self, interaction: discord.Interaction, member: discord.Member = None):
        try:
            await interaction.response.defer()

            target_user = member or interaction.user
            user_data = data_manager.get_player_data(target_user.id)
            if not user_data: 
                return await interaction.followup.send(f"Người chơi {target_user.mention} chưa đăng ký game!")
            
            farm_size = user_data["farm"]["size"]
            plots = user_data["farm"]["plots"]
            current_time = time.time()
            
            current_season = season_manager.get_current_season()['name']
            empty_plot_emoji = config.PLOT_FROZEN_EMOJI if current_season == 'winter' else config.PLOT_EMPTY_EMOJI
            
            grid_rows = []
            companion_rows_info = []

            for r in range(farm_size):
                row_emojis = []
                # Kiểm tra thông tin xen canh cho cả hàng
                first_plot_in_row = plots.get(f"{r}_0")
                if first_plot_in_row and first_plot_in_row.get('companion_bonus_applied'):
                    crop_info = config.CROPS.get(first_plot_in_row.get("crop"))
                    if crop_info:
                        companion_rows_info.append(f"Hàng {r+1} ({crop_info['display_name']})")

                # Vòng lặp để xây dựng hiển thị cho hàng
                for c in range(farm_size):
                    plot_data = plots.get(f"{r}_{c}")

                    # --- CẤU TRÚC IF/ELIF/ELSE ĐÚNG ---
                    if not plot_data:
                        row_emojis.append(empty_plot_emoji)
                    else:
                        crop_info = config.CROPS.get(plot_data.get("crop"))
                        if not crop_info:
                            row_emojis.append("❓")
                        else:
                            grow_time = crop_info.get("grow_time", float('inf'))
                            plant_time = plot_data.get("plant_time", current_time)
                            progress = (current_time - plant_time) / grow_time if grow_time > 0 else 1

                            if progress >= 1:
                                row_emojis.append(crop_info["emoji"])
                            elif progress >= 0.4:
                                row_emojis.append(config.SAPLING_EMOJI)
                            else:
                                row_emojis.append(config.SEEDLING_EMOJI)
                
                grid_rows.append(" ".join(row_emojis))
            
            embed = discord.Embed(title=f"Nông trại của {target_user.name} ({farm_size}x{farm_size})", description="\n".join(grid_rows), color=discord.Color.dark_green())
            legend = (f"{config.SEEDLING_EMOJI}: Mầm | {config.SAPLING_EMOJI}: Cây non | 🌾🌽...: Sẵn sàng thu hoạch")
            embed.add_field(name="Chú thích", value=legend, inline=False)

            if companion_rows_info:
                bonus_text = f"Các hàng sau đang được tăng trưởng nhanh hơn: **{', '.join(companion_rows_info)}**"
                embed.add_field(name=f"{config.COMPANION_BONUS_EMOJI} Hiệu ứng Xen canh", value=bonus_text, inline=False)

            if target_user == interaction.user:
                await interaction.followup.send(embed=embed, view=FarmView(user_id=interaction.user.id))
            else:
                await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Lỗi nghiêm trọng trong lệnh /farm view: {e}")
            import traceback
            traceback.print_exc()
            if not interaction.response.is_done():
                await interaction.response.send_message("Rất tiếc, đã có lỗi xảy ra khi xem nông trại.", ephemeral=True)
            else:
                await interaction.followup.send("Rất tiếc, đã có lỗi xảy ra khi xem nông trại.", ephemeral=True)


    @farm.command(name="upgrade", description="Nâng cấp kích thước nông trại của bạn.")
    async def farm_upgrade(self, interaction: discord.Interaction):
        # ... (Nội dung hàm này giữ nguyên như phiên bản có try-except)
        try:
            user_data = data_manager.get_player_data(interaction.user.id)
            if not user_data: return await interaction.response.send_message("Bạn chưa đăng ký!", ephemeral=True)
            current_size = user_data.get('farm', {}).get('size', config.FARM_GRID_SIZE)
            if current_size >= config.MAX_FARM_SIZE: return await interaction.response.send_message("Nông trại của bạn đã đạt kích thước tối đa!", ephemeral=True)
            next_size = current_size + 1
            upgrade_info = config.FARM_UPGRADES.get(next_size)
            if not upgrade_info: return await interaction.response.send_message("Không có thông tin nâng cấp.", ephemeral=True)
            if user_data.get('level', 1) < upgrade_info['level_required']: return await interaction.response.send_message(f"Bạn cần đạt **Cấp {upgrade_info['level_required']}** để nâng cấp.", ephemeral=True)
            if user_data.get('balance', 0) < upgrade_info['cost']: return await interaction.response.send_message(f"Bạn không đủ tiền! Cần {upgrade_info['cost']} {config.CURRENCY_SYMBOL}.", ephemeral=True)
            user_data['balance'] -= upgrade_info['cost']
            user_data['farm']['size'] = next_size
            for r in range(next_size):
                for c in range(next_size):
                    if f"{r}_{c}" not in user_data['farm']['plots']: user_data['farm']['plots'][f"{r}_{c}"] = None
            data_manager.save_player_data()
            await achievement_manager.check_achievements(interaction, user_data, "farm_size")
            await interaction.response.send_message(f"🎉 **Chúc mừng!** Bạn đã nâng cấp nông trại lên kích thước **{next_size}x{next_size}**!")
        except Exception as e:
            print(f"Lỗi trong lệnh /farm upgrade: {e}")
            await interaction.response.send_message("Có lỗi xảy ra khi nâng cấp.", ephemeral=True)

    # --- CÁC LỆNH ĐỘC LẬP KHÁC ---
    @app_commands.command(name="seeds", description="Xem danh sách các loại hạt giống bạn có thể trồng.")
    async def seeds(self, interaction: discord.Interaction):
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return await interaction.response.send_message('Bạn chưa đăng ký!', ephemeral=True)
        plantable_seeds = self._get_plantable_seeds(user_data)
        if not plantable_seeds: return await interaction.response.send_message("Bạn không có hạt giống nào. Dùng `/shop` để mua nhé.")
        
        embed = discord.Embed(title=f"Túi hạt giống của {interaction.user.name}", color=discord.Color.dark_green())
        lines = []
        for index, seed_key in enumerate(plantable_seeds):
            quantity = user_data["inventory"].get(seed_key, {}).get("0", 0)
            crop_id = seed_key.split('_', 1)[1]
            crop_info = config.CROPS.get(crop_id)
            if crop_info:
                lines.append(f"**{index + 1}.** {crop_info['emoji']} **Hạt {crop_info['display_name']}**: `{quantity}`")
        
        embed.description = "\n".join(lines)
        embed.set_footer(text="Dùng /plant [số] [lượng] để trồng")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="plant", description="Trồng hạt giống từ túi hạt giống của bạn.")
    @app_commands.describe(số_thứ_tự="Số thứ tự của hạt giống trong /seeds.", số_lượng="Số lượng bạn muốn trồng.")
    async def plant(self, interaction: discord.Interaction, số_thứ_tự: int, số_lượng: int = 1):
        try:
            user_data = data_manager.get_player_data(interaction.user.id)
            if not user_data: return await interaction.response.send_message('Bạn chưa đăng ký!', ephemeral=True)
            if số_lượng <= 0: return await interaction.response.send_message("Số lượng phải lớn hơn 0.", ephemeral=True)
            
            plantable_seeds = self._get_plantable_seeds(user_data)
            index = số_thứ_tự - 1
            if not (0 <= index < len(plantable_seeds)): return await interaction.response.send_message(f"STT `{số_thứ_tự}` không hợp lệ.", ephemeral=True)
            
            seed_key = plantable_seeds[index]
            crop_id = seed_key.split('_', 1)[1]
            crop_info = config.CROPS[crop_id]
            current_season = season_manager.get_current_season()['name']
            if current_season not in crop_info['seasons']: return await interaction.response.send_message(f"Không thể trồng {crop_info['display_name']} trong mùa này!", ephemeral=True)

            seeds_owned = user_data.get('inventory', {}).get(seed_key, {}).get('0', 0)
            if seeds_owned < số_lượng: return await interaction.response.send_message(f"Bạn không có đủ {số_lượng} hạt {crop_info['display_name']}.", ephemeral=True)

            empty_plots = [key for key, value in user_data['farm']['plots'].items() if value is None]
            if len(empty_plots) < số_lượng: return await interaction.response.send_message("Không đủ ô đất trống!", ephemeral=True)

            planted_count = 0
            for i in range(min(số_lượng, len(empty_plots))):
                quality = determine_quality()
                plot_key = sorted(empty_plots, key=lambda x: (int(x.split('_')[0]), int(x.split('_')[1])))[i]
                user_data['farm']['plots'][plot_key] = {"crop": crop_id, "plant_time": time.time(), "ready_time": time.time() + crop_info["grow_time"], "quality": quality}
                
                # SỬA LỖI: Trừ và dọn dẹp kho đồ một cách an toàn
                user_data['inventory'][seed_key]['0'] -= 1
                if user_data['inventory'][seed_key]['0'] <= 0:
                    del user_data['inventory'][seed_key]['0']
                if not user_data['inventory'][seed_key]:
                    del user_data['inventory'][seed_key]
                
                planted_count += 1
            
            user_data['farm']['notification_sent'] = False
            data_manager.save_player_data()
            await interaction.response.send_message(f"Đã trồng thành công {planted_count} {crop_info['emoji']} {crop_info['display_name']}.")
        except Exception as e:
            print(f"Lỗi trong lệnh /plant: {e}")
            await interaction.response.send_message("Có lỗi xảy ra khi trồng cây.", ephemeral=True)

    @app_commands.command(name="harvest", description="Thu hoạch tất cả cây trồng đã sẵn sàng.")
    async def harvest(self, interaction: discord.Interaction):
        """Phiên bản mới với logic 'thu hoạch bội thu'."""
        try:
            user_data = data_manager.get_player_data(interaction.user.id)
            if not user_data: return await interaction.response.send_message('Bạn chưa đăng ký!', ephemeral=True)

            farm_plots = user_data['farm']['plots']
            current_time = time.time()
            harvested_items = {}
            plots_to_clear = []

            for plot_key, plot_data in farm_plots.items():
                if plot_data and current_time >= plot_data.get('ready_time', float('inf')):
                    crop_id = plot_data.get('crop')
                    if not (crop_id and crop_id in config.CROPS):
                        plots_to_clear.append(plot_key)
                        continue

                    # --- LOGIC MỚI: KIỂM TRA TỈ LỆ KHỔNG LỒ KHI THU HOẠCH ---
                    final_quality = plot_data.get('quality', 0)
                    yield_amount = 1
                    
                    if crop_id in config.GIANT_CROP_CANDIDATES and random.random() < config.GIANT_CROP_CHANCE:
                        final_quality = 5 # Cấp sao 5 cho cây khổng lồ
                    
                    quality_str = str(final_quality)
                    # ---------------------------------------------------------

                    harvested_items.setdefault(crop_id, {})[quality_str] = harvested_items.setdefault(crop_id, {}).get(quality_str, 0) + yield_amount
                    plots_to_clear.append(plot_key)

            if not plots_to_clear: return await interaction.response.send_message("Không có cây nào sẵn sàng để thu hoạch.")
            
            # Phản hồi ban đầu để người dùng không phải chờ
            await interaction.response.send_message("Đang tiến hành thu hoạch...")

            harvest_summary = []
            total_xp_gained = 0
            if harvested_items:
                for crop_id, qualities in harvested_items.items():
                    inventory_key = f"harvest_{crop_id}"
                    user_data['inventory'].setdefault(inventory_key, {})
                    for quality_str, quantity in qualities.items():
                        user_data['inventory'][inventory_key][quality_str] = user_data['inventory'][inventory_key].get(quality_str, 0) + quantity
                        star_emoji = config.STAR_EMOJIS.get(int(quality_str), "👑")
                        harvest_summary.append(f"{quantity} {config.CROPS[crop_id]['emoji']}{star_emoji}")
                        total_xp_gained += config.XP_PER_CROP.get(crop_id, 0) * quantity
            
            for plot_key in plots_to_clear: farm_plots[plot_key] = None
            user_data['farm']['notification_sent'] = True
            
            if harvest_summary:
                await interaction.followup.send(f"{interaction.user.mention}, bạn đã thu hoạch thành công: {', '.join(harvest_summary)}.")
            else:
                 await interaction.followup.send("Đã dọn dẹp một số cây trồng không hợp lệ khỏi nông trại.")

            if total_xp_gained > 0:
                user_data['xp'] = user_data.get('xp', 0) + total_xp_gained
                await interaction.followup.send(f"Bạn nhận được **{total_xp_gained} XP**!")
                await self.check_for_level_up(interaction, user_data)
            
            total_harvested_amount = 0
            unique_harvested_ids = []
            for crop_id, qualities in harvested_items.items():
                unique_harvested_ids.append(crop_id)
                for quality, quantity in qualities.items():
                    total_harvested_amount += quantity
                    if int(quality) == 5: # Cây khổng lồ
                        await achievement_manager.check_achievements(interaction, user_data, "harvest_quality", quality=5, amount=quantity)
            
            await achievement_manager.check_achievements(interaction, user_data, "harvest_total", amount=total_harvested_amount)
            for crop_id in unique_harvested_ids:
                 await achievement_manager.check_achievements(interaction, user_data, "collection", category="harvest", event_id=crop_id)

            await achievement_manager.check_achievements(interaction, user_data, "harvest", harvested_items=harvested_items)
            data_manager.save_player_data()
        except Exception as e:
            print(f"Lỗi trong lệnh /harvest: {e}")
            if interaction.response.is_done():
                await interaction.followup.send("Có lỗi xảy ra khi thu hoạch.", ephemeral=True)
            else:
                await interaction.response.send_message("Có lỗi xảy ra khi thu hoạch.", ephemeral=True)
async def setup(bot):
    # Chỉ cần thêm Cog, bot sẽ tự động đăng ký các lệnh app_command trong đó
    await bot.add_cog(Farm(bot))