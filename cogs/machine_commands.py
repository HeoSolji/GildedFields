# cogs/machine_commands.py

import discord
from discord.ext import commands
from discord import app_commands
import random
import data_manager, config
import time, datetime

def get_all_harvested_crops(user_data):
    """Lấy danh sách TẤT CẢ các nông sản đã thu hoạch, không phân biệt chất lượng."""
    harvested = []
    inventory = user_data.get("inventory", {})
    for item_key, qualities in inventory.items():
        if item_key.startswith("harvest_"):
            if any(q > 0 for q in qualities.values()):
                crop_id = item_key.split('_', 1)[1]
                if crop_id not in config.SEED_MAKER_CONFIG.get('blacklist', []):
                    harvested.append(item_key)
    return sorted(harvested)

class MachineCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    machine = app_commands.Group(name="machine", description="Tương tác với các máy móc của bạn.")

    async def machine_add_autocomplete(self, interaction: discord.Interaction, current: str):
        user_data = data_manager.get_player_data(interaction.user.id)
        if not user_data: return []
        
        choices = []
        processable_crops = get_all_harvested_crops(user_data)
        for item_key in processable_crops:
            crop_id = item_key.split('_', 1)[1]
            crop_name = config.CROPS[crop_id]['display_name']
            if current.lower() in crop_name.lower():
                choices.append(app_commands.Choice(name=crop_name, value=item_key))
        return choices[:25]

    @machine.command(name="view", description="Xem trạng thái của các Máy Tạo Hạt Giống.")
    async def machine_view(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            user_data = data_manager.get_player_data(interaction.user.id)
            if not user_data: return await interaction.followup.send("Bạn chưa đăng ký!")
            
            seed_makers = user_data.get('machines', {}).get('seed_maker', [])
            if not seed_makers:
                return await interaction.followup.send("Bạn chưa có Máy Tạo Hạt Giống nào. Dùng `/craftlist` để xem cách chế tạo.")

            embed = discord.Embed(
                title=f"🏭 Nhà xưởng của {interaction.user.name}", 
                description="Tổng quan về các Máy Tạo Hạt Giống của bạn.",
                color=discord.Color.light_grey()
            )
            
            for i, machine_data in enumerate(seed_makers):
                state = machine_data.get('state', 'idle')
                if state == 'idle':
                    embed.add_field(
                        name=f"Máy #{i+1} 🟢 Rảnh rỗi",
                        value="Sẵn sàng nhận nông sản mới.\nDùng `/machine add`.",
                        inline=True
                    )
                else:
                    finish_time = machine_data.get('finish_time', 0)
                    time_left = finish_time - time.time()
                    input_key = machine_data.get('input_key', 'harvest_wheat')
                    crop_id = input_key.split('_', 1)[1]
                    crop_info = config.CROPS.get(crop_id, {})
                    
                    if time_left > 0:
                        td = datetime.timedelta(seconds=int(time_left))
                        embed.add_field(
                            name=f"Máy #{i+1} 🟡 Đang hoạt động",
                            value=f"Đang xử lý: **{machine_data.get('input_qty', 0)}** {crop_info.get('emoji', '❓')}\nHoàn thành sau: `{str(td)}`",
                            inline=True
                        )
                    else:
                        embed.add_field(
                            name=f"Máy #{i+1} ✅ Đã xong!",
                            value=f"**{machine_data.get('input_qty', 0)}** {crop_info.get('emoji', '❓')} đang chờ thu hoạch.\nDùng `/machine collect`.",
                            inline=True
                        )
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"Lỗi trong /machine view: {e}")
            await interaction.followup.send("Có lỗi xảy ra khi xem máy.", ephemeral=True)

    @machine.command(name="add", description="Bỏ nông sản vào Máy Tạo Hạt Giống.")
    @app_commands.autocomplete(nông_sản=machine_add_autocomplete)
    @app_commands.describe(nông_sản="Loại nông sản muốn xử lý.", số_lượng="Số lượng muốn bỏ vào.")
    async def machine_add(self, interaction: discord.Interaction, nông_sản: str, số_lượng: int):
        try:
            await interaction.response.defer()
            user_data = data_manager.get_player_data(interaction.user.id)
            if not user_data: return await interaction.followup.send("Bạn chưa đăng ký!", ephemeral=True)
            if số_lượng <= 0: return await interaction.followup.send("Số lượng phải lớn hơn 0.", ephemeral=True)

            idle_machine = None
            seed_makers = user_data.get('machines', {}).get('seed_maker', [])
            for m in seed_makers:
                if m.get('state') == 'idle':
                    idle_machine = m
                    break
            
            if not idle_machine:
                return await interaction.followup.send("Tất cả Máy Tạo Hạt Giống của bạn đều đang bận!", ephemeral=True)

            crop_id = nông_sản.split('_', 1)[1]
            crop_info = config.CROPS.get(crop_id)
            if not crop_info or not nông_sản.startswith("harvest_"):
                 return await interaction.followup.send("Lựa chọn nông sản không hợp lệ.", ephemeral=True)

            if crop_id in config.SEED_MAKER_CONFIG.get('blacklist', []):
                return await interaction.followup.send(f"Không thể dùng Máy Tạo Hạt Giống cho {crop_info['display_name']}.", ephemeral=True)
            
            owned_qualities = user_data.get('inventory', {}).get(nông_sản, {})
            total_owned = sum(owned_qualities.values())
            if total_owned < số_lượng:
                return await interaction.followup.send(f"Bạn không có đủ {số_lượng} {crop_info['display_name']} (tính cả các cấp sao).", ephemeral=True)

            # Trừ vật phẩm, ưu tiên cấp sao thấp nhất
            amount_to_consume = số_lượng
            for quality_str in sorted(owned_qualities.keys(), key=int):
                if amount_to_consume <= 0: break
                available_in_bucket = owned_qualities[quality_str]
                consume = min(amount_to_consume, available_in_bucket)
                owned_qualities[quality_str] -= consume
                if owned_qualities[quality_str] == 0: del owned_qualities[quality_str]
                amount_to_consume -= consume
            if not owned_qualities: del user_data['inventory'][nông_sản]
            
            # Cập nhật trạng thái máy
            processing_time = số_lượng * config.SEED_MAKER_CONFIG['time_per_item']
            idle_machine['state'] = 'processing'
            idle_machine['input_key'] = nông_sản
            idle_machine['input_qty'] = số_lượng
            idle_machine['finish_time'] = time.time() + processing_time
            
            td = datetime.timedelta(seconds=int(processing_time))
            
            embed = discord.Embed(
                title="⚙️ Bắt đầu Xử lý",
                description=f"Đã bỏ **{số_lượng}** {crop_info['emoji']} {crop_info['display_name']} vào một máy rảnh rỗi.",
                color=discord.Color.yellow()
            )
            embed.add_field(name="Thời gian hoàn thành", value=f"`{str(td)}`")
            await interaction.followup.send(embed=embed)
            data_manager.save_player_data()
        except Exception as e:
            print(f"Lỗi trong lệnh /machine add: {e}")
            await interaction.followup.send("Có lỗi xảy ra.", ephemeral=True)

    @machine.command(name="collect", description="Thu hoạch hạt giống từ các máy đã chạy xong.")
    async def machine_collect(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            user_data = data_manager.get_player_data(interaction.user.id)
            if not user_data: return await interaction.followup.send("Bạn chưa đăng ký!", ephemeral=True)
            
            seed_makers = user_data.get('machines', {}).get('seed_maker', [])
            collected_summary = {}
            collected_anything = False

            for machine in seed_makers:
                if machine.get('state') == 'processing' and time.time() >= machine.get('finish_time', float('inf')):
                    collected_anything = True
                    original_crop_id = machine['input_key'].split('_', 1)[1]
                    
                    for _ in range(machine['input_qty']):
                        cfg = config.SEED_MAKER_CONFIG
                        roll = random.random()
                        if roll < cfg['chance_same_seed']:
                            amount = random.randint(cfg['min_same_seed'], cfg['max_same_seed'])
                            seed_key = f"seed_{original_crop_id}"
                            collected_summary[seed_key] = collected_summary.get(seed_key, 0) + amount
                        else:
                            rare_seed_id = "ancient_fruit"
                            seed_key = f"seed_{rare_seed_id}"
                            collected_summary[seed_key] = collected_summary.get(seed_key, 0) + 1
                    
                    machine['state'] = 'idle'
                    machine.pop('input_key', None); machine.pop('input_qty', None); machine.pop('finish_time', None)
            
            if not collected_anything:
                return await interaction.followup.send("Không có hạt giống nào sẵn sàng để thu hoạch.", ephemeral=True)
                
            summary_lines = []
            for seed_key, quantity in collected_summary.items():
                user_data['inventory'].setdefault(seed_key, {})['0'] = user_data['inventory'].setdefault(seed_key, {}).get('0', 0) + quantity
                crop_id = seed_key.split('_', 1)[1]
                crop_info = config.CROPS[crop_id]
                summary_lines.append(f"• {quantity} {crop_info['emoji']} Hạt {crop_info['display_name']}")
            
            embed = discord.Embed(
                title="📦 Thu hoạch từ Máy móc",
                description="Bạn đã thu hoạch các vật phẩm sau:",
                color=discord.Color.green()
            )
            embed.add_field(name="Hạt giống nhận được", value="\n".join(summary_lines))
            await interaction.followup.send(embed=embed)
            data_manager.save_player_data()
        except Exception as e:
            print(f"Lỗi trong lệnh /machine collect: {e}")
            await interaction.followup.send("Có lỗi xảy ra.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MachineCommands(bot))