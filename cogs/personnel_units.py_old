import discord
from discord.ext import commands
from discord import app_commands
import json
import os

DATA_FILE = "./data/personnel_units.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        # Initialize empty structure
        return {"units": {}, "personnel": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def normalize_user_key(user: discord.User | discord.Member):
    return str(user.id)

class PersonnelUnits(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    def ensure_unit_exists(self, unit_name: str):
        if unit_name not in self.data["units"]:
            self.data["units"][unit_name] = {
                "troop_count": 0,
                "personnel": []
            }

    def save(self):
        save_data(self.data)

    # ======= PERSONNEL COMMANDS =======

    @commands.command(name="addperson")
    async def add_person_cmd(self, ctx, member: discord.Member, rank: str, *, unit_name: str):
        """Add a new person with rank and assign to a unit (auto-creates unit)"""
        self.ensure_unit_exists(unit_name)
        user_key = normalize_user_key(member)

        # If person already exists, remove from old unit first
        if user_key in self.data["personnel"]:
            old_unit = self.data["personnel"][user_key]["unit"]
            if old_unit in self.data["units"]:
                if user_key in self.data["units"][old_unit]["personnel"]:
                    self.data["units"][old_unit]["personnel"].remove(user_key)

        self.data["personnel"][user_key] = {
            "name": str(member),
            "rank": rank,
            "unit": unit_name
        }
        self.data["units"][unit_name]["personnel"].append(user_key)
        self.save()
        await ctx.send(f"Added {member.mention} as '{rank}' to unit '{unit_name}'.")

    @app_commands.command(name="addperson", description="Add a new person with rank and unit")
    async def add_person_slash(self, interaction: discord.Interaction, member: discord.Member, rank: str, unit_name: str):
        self.ensure_unit_exists(unit_name)
        user_key = normalize_user_key(member)

        if user_key in self.data["personnel"]:
            old_unit = self.data["personnel"][user_key]["unit"]
            if old_unit in self.data["units"]:
                if user_key in self.data["units"][old_unit]["personnel"]:
                    self.data["units"][old_unit]["personnel"].remove(user_key)

        self.data["personnel"][user_key] = {
            "name": str(member),
            "rank": rank,
            "unit": unit_name
        }
        self.data["units"][unit_name]["personnel"].append(user_key)
        self.save()
        await interaction.response.send_message(f"Added {member.mention} as '{rank}' to unit '{unit_name}'.")

    @commands.command(name="removeperson")
    async def remove_person_cmd(self, ctx, member: discord.Member):
        """Remove a person from personnel and their unit"""
        user_key = normalize_user_key(member)
        if user_key not in self.data["personnel"]:
            await ctx.send(f"{member.mention} is not in personnel database.")
            return
        unit_name = self.data["personnel"][user_key]["unit"]
        if unit_name in self.data["units"]:
            if user_key in self.data["units"][unit_name]["personnel"]:
                self.data["units"][unit_name]["personnel"].remove(user_key)
        del self.data["personnel"][user_key]
        self.save()
        await ctx.send(f"Removed {member.mention} from personnel.")

    @app_commands.command(name="removeperson", description="Remove a person from personnel database")
    async def remove_person_slash(self, interaction: discord.Interaction, member: discord.Member):
        user_key = normalize_user_key(member)
        if user_key not in self.data["personnel"]:
            await interaction.response.send_message(f"{member.mention} is not in personnel database.", ephemeral=True)
            return
        unit_name = self.data["personnel"][user_key]["unit"]
        if unit_name in self.data["units"]:
            if user_key in self.data["units"][unit_name]["personnel"]:
                self.data["units"][unit_name]["personnel"].remove(user_key)
        del self.data["personnel"][user_key]
        self.save()
        await interaction.response.send_message(f"Removed {member.mention} from personnel.")

    @commands.command(name="promote")
    async def promote_cmd(self, ctx, member: discord.Member, *, new_rank: str):
        """Change a person's rank"""
        user_key = normalize_user_key(member)
        if user_key not in self.data["personnel"]:
            await ctx.send(f"{member.mention} is not in personnel database.")
            return
        self.data["personnel"][user_key]["rank"] = new_rank
        self.save()
        await ctx.send(f"Promoted {member.mention} to '{new_rank}'.")

    @app_commands.command(name="promote", description="Change a person's rank")
    async def promote_slash(self, interaction: discord.Interaction, member: discord.Member, new_rank: str):
        user_key = normalize_user_key(member)
        if user_key not in self.data["personnel"]:
            await interaction.response.send_message(f"{member.mention} is not in personnel database.", ephemeral=True)
            return
        self.data["personnel"][user_key]["rank"] = new_rank
        self.save()
        await interaction.response.send_message(f"Promoted {member.mention} to '{new_rank}'.")

    @commands.command(name="transfer")
    async def transfer_cmd(self, ctx, member: discord.Member, *, new_unit: str):
        """Transfer a person to a different unit (auto-create unit)"""
        user_key = normalize_user_key(member)
        if user_key not in self.data["personnel"]:
            await ctx.send(f"{member.mention} is not in personnel database.")
            return
        self.ensure_unit_exists(new_unit)
        old_unit = self.data["personnel"][user_key]["unit"]
        if old_unit in self.data["units"]:
            if user_key in self.data["units"][old_unit]["personnel"]:
                self.data["units"][old_unit]["personnel"].remove(user_key)
        self.data["personnel"][user_key]["unit"] = new_unit
        self.data["units"][new_unit]["personnel"].append(user_key)
        self.save()
        await ctx.send(f"Transferred {member.mention} to unit '{new_unit}'.")

    @app_commands.command(name="transfer", description="Transfer a person to a different unit")
    async def transfer_slash(self, interaction: discord.Interaction, member: discord.Member, new_unit: str):
        user_key = normalize_user_key(member)
        if user_key not in self.data["personnel"]:
            await interaction.response.send_message(f"{member.mention} is not in personnel database.", ephemeral=True)
            return
        self.ensure_unit_exists(new_unit)
        old_unit = self.data["personnel"][user_key]["unit"]
        if old_unit in self.data["units"]:
            if user_key in self.data["units"][old_unit]["personnel"]:
                self.data["units"][old_unit]["personnel"].remove(user_key)
        self.data["personnel"][user_key]["unit"] = new_unit
        self.data["units"][new_unit]["personnel"].append(user_key)
        self.save()
        await interaction.response.send_message(f"Transferred {member.mention} to unit '{new_unit}'.")

    @commands.command(name="viewperson")
    async def view_person_cmd(self, ctx, member: discord.Member):
        """View a person's details"""
        user_key = normalize_user_key(member)
        if user_key not in self.data["personnel"]:
            await ctx.send(f"{member.mention} is not in personnel database.")
            return
        info = self.data["personnel"][user_key]
        await ctx.send(f"**{member}**\nRank: {info['rank']}\nUnit: {info['unit']}")

    @app_commands.command(name="viewperson", description="View a person's details")
    async def view_person_slash(self, interaction: discord.Interaction, member: discord.Member):
        user_key = normalize_user_key(member)
        if user_key not in self.data["personnel"]:
            await interaction.response.send_message(f"{member.mention} is not in personnel database.", ephemeral=True)
            return
        info = self.data["personnel"][user_key]
        await interaction.response.send_message(f"**{member}**\nRank: {info['rank']}\nUnit: {info['unit']}")

    # ======= UNIT COMMANDS =======

    @commands.command(name="createunit")
    async def create_unit_cmd(self, ctx, unit_name: str, troop_count: int = 0):
        """Create a unit with optional fictional troop count"""
        if unit_name in self.data["units"]:
            await ctx.send(f"Unit '{unit_name}' already exists.")
            return
        self.data["units"][unit_name] = {
            "troop_count": troop_count,
            "personnel": []
        }
        self.save()
        await ctx.send(f"Created unit '{unit_name}' with troop count {troop_count}.")

    @app_commands.command(name="createunit", description="Create a unit with optional troop count")
    async def create_unit_slash(self, interaction: discord.Interaction, unit_name: str, troop_count: int = 0):
        if unit_name in self.data["units"]:
            await interaction.response.send_message(f"Unit '{unit_name}' already exists.", ephemeral=True)
            return
        self.data["units"][unit_name] = {
            "troop_count": troop_count,
            "personnel": []
        }
        self.save()
        await interaction.response.send_message(f"Created unit '{unit_name}' with troop count {troop_count}.")

    @commands.command(name="removeunit")
    async def remove_unit_cmd(self, ctx, unit_name: str):
        """Remove a unit only if empty"""
        if unit_name not in self.data["units"]:
            await ctx.send(f"Unit '{unit_name}' does not exist.")
            return
        if self.data["units"][unit_name]["personnel"]:
            await ctx.send(f"Unit '{unit_name}' is not empty. Remove personnel first.")
            return
        del self.data["units"][unit_name]
        self.save()
        await ctx.send(f"Removed unit '{unit_name}'.")

    @app_commands.command(name="removeunit", description="Remove a unit if empty")
    async def remove_unit_slash(self, interaction: discord.Interaction, unit_name: str):
        if unit_name not in self.data["units"]:
            await interaction.response.send_message(f"Unit '{unit_name}' does not exist.", ephemeral=True)
            return
        if self.data["units"][unit_name]["personnel"]:
            await interaction.response.send_message(f"Unit '{unit_name}' is not empty. Remove personnel first.", ephemeral=True)
            return
        del self.data["units"][unit_name]
        self.save()
        await interaction.response.send_message(f"Removed unit '{unit_name}'.")

    @commands.command(name="addtroops")
    async def add_troops_cmd(self, ctx, unit_name: str, amount: int):
        """Add fictional troop count to a unit"""
        if unit_name not in self.data["units"]:
            await ctx.send(f"Unit '{unit_name}' does not exist.")
            return
        self.data["units"][unit_name]["troop_count"] += amount
        self.save()
        await ctx.send(f"Added {amount} troops to '{unit_name}'. Total troops now: {self.data['units'][unit_name]['troop_count']}")

    @app_commands.command(name="addtroops", description="Add fictional troop count to a unit")
    async def add_troops_slash(self, interaction: discord.Interaction, unit_name: str, amount: int):
        if unit_name not in self.data["units"]:
            await interaction.response.send_message(f"Unit '{unit_name}' does not exist.", ephemeral=True)
            return
        self.data["units"][unit_name]["troop_count"] += amount
        self.save()
        await interaction.response.send_message(f"Added {amount} troops to '{unit_name}'. Total troops now: {self.data['units'][unit_name]['troop_count']}")

    @commands.command(name="removetroops")
    async def remove_troops_cmd(self, ctx, unit_name: str, amount: int):
        """Remove fictional troops from a unit"""
        if unit_name not in self.data["units"]:
            await ctx.send(f"Unit '{unit_name}' does not exist.")
            return
        current = self.data["units"][unit_name]["troop_count"]
        new_count = max(0, current - amount)
        self.data["units"][unit_name]["troop_count"] = new_count
        self.save()
        await ctx.send(f"Removed {amount} troops from '{unit_name}'. Total troops now: {new_count}")

    @app_commands.command(name="removetroops", description="Remove fictional troops from a unit")
    async def remove_troops_slash(self, interaction: discord.Interaction, unit_name: str, amount: int):
        if unit_name not in self.data["units"]:
            await interaction.response.send_message(f"Unit '{unit_name}' does not exist.", ephemeral=True)
            return
        current = self.data["units"][unit_name]["troop_count"]
        new_count = max(0, current - amount)
        self.data["units"][unit_name]["troop_count"] = new_count
        self.save()
        await interaction.response.send_message(f"Removed {amount} troops from '{unit_name}'. Total troops now: {new_count}")

    @commands.command(name="viewunit")
    async def view_unit_cmd(self, ctx, *, unit_name: str):
        """View unit details and personnel list"""
        if unit_name not in self.data["units"]:
            await ctx.send(f"Unit '{unit_name}' does not exist.")
            return
        unit = self.data["units"][unit_name]
        troop_count = unit["troop_count"]
        personnel_list = unit["personnel"]

        if personnel_list:
            desc = ""
            for user_key in personnel_list:
                person = self.data["personnel"].get(user_key)
                if person:
                    desc += f"- {person['name']} ({person['rank']})\n"
                else:
                    desc += f"- Unknown user ID {user_key}\n"
        else:
            desc = "No personnel assigned."

        embed = discord.Embed(title=f"Unit: {unit_name}", description=desc, color=discord.Color.blue())
        embed.add_field(name="Troop Count (fictional)", value=str(troop_count))
        await ctx.send(embed=embed)

    @app_commands.command(name="viewunit", description="View unit details and personnel list")
    async def view_unit_slash(self, interaction: discord.Interaction, unit_name: str):
        if unit_name not in self.data["units"]:
            await interaction.response.send_message(f"Unit '{unit_name}' does not exist.", ephemeral=True)
            return
        unit = self.data["units"][unit_name]
        troop_count = unit["troop_count"]
        personnel_list = unit["personnel"]

        if personnel_list:
            desc = ""
            for user_key in personnel_list:
                person = self.data["personnel"].get(user_key)
                if person:
                    desc += f"- {person['name']} ({person['rank']})\n"
                else:
                    desc += f"- Unknown user ID {user_key}\n"
        else:
            desc = "No personnel assigned."

        embed = discord.Embed(title=f"Unit: {unit_name}", description=desc, color=discord.Color.blue())
        embed.add_field(name="Troop Count (fictional)", value=str(troop_count))
        await interaction.response.send_message(embed=embed)

    @commands.command(name="listunits")
    async def list_units_cmd(self, ctx):
        """List all units with troop counts"""
        if not self.data["units"]:
            await ctx.send("No units created yet.")
            return
        desc = ""
        for unit_name, info in self.data["units"].items():
            desc += f"**{unit_name}** - Troops: {info['troop_count']} - Personnel: {len(info['personnel'])}\n"
        await ctx.send(desc)

    @app_commands.command(name="listunits", description="List all units with troop counts")
    async def list_units_slash(self, interaction: discord.Interaction):
        if not self.data["units"]:
            await interaction.response.send_message("No units created yet.", ephemeral=True)
            return
        desc = ""
        for unit_name, info in self.data["units"].items():
            desc += f"**{unit_name}** - Troops: {info['troop_count']} - Personnel: {len(info['personnel'])}\n"
        await interaction.response.send_message(desc)

    @commands.command(name="listpersonnel")
    async def list_personnel_cmd(self, ctx):
        """List all personnel with rank and unit"""
        if not self.data["personnel"]:
            await ctx.send("No personnel added yet.")
            return
        desc = ""
        for user_key, info in self.data["personnel"].items():
            desc += f"{info['name']} - Rank: {info['rank']} - Unit: {info['unit']}\n"
        await ctx.send(desc)

    @app_commands.command(name="listpersonnel", description="List all personnel with rank and unit")
    async def list_personnel_slash(self, interaction: discord.Interaction):
        if not self.data["personnel"]:
            await interaction.response.send_message("No personnel added yet.", ephemeral=True)
            return
        desc = ""
        for user_key, info in self.data["personnel"].items():
            desc += f"{info['name']} - Rank: {info['rank']} - Unit: {info['unit']}\n"
        await interaction.response.send_message(desc)

async def setup(bot):
    await bot.add_cog(PersonnelUnits(bot))
