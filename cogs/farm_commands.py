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
# from utils import determine_quality
import math
import asyncio
import quest_manager
import utils

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

# --- VIEW CHO LỆNH /FARM DESIGN ---
class SeedSelect(discord.ui.Select):
    """Menu thả xuống để chọn hạt giống."""
    def __init__(self, plantable_seeds: list):
        options = [
            discord.SelectOption(
                label=f"Hạt {config.CROPS.get(key.split('_',1)[1], {}).get('display_name', '?')}",
                value=key,
                emoji=config.CROPS.get(key.split('_',1)[1], {}).get('emoji')
            ) for key in plantable_seeds
        ]
        super().__init__(placeholder="1. Chọn một loại hạt giống...", row=0, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Lưu lại lựa chọn của người dùng vào view và xác nhận âm thầm
        self.view.current_seed = self.values[0]
        print(f"[DESIGN DEBUG] Đã chọn hạt giống: {self.view.current_seed}")
        await interaction.response.defer()

class FarmDesignView(discord.ui.View):
    """Giao diện thiết kế nông trại có phân trang và xử lý state."""
    def __init__(self, interaction: discord.Interaction, user_data: dict):
        super().__init__(timeout=600.0)
        self.interaction = interaction
        self.user_data = user_data
        self.farm_size = user_data['farm']['size']
        self.plots = user_data['farm']['plots']
        self.message = None # Sẽ được gán sau khi gửi tin nhắn
        
        self.design = {}
        self.current_seed = None
        self.page = 0
        self.rows_per_page = 3
        self.total_pages = math.ceil(self.farm_size / self.rows_per_page)

        self.rebuild_view()

    def rebuild_view(self):
        """Xóa và xây dựng lại các thành phần giao diện dựa trên state hiện tại."""
        print(f"[DESIGN DEBUG] Đang vẽ lại giao diện trang {self.page}")
        self.clear_items()
        
        # Hàng 0: Menu chọn hạt giống
        plantable_seeds = [key for key, val in self.user_data.get("inventory", {}).items() if key.startswith("seed_") and val.get("0", 0) > 0]
        self.add_item(SeedSelect(plantable_seeds))

        # Hàng 1-3: Lưới nông trại
        start_row = self.page * self.rows_per_page
        end_row = min(start_row + self.rows_per_page, self.farm_size)

        for r in range(start_row, end_row):
            for c in range(self.farm_size):
                plot_key = f"{r}_{c}"
                view_row = (r % self.rows_per_page) + 1
                button = discord.ui.Button(style=discord.ButtonStyle.secondary, custom_id=plot_key, row=view_row)

                if self.plots.get(plot_key) is not None:
                    button.disabled = True
                    button.emoji = "❌"
                else:
                    selected_seed = self.design.get(plot_key)
                    if selected_seed:
                        button.emoji = config.CROPS[selected_seed.split('_',1)[1]]['emoji']
                    else:
                        button.emoji = config.PLOT_EMPTY_EMOJI

                button.callback = self.on_plot_button_click
                self.add_item(button)

        # Hàng 4: Các nút điều khiển
        prev_button = discord.ui.Button(label="◀️", style=discord.ButtonStyle.grey, row=4, custom_id="prev_page", disabled=(self.page == 0))
        prev_button.callback = self.change_page
        self.add_item(prev_button)

        next_button = discord.ui.Button(label="▶️", style=discord.ButtonStyle.grey, row=4, custom_id="next_page", disabled=(self.page >= self.total_pages - 1))
        next_button.callback = self.change_page
        self.add_item(next_button)

        confirm_button = discord.ui.Button(label="Xác nhận Trồng", style=discord.ButtonStyle.green, row=4, custom_id="confirm")
        confirm_button.callback = self.confirm_planting
        self.add_item(confirm_button)

        cancel_button = discord.ui.Button(label="Hủy", style=discord.ButtonStyle.red, row=4, custom_id="cancel")
        cancel_button.callback = self.cancel
        self.add_item(cancel_button)

    async def _update_view(self, interaction: discord.Interaction):
        """Hàm trung tâm để cập nhật giao diện sau mỗi hành động."""
        self.rebuild_view()
        await interaction.edit_original_response(view=self)

    async def change_page(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.data['custom_id'] == 'next_page': self.page += 1
        else: self.page -= 1
        print(f"[DESIGN DEBUG] Chuyển trang: {self.page}")
        await self._update_view(interaction)

    async def on_plot_button_click(self, interaction: discord.Interaction):
        if not self.current_seed:
            return await interaction.response.send_message("Vui lòng chọn một loại hạt giống từ menu trước!", ephemeral=True)
        
        await interaction.response.defer()
        plot_key = interaction.data['custom_id']
        if self.design.get(plot_key) == self.current_seed: del self.design[plot_key]
        else: self.design[plot_key] = self.current_seed
        print(f"[DESIGN DEBUG] Cập nhật thiết kế: {self.design}")
        await self._update_view(interaction)

    async def confirm_planting(self, interaction: discord.Interaction):
        try:
            # 1. Báo cho Discord biết bot đang xử lý
            await interaction.response.defer()

            if not self.design:
                return await interaction.followup.send("Bạn chưa thiết kế gì cả!", ephemeral=True)

            # 2. Lấy dữ liệu mới nhất của người chơi tại thời điểm bấm nút
            user_data = data_manager.get_player_data(interaction.user.id)
            if not user_data:
                return await interaction.followup.send("Không tìm thấy dữ liệu người chơi.", ephemeral=True)

            # 3. Kiểm tra lại số lượng hạt giống một lần cuối
            seeds_needed = {}
            for plot_key, seed_key in self.design.items():
                seeds_needed[seed_key] = seeds_needed.get(seed_key, 0) + 1
            
            for seed_key, needed_amount in seeds_needed.items():
                owned_amount = user_data.get('inventory', {}).get(seed_key, {}).get('0', 0)
                if owned_amount < needed_amount:
                    crop_id = seed_key.split('_', 1)[1]
                    crop_name = config.CROPS[crop_id]['display_name']
                    return await interaction.followup.send(f"Không đủ hạt giống! Cần {needed_amount} Hạt {crop_name} nhưng bạn chỉ có {owned_amount}.", ephemeral=True)

            # 4. Nếu đủ, thực hiện trồng cây
            planted_count = 0
            for plot_key, seed_key in self.design.items():
                crop_id = seed_key.split('_', 1)[1]
                crop_info = config.CROPS[crop_id]
                quality = determine_quality()
                
                user_data['farm']['plots'][plot_key] = {
                    "crop": crop_id, "plant_time": time.time(), 
                    "ready_time": time.time() + crop_info["grow_time"], "quality": quality
                }
                
                user_data['inventory'][seed_key]['0'] -= 1
                if user_data['inventory'][seed_key]['0'] <= 0: del user_data['inventory'][seed_key]
                
                planted_count += 1
            
            user_data['farm']['notification_sent'] = False
            
            # 5. Lưu dữ liệu một cách bất đồng bộ để không làm treo bot
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, data_manager.save_player_data)

            # 6. Vô hiệu hóa giao diện và thông báo thành công
            for child in self.children:
                child.disabled = True
            
            # Dùng interaction.message.edit để sửa tin nhắn chứa nút bấm
            await interaction.edit_original_response(content=f"✅ Đã trồng thành công **{planted_count}** cây theo thiết kế của bạn!", embed=None, view=self)

        except Exception as e:
            print(f"Lỗi nghiêm trọng trong nút Xác nhận Trồng: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send("Rất tiếc, đã có lỗi nghiêm trọng xảy ra. Vui lòng thử lại.", ephemeral=True)

    async def cancel(self, interaction: discord.Interaction):
        await interaction.response.defer()
        for child in self.children: child.disabled = True
        await interaction.edit_original_response(content="Đã hủy chế độ thiết kế.", view=self, embed=None)


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

    @farm.command(name="design", description="Mở giao diện thiết kế nông trại trực quan.")
    async def farm_design(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            user_data = data_manager.get_player_data(interaction.user.id)
            if not user_data: return await interaction.followup.send("Bạn cần `/register` trước!")
            
            plantable_seeds = self._get_plantable_seeds(user_data)
            if not plantable_seeds: return await interaction.followup.send("Bạn không có hạt giống nào để thiết kế.")
            
            embed = discord.Embed(
                title="🖋️ Chế độ Thiết kế Nông trại",
                description="1. Chọn một loại hạt giống từ menu.\n2. Bấm vào các ô đất trống để 'vẽ' thiết kế.\n3. Dùng nút ◀️▶️ để lật trang nếu farm lớn.\n4. Nhấn 'Xác nhận Trồng' khi hoàn tất.",
                color=discord.Color.teal()
            )
            
            view = FarmDesignView(interaction, user_data)
            await interaction.followup.send(embed=embed, view=view)
            view.message = await interaction.original_response()
        except Exception as e:
            print(f"Lỗi nghiêm trọng trong lệnh /farm design: {e}")
            import traceback
            traceback.print_exc()


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
                quality = utils.determine_quality()
                print(f"Chất lượng cây vừa trồng: {quality}") # Giữ lại dòng debug này
                plot_key = sorted(empty_plots, key=lambda x: (int(x.split('_')[0]), int(x.split('_')[1])))[i]
                user_data['farm']['plots'][plot_key] = {"crop": crop_id, "plant_time": time.time(), "ready_time": time.time() + crop_info["grow_time"], "quality": quality}
                
                user_data['inventory'][seed_key]['0'] -= 1
                if user_data['inventory'][seed_key]['0'] <= 0: del user_data['inventory'][seed_key]
                
                planted_count += 1
            
            # --- DÒNG QUAN TRỌNG NHẤT ĐỂ KÍCH HOẠT THÔNG BÁO ---
            user_data['farm']['notification_sent'] = False
            # ---------------------------------------------------
            
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

            total_harvested_amount = sum(q for qualities in harvested_items.values() for q in qualities.values())
            await quest_manager.update_quest_progress(interaction, "action_harvest", amount=total_harvested_amount)
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