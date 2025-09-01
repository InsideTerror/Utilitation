# cogs/color_viewer.py
import discord
from discord.ext import commands
from discord import app_commands

class ColorViewer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="color", description="Display a color preview from HEX code.")
    async def color(self, interaction: discord.Interaction, hex_code: str):
        if not hex_code.startswith("#"):
            hex_code = "#" + hex_code

        if len(hex_code) != 7:
            return await interaction.response.send_message("❌ Invalid HEX color format. Use format like `#FF5733`.", ephemeral=True)

        try:
            int(hex_code[1:], 16)
        except ValueError:
            return await interaction.response.send_message("❌ Not a valid HEX value.", ephemeral=True)

        embed = discord.Embed(title=f"Color Preview: {hex_code}", color=int(hex_code[1:], 16))
        embed.set_image(url=f"https://singlecolorimage.com/get/{hex_code[1:]}/400x100")
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ColorViewer(bot))
