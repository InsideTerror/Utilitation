import discord
from discord.ext import commands
import os
from utils.file_io import load_json, save_json

DATA_PATH = "data/personnel_units.json"

class PersonnelUnits(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = load_json(DATA_PATH)

    def save(self):
        save_json(DATA_PATH, self.db)

    @commands.command(name="add_person")
    async def add_person(self, ctx, member: discord.Member, rank: str, unit: str):
        user_id = str(member.id)
        self.db.setdefault("users", {})[user_id] = {
            "name": member.name,
            "rank": rank,
            "unit": unit,
            "discord_id": member.id
        }
        self.db.setdefault("units", {}).setdefault(unit, {
            "type": "Unit",
            "members": [],
            "size": 0
        })
        if user_id not in self.db["units"][unit]["members"]:
            self.db["units"][unit]["members"].append(user_id)
            self.db["units"][unit]["size"] += 1
        self.save()
        await ctx.send(f"Added {member.mention} as {rank} in {unit}.")
