import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from utils.permissions import is_authorized

DATA_PATH = "data/resources.json"
RESOURCE_TYPES = ["ammo", "rations", "fuel", "medkits", "vehicles"]

def load_data():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=4)

class MilitaryResources(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    def save(self):
        save_data(self.data)

    @app_commands.command(name="resources_view", description="View current resource levels for a unit.")
    async def view_resources(self, interaction: discord.Interaction, unit: str):
        unit_data = self.data.get(unit.lower())
        if not unit_data:
            await interaction.response.send_message(f"No data found for unit `{unit}`.", ephemeral=True)
            return
        embed = discord.Embed(title=f"Resources for {unit}", color=discord.Color.dark_green())
        for rtype in RESOURCE_TYPES:
            embed.add_field(name=rtype.capitalize(), value=str(unit_data.get(rtype, 0)), inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="resources_allocate", description="Allocate resources to a unit.")
    async def allocate_resources(self, interaction: discord.Interaction, unit: str, resource: str, amount: int):
        if not await is_authorized(interaction.user, ["Commander", "Quartermaster"]):
            await interaction.response.send_message("You are not authorized to allocate resources.", ephemeral=True)
            return
        resource = resource.lower()
        if resource not in RESOURCE_TYPES:
            await interaction.response.send_message("Invalid resource type.", ephemeral=True)
            return
        unit_data = self.data.setdefault(unit.lower(), {})
        unit_data[resource] = unit_data.get(resource, 0) + amount
        self.save()
        await interaction.response.send_message(f"Allocated {amount} {resource} to {unit}.")

    @app_commands.command(name="resources_consume", description="Consume resources for an operation.")
    async def consume_resources(self, interaction: discord.Interaction, unit: str, resource: str, amount: int, operation: str):
        if not await is_authorized(interaction.user, ["Commander", "Quartermaster"]):
            await interaction.response.send_message("You are not authorized to consume resources.", ephemeral=True)
            return
        resource = resource.lower()
        if resource not in RESOURCE_TYPES:
            await interaction.response.send_message("Invalid resource type.", ephemeral=True)
            return
        unit_data = self.data.setdefault(unit.lower(), {})
        current = unit_data.get(resource, 0)
        if current < amount:
            await interaction.response.send_message(f"Not enough {resource} in stock. Only {current} available.", ephemeral=True)
            return
        unit_data[resource] = current - amount
        self.save()
        await interaction.response.send_message(f"Consumed {amount} {resource} from {unit} for {operation}.")

async def setup(bot):
    await bot.add_cog(MilitaryResources(bot))
