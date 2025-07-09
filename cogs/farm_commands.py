# cogs/farm_commands.py

import discord
from discord.ext import commands
import time
import datetime
import data_manager
import config
import season_manager
import achievement_manager

# --- CLASS VIEW ĐỂ CHỨA NÚT BẤM CHO LỆNH !FARM (Giữ nguyên) ---
class FarmView(discord.ui.View):
    def __init__(self, user_id, timeout=180):
        super().__init__(timeout=timeout)
        self.user_id = user_id

    @discord.ui.button(label="Xem thời gian", style=discord.ButtonStyle.secondary, emoji="⏰")
    async def show_times(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ... (Nội dung hàm này giữ nguyên)
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
                crop_info = config.CROPS[plot_data["crop"]]
                time_left_seconds = plot_data["ready_time"] - current_time
                td = datetime.timedelta(seconds=int(time_left_seconds))
                r, c = map(int, plot_key.split('_'))
                growing_crops_details.append(f"**Ô ({r+1},{c+1})** {crop_info['emoji']}: Còn lại `{str(td)}`")
        content = "\n".join(growing_crops_details) if growing_crops_details else "Bạn không có cây nào đang lớn cả!"
        await interaction.response.send_message(content, ephemeral=True)


class Farm(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- HÀM TRỢ GIÚP MỚI ---
    def _get_plantable_seeds(self, user_data):
        """Lấy danh sách các loại hạt giống có trong kho đồ."""
        plantable_seeds = []
        inventory = user_data.get("inventory", {})
        for item_key in sorted(inventory.keys()):
            if inventory[item_key] > 0 and item_key.startswith("seed_"):
                plantable_seeds.append(item_key)
        return plantable_seeds

    # ... (Hàm check_for_level_up, farm, farm_upgrade giữ nguyên) ...
    async def check_for_level_up(self, ctx, user_data):
        level = user_data.get('level', 1)
        xp = user_data.get('xp', 0)
        xp_needed = config.get_xp_for_level(level)
        while xp >= xp_needed:
            user_data['level'] += 1
            user_data['xp'] -= xp_needed
            user_data['balance'] += config.REWARD_PER_LEVEL_UP
            level = user_data['level']
            xp = user_data['xp']
            xp_needed = config.get_xp_for_level(level)
            await ctx.send(f"🎉 **CHÚC MỪNG** {ctx.author.mention}! Bạn đã lên **Cấp {level}**! Bạn nhận được {config.REWARD_PER_LEVEL_UP} {config.CURRENCY_SYMBOL} tiền thưởng.")

    @commands.group(name='farm', aliases=['f'], invoke_without_command=True)
    async def farm(self, ctx, member: discord.Member = None):
        target_user = member or ctx.author
        user_data = data_manager.get_player_data(target_user.id)
        if not user_data: return await ctx.send(f"Người chơi {target_user.mention} chưa đăng ký game!")
        farm_size = user_data["farm"]["size"]
        farm_plots = user_data["farm"]["plots"]
        current_time = time.time()
        farm_grid_display = []
        for r in range(farm_size):
            row_emojis = []
            for c in range(farm_size):
                plot_key = f"{r}_{c}"
                plot_data = farm_plots.get(plot_key)
                if not plot_data: row_emojis.append(config.PLOT_EMPTY_EMOJI)
                else:
                    if current_time >= plot_data["ready_time"]: row_emojis.append(config.PLOT_READY_EMOJI)
                    else: row_emojis.append(config.CROPS[plot_data["crop"]]["emoji"])
            farm_grid_display.append(" ".join(row_emojis))
        embed = discord.Embed(title=f"Nông trại của {target_user.name} ({farm_size}x{farm_size})", description="\n".join(farm_grid_display), color=discord.Color.dark_green())
        if target_user == ctx.author:
            embed.set_footer(text="Dùng !farm upgrade để nâng cấp. Bấm nút để xem thời gian.")
            view = FarmView(user_id=ctx.author.id)
            await ctx.send(embed=embed, view=view)
        else: await ctx.send(embed=embed)

    @farm.command(name='upgrade')
    async def farm_upgrade(self, ctx):
        try:
            user_data = data_manager.get_player_data(ctx.author.id)
            if not user_data: return await ctx.send("Bạn chưa đăng ký. Dùng `!register` để bắt đầu!")
            current_size = user_data.get('farm', {}).get('size', config.FARM_GRID_SIZE)
            user_balance = user_data.get('balance', 0)
            user_level = user_data.get('level', 1)
            if current_size >= config.MAX_FARM_SIZE: return await ctx.send("Nông trại của bạn đã đạt kích thước tối đa!")
            next_size = current_size + 1
            upgrade_info = config.FARM_UPGRADES.get(next_size)
            if not upgrade_info: return await ctx.send("Không có thông tin nâng cấp cho kích thước tiếp theo hoặc đã đạt tối đa.")
            cost = upgrade_info['cost']
            level_required = upgrade_info['level_required']
            if user_level < level_required: return await ctx.send(f"Bạn cần đạt **Cấp {level_required}** để nâng cấp lên {next_size}x{next_size}.")
            if user_balance < cost: return await ctx.send(f"Bạn không đủ tiền! Cần {cost} {config.CURRENCY_SYMBOL} để nâng cấp, bạn chỉ có {user_balance}.")
            user_data['balance'] -= cost
            user_data['farm']['size'] = next_size
            for r in range(next_size):
                for c in range(next_size):
                    plot_key = f"{r}_{c}"
                    if plot_key not in user_data['farm']['plots']: user_data['farm']['plots'][plot_key] = None
            data_manager.save_player_data()
            await ctx.send(f"🎉 **Chúc mừng!** Bạn đã chi {cost} {config.CURRENCY_SYMBOL} để nâng cấp thành công nông trại lên kích thước **{next_size}x{next_size}**!")
        except Exception as e:
            print(f"Lỗi nghiêm trọng trong lệnh !farm upgrade: {e}")
            import traceback; traceback.print_exc()
            await ctx.send(f"Rất tiếc, đã có lỗi xảy ra khi xử lý lệnh của bạn. Vui lòng báo cho quản trị viên và gửi kèm thông tin sau: `Lỗi trong farm/upgrade - {type(e).__name__}`")

    # --- LỆNH MỚI ---
    @commands.command(name='seeds')
    async def seeds(self, ctx):
        """Xem danh sách các loại hạt giống bạn có thể trồng."""
        user_data = data_manager.get_player_data(ctx.author.id)
        if not user_data: return await ctx.send('Bạn chưa đăng ký!')

        plantable_seeds = self._get_plantable_seeds(user_data)
        if not plantable_seeds:
            return await ctx.send("Bạn không có hạt giống nào trong kho đồ. Dùng `!shop` để mua nhé.")

        embed = discord.Embed(title=f"Túi hạt giống của {ctx.author.name}", color=discord.Color.dark_green())
        lines = []
        for index, seed_key in enumerate(plantable_seeds):
            quantity = user_data["inventory"][seed_key]
            crop_id = seed_key.split('_', 1)[1]
            crop_info = config.CROPS.get(crop_id)
            if crop_info:
                lines.append(f"**{index + 1}.** {crop_info['emoji']} **Hạt {crop_info['display_name']}**: `{quantity}`")

        embed.description = "\n".join(lines)
        embed.set_footer(text="Dùng !plant [số] [lượng] để trồng")
        await ctx.send(embed=embed)

    # --- LÀM LẠI HOÀN TOÀN LỆNH PLANT ---
    @commands.command(name='plant', aliases=['p'])
    async def plant(self, ctx, item_index: int, amount: int = 1):
        """Trồng hạt giống từ túi hạt giống của bạn (!seeds)."""
        try:
            user_data = data_manager.get_player_data(ctx.author.id)
            if not user_data: return await ctx.send('Bạn chưa đăng ký!')
            if amount <= 0: return await ctx.send("Số lượng trồng phải lớn hơn 0.")

            # Lấy danh sách hạt giống từ kho đồ của người chơi
            plantable_seeds = self._get_plantable_seeds(user_data)
            index = item_index - 1

            if not (0 <= index < len(plantable_seeds)):
                return await ctx.send(f"Số thứ tự `{item_index}` không hợp lệ. Dùng `!seeds` để xem lại.")

            seed_key = plantable_seeds[index]
            crop_id = seed_key.split('_', 1)[1]
            crop_info = config.CROPS[crop_id]
            
            # Kiểm tra mùa
            current_season = season_manager.get_current_season()['name']
            if current_season not in crop_info['seasons']:
                return await ctx.send(f"Không thể trồng {crop_info['display_name']} trong mùa này!")

            # Kiểm tra số lượng hạt giống sở hữu
            seeds_owned = user_data['inventory'].get(seed_key, 0)
            if seeds_owned < amount:
                return await ctx.send(f"Bạn không có đủ {amount} hạt {crop_info['display_name']}. Bạn chỉ có {seeds_owned}.")

            # Tìm ô đất trống và trồng cây (logic này giữ nguyên)
            empty_plots = [key for key, value in user_data['farm']['plots'].items() if value is None]
            if not empty_plots: return await ctx.send("Tất cả ô đất đã được trồng! Dùng `!harvest` để thu hoạch.")

            planted_count = 0
            current_time = time.time()
            for plot_key in sorted(empty_plots, key=lambda x: (int(x.split('_')[0]), int(x.split('_')[1]))):
                if planted_count >= amount: break
                user_data['farm']['plots'][plot_key] = {"crop": crop_id, "plant_time": current_time, "ready_time": current_time + crop_info["grow_time"]}
                user_data['inventory'][seed_key] -= 1
                planted_count += 1
            
            grow_time_str = config.get_grow_time_string(crop_info["grow_time"])
            await ctx.send(f"Đã trồng thành công {planted_count} {crop_info['emoji']} {crop_info['display_name']}. Cây sẽ lớn sau {grow_time_str}.")
            if planted_count < amount:
                await ctx.send(f"Lưu ý: Chỉ trồng được {planted_count} cây do không đủ ô đất trống.")
            
            user_data['farm']['notification_sent'] = False

            data_manager.save_player_data()
        
        except Exception as e:
            print(f"Lỗi trong lệnh !plant: {e}")
            await ctx.send("Có lỗi xảy ra khi thực hiện lệnh trồng cây.")

    @commands.command(name='harvest', aliases=['h'])
    async def harvest(self, ctx):
        # ... (Nội dung hàm này giữ nguyên) ...
        try:
            user_data = data_manager.get_player_data(ctx.author.id)
            if not user_data: return await ctx.send('Bạn chưa đăng ký!')
            farm_plots = user_data['farm']['plots']
            current_time = time.time()
            harvested_items = {}
            plots_to_clear = []
            for plot_key, plot_data in farm_plots.items():
                if plot_data and current_time >= plot_data['ready_time']:
                    crop_id = plot_data['crop']
                    if crop_id in config.CROPS:
                        harvested_items[crop_id] = harvested_items.get(crop_id, 0) + 1
                        plots_to_clear.append(plot_key)
                    else:
                        print(f"Phát hiện cây trồng không hợp lệ '{crop_id}' trong farm của {ctx.author.id}. Sẽ xóa bỏ.")
                        plots_to_clear.append(plot_key)
            if not harvested_items:
                if plots_to_clear:
                    for plot_key in plots_to_clear: farm_plots[plot_key] = None
                    data_manager.save_player_data()
                    return await ctx.send("Đã dọn dẹp một số cây trồng không còn hợp lệ khỏi nông trại của bạn.")
                else: return await ctx.send("Không có cây nào sẵn sàng để thu hoạch.")
            total_xp_gained = 0
            harvest_summary = []
            for crop_id, quantity in harvested_items.items():
                harvest_key = f"harvest_{crop_id}"
                user_data['inventory'][harvest_key] = user_data['inventory'].get(harvest_key, 0) + quantity
                crop_info = config.CROPS[crop_id]
                harvest_summary.append(f"{quantity} {crop_info['emoji']} {crop_info['display_name']}")
                total_xp_gained += config.XP_PER_CROP.get(crop_id, 0) * quantity
            for plot_key in plots_to_clear: farm_plots[plot_key] = None
            await ctx.send(f"{ctx.author.mention}, bạn đã thu hoạch thành công: {', '.join(harvest_summary)}.")
            if total_xp_gained > 0:
                user_data['xp'] = user_data.get('xp', 0) + total_xp_gained
                await ctx.send(f"Bạn nhận được **{total_xp_gained} XP**!")
                await self.check_for_level_up(ctx, user_data)
            
            for crop_id, quantity in harvested_items.items():
                await achievement_manager.check_achievements(ctx, user_data, "harvest", event_id=crop_id, amount=quantity)

            if total_xp_gained > 0:
                user_data['xp'] += total_xp_gained
                await ctx.send(f"Bạn nhận được **{total_xp_gained} XP**!")
                # Kiểm tra thành tựu lên cấp
                leveled_up = await self.check_for_level_up(ctx, user_data)
                if leveled_up:
                    await achievement_manager.check_achievements(ctx, user_data, "level")
                    
            user_data['farm']['notification_sent'] = True
            data_manager.save_player_data()
        except Exception as e:
            print(f"Lỗi trong lệnh !harvest: {e}")
            import traceback; traceback.print_exc()
            await ctx.send("Rất tiếc, đã có lỗi xảy ra khi thu hoạch. Vui lòng thử lại.")
        
    @commands.command(name='farmtime', aliases=['ftime'])
    async def farmtime(self, ctx):
        # ... (Nội dung hàm này giữ nguyên) ...
        user_data = data_manager.get_player_data(ctx.author.id)
        if not user_data: return await ctx.send('Bạn chưa đăng ký!')
        farm_plots = user_data["farm"]["plots"]
        current_time = time.time()
        growing_crops_details = []
        sorted_plots = sorted(farm_plots.items(), key=lambda item: (int(item[0].split('_')[0]), int(item[0].split('_')[1])))
        for plot_key, plot_data in sorted_plots:
            if plot_data and current_time < plot_data["ready_time"]:
                crop_info = config.CROPS[plot_data["crop"]]
                time_left_seconds = plot_data["ready_time"] - current_time
                td = datetime.timedelta(seconds=int(time_left_seconds))
                r, c = map(int, plot_key.split('_'))
                growing_crops_details.append(f"**Ô ({r+1},{c+1})** {crop_info['emoji']} {crop_info['display_name']}: Còn lại `{str(td)}`")
        if not growing_crops_details: return await ctx.send("Bạn không có cây nào đang lớn cả!")
        embed = discord.Embed(title=f"Thời Gian Cây Trồng của {ctx.author.name}", description="\n".join(growing_crops_details), color=discord.Color.from_rgb(139, 69, 19))
        embed.set_footer(text="Thời gian được hiển thị theo dạng Giờ:Phút:Giây")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Farm(bot))