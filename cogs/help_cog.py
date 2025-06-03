import discord
from discord.ext import commands
from discord import app_commands

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Prefix command: !commands
    @commands.command(name="commands", help="Show all commands")
    async def commands_prefix(self, ctx):
        embed = self.generate_help_embed()
        await ctx.send(embed=embed)

    # Slash command: /commands
    @app_commands.command(name="commands", description="Show all commands")
    async def commands_slash(self, interaction: discord.Interaction):
        embed = self.generate_help_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    def generate_help_embed(self):
        embed = discord.Embed(title="🪖 Military Bot Commands", color=discord.Color.green())

        embed.add_field(name="Personnel & Units",
                        value="`/addperson`, `/removeperson`, `/promote`, `/demote`, `/transfer`, `/createunit`, `/removeunit`, `/viewunit`, `/viewpersonnel`",
                        inline=False)

        embed.add_field(name="Resources",
                        value="`/addresource`, `/removeresource`, `/viewresources`, `/assignresource`, `/unitresources`",
                        inline=False)

        embed.add_field(name="General",
                        value="`!commands` or `/commands` - Show this help menu", inline=False)

        embed.set_footer(text="Fictional military system • Use responsibly.")
        return embed

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
