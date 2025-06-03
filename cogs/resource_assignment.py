import discord
from discord.ext import commands
from discord import app_commands
from utils.permissions import is_authorized_prefix, is_authorized_slash

class ResourceAssignment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.unit_resources = {}  # {unit_name: {resource_name: quantity}}

    # Assign resources (prefix)
    @commands.command(name="assign_resource")
    @is_authorized_prefix()
    async def assign_resource_cmd(self, ctx, unit: str, resource: str, quantity: int):
        unit_dict = self.unit_resources.setdefault(unit, {})
        unit_dict[resource] = unit_dict.get(resource, 0) + quantity
        await ctx.send(f"✅ Assigned {quantity} of {resource} to {unit}.")

    # Assign resources (slash)
    @app_commands.command(name="assignresource", description="Assign a resource to a unit")
    async def assign_resource_slash(self, interaction: discord.Interaction, unit: str, resource: str, quantity: int):
        if not await is_authorized_slash(interaction.user):
            await interaction.response.send_message("🚫 You are not authorized.", ephemeral=True)
            return
        unit_dict = self.unit_resources.setdefault(unit, {})
        unit_dict[resource] = unit_dict.get(resource, 0) + quantity
        await interaction.response.send_message(f"✅ Assigned {quantity} of {resource} to {unit}.")

    # View resources of a unit (prefix)
    @commands.command(name="view_unit_resources")
    async def view_unit_resources_cmd(self, ctx, unit: str):
        unit_dict = self.unit_resources.get(unit)
        if not unit_dict:
            await ctx.send(f"❌ No resources found for {unit}.")
            return
        resource_list = "\n".join([f"{res}: {qty}" for res, qty in unit_dict.items()])
        await ctx.send(f"📦 Resources for {unit}:\n{resource_list}")

    # View resources of a unit (slash)
    @app_commands.command(name="viewunitresources", description="View all resources assigned to a unit")
    async def view_unit_resources_slash(self, interaction: discord.Interaction, unit: str):
        unit_dict = self.unit_resources.get(unit)
        if not unit_dict:
            await interaction.response.send_message(f"❌ No resources found for {unit}.", ephemeral=True)
            return
        resource_list = "\n".join([f"{res}: {qty}" for res, qty in unit_dict.items()])
        await interaction.response.send_message(f"📦 Resources for {unit}:\n{resource_list}")

async def setup(bot):
    await bot.add_cog(ResourceAssignment(bot))
