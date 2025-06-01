import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from utils.permissions import has_role_permission

DATA_FILE = "data/personnel.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

class PersonnelDB(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.personnel = load_data()

    def save(self):
        save_data(self.personnel)

    @app_commands.command(name="personnel_add", description="Add a new personnel record")
    @app_commands.describe(name="Full name", rank="Rank of personnel", unit="Assigned unit", status="Status (Active/On Leave/etc)")
    async def personnel_add(self, interaction: discord.Interaction, name: str, rank: str, unit: str, status: str):
        if not has_role_permission(interaction.user, ["Commander", "HR"]):
            await interaction.response.send_message("You do not have permission to add personnel.", ephemeral=True)
            return

        if name in self.personnel:
            await interaction.response.send_message(f"Personnel `{name}` already exists.", ephemeral=True)
            return

        self.personnel[name] = {
            "rank": rank,
            "unit": unit,
            "status": status,
            "role": "",
            "clearance": "",
            "notes": ""
        }
        self.save()
        await interaction.response.send_message(f"Personnel `{name}` added successfully.", ephemeral=True)

    @app_commands.command(name="personnel_update", description="Update a personnel record field")
    @app_commands.describe(name="Name of personnel", field="Field to update", value="New value")
    async def personnel_update(self, interaction: discord.Interaction, name: str, field: str, value: str):
        if not has_role_permission(interaction.user, ["Commander", "HR"]):
            await interaction.response.send_message("You do not have permission to update personnel.", ephemeral=True)
            return

        if name not in self.personnel:
            await interaction.response.send_message(f"Personnel `{name}` not found.", ephemeral=True)
            return

        if field.lower() not in ["rank", "unit", "status", "role", "clearance", "notes"]:
            await interaction.response.send_message(f"Invalid field `{field}`. Allowed fields: rank, unit, status, role, clearance, notes.", ephemeral=True)
            return

        self.personnel[name][field.lower()] = value
        self.save()
        await interaction.response.send_message(f"Personnel `{name}` updated: {field} set to `{value}`.", ephemeral=True)

    @app_commands.command(name="personnel_view", description="View details of a personnel record")
    @app_commands.describe(name="Name of personnel")
    async def personnel_view(self, interaction: discord.Interaction, name: str):
        if name not in self.personnel:
            await interaction.response.send_message(f"Personnel `{name}` not found.", ephemeral=True)
            return

        p = self.personnel[name]
        embed = discord.Embed(title=f"Personnel Record: {name}", color=0x2F3136)
        embed.add_field(name="Rank", value=p.get("rank", "N/A"), inline=True)
        embed.add_field(name="Unit", value=p.get("unit", "N/A"), inline=True)
        embed.add_field(name="Status", value=p.get("status", "N/A"), inline=True)
        embed.add_field(name="Role", value=p.get("role", "N/A"), inline=True)
        embed.add_field(name="Clearance Level", value=p.get("clearance", "N/A"), inline=True)
        embed.add_field(name="Notes", value=p.get("notes", "None"), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="personnel_list", description="List personnel optionally filtered by unit or status")
    @app_commands.describe(filter_by="Filter type: unit or status", filter_value="Filter value")
    async def personnel_list(self, interaction: discord.Interaction, filter_by: str = None, filter_value: str = None):
        # No restrictions on viewing the list

        if filter_by and filter_by.lower() not in ["unit", "status"]:
            await interaction.response.send_message("Filter type must be 'unit' or 'status'.", ephemeral=True)
            return

        filtered = []
        for name, p in self.personnel.items():
            if filter_by and filter_value:
                if p.get(filter_by.lower(), "").lower() == filter_value.lower():
                    filtered.append(f"**{name}** - {p.get('rank', 'N/A')} ({p.get('unit', 'N/A')})")
            else:
                filtered.append(f"**{name}** - {p.get('rank', 'N/A')} ({p.get('unit', 'N/A')})")

        if not filtered:
            await interaction.response.send_message("No personnel found matching the filter.", ephemeral=True)
            return

        # Split the list into pages of 10
        pages = [filtered[i:i+10] for i in range(0, len(filtered), 10)]
        embed = discord.Embed(title="Personnel List", color=0x2F3136)
        embed.description = "\n".join(pages[0])
        embed.set_footer(text=f"Page 1 of {len(pages)}")

        message = await interaction.response.send_message(embed=embed, ephemeral=True)

        # Optional: Add pagination reactions/buttons here if you want (not implemented now)

