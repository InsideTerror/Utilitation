import discord
from discord.ext import commands
from discord import app_commands
from utils.permissions import is_authorized_prefix, is_authorized_slash

class MilitaryResources(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.resources = {}  # {name: quantity}

    # Add Resource
    @commands.command(name="add_resource")
    @is_authorized_prefix()
    async def add_resource_cmd(self, ctx, name: str, quantity: int):
        self.resources[name] = self.resources.get(name, 0) + quantity
        await ctx.send(f"Added {quantity} of {name}. New total: {self.resources[name]}")

    @app_commands.command(name="addresource", description="Add military resource")
    async def add_resource_slash(self, interaction: discord.Interaction, name: str, quantity: int):
        if not await is_authorized_slash(interaction.user):
            await interaction.response.send_message("You are not authorized.", ephemeral=True)
            return
        self.resources[name] = self.resources.get(name, 0) + quantity
        await interaction.response.send_message(f"Added {quantity} of {name}. New total: {self.resources[name]}")

    # Remove Resource
    @commands.command(name="remove_resource")
    @is_authorized_prefix()
    async def remove_resource_cmd(self, ctx, name: str, quantity: int):
        if name not in self.resources:
            await ctx.send("Resource not found.")
            return
        self.resources[name] = max(0, self.resources[name] - quantity)
        await ctx.send(f"Removed {quantity} of {name}. Remaining: {self.resources[name]}")

    @app_commands.command(name="removeresource", description="Remove military resource")
    async def remove_resource_slash(self, interaction: discord.Interaction, name: str, quantity: int):
        if not await is_authorized_slash(interaction.user):
            await interaction.response.send_message("You are not authorized.", ephemeral=True)
            return
        if name not in self.resources:
            await interaction.response.send_message("Resource not found.", ephemeral=True)
            return
        self.resources[name] = max(0, self.resources[name] - quantity)
        await interaction.response.send_message(f"Removed {quantity} of {name}. Remaining: {self.resources[name]}")

    # View Resources
    @commands.command(name="view_resources")
    async def view_resources_cmd(self, ctx):
        if not self.resources:
            await ctx.send("No resources.")
            return
        msg = "\n".join([f"{k}: {v}" for k, v in self.resources.items()])
        await ctx.send(f"Resources:\n{msg}")

    @app_commands.command(name="viewresources", description="View all military resources")
    async def view_resources_slash(self, interaction: discord.Interaction):
        if not self.resources:
            await interaction.response.send_message("No resources.")
            return
        msg = "\n".join([f"{k}: {v}" for k, v in self.resources.items()])
        await interaction.response.send_message(f"Resources:\n{msg}")

async def setup(bot):
    await bot.add_cog(MilitaryResources(bot))
