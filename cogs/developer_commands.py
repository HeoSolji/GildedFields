# cogs/developer_commands.py

import discord
from discord.ext import commands
import os

class Developer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Dùng decorator @commands.is_owner() để đảm bảo chỉ chủ bot mới chạy được lệnh này
    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def reload_cogs(self, ctx, *, cog: str):
        """Tải lại một hoặc tất cả các cogs.
        
        Để tải lại một cog, dùng: !reload [tên_cog]
        Ví dụ: !reload farm_commands
        
        Để tải lại tất cả, dùng: !reload all
        """
        if cog.lower() == 'all':
            reloaded_cogs = []
            error_cogs = []
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    cog_name = f"cogs.{filename[:-3]}"
                    try:
                        await self.bot.reload_extension(cog_name)
                        reloaded_cogs.append(f"`{cog_name}`")
                    except Exception as e:
                        error_cogs.append(f"`{cog_name}`: {e}")
            
            success_message = f"✅ Đã tải lại thành công: {', '.join(reloaded_cogs)}" if reloaded_cogs else ""
            error_message = f"❌ Lỗi khi tải lại: {', '.join(error_cogs)}" if error_cogs else ""
            await ctx.send(f"{success_message}\n{error_message}".strip())
            return

        try:
            cog_name = f"cogs.{cog}"
            await self.bot.reload_extension(cog_name)
            await ctx.send(f'✅ Cog `{cog_name}` đã được tải lại thành công!')
        except commands.ExtensionNotLoaded:
            await ctx.send(f'⚠️ Cog `{cog_name}` chưa được tải, đang thử tải mới...')
            try:
                await self.bot.load_extension(cog_name)
                await ctx.send(f'✅ Cog `{cog_name}` đã được tải lần đầu thành công!')
            except Exception as e:
                await ctx.send(f'❌ Lỗi khi tải cog `{cog_name}`: ```py\n{e}\n```')
        except Exception as e:
            await ctx.send(f'❌ Lỗi khi tải lại cog `{cog_name}`: ```py\n{e}\n```')

# Hàm setup để bot có thể nhận diện cog này
async def setup(bot):
    await bot.add_cog(Developer(bot))