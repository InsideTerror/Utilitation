import discord
from discord.ext import commands
import os
from utils.file_io import load_json, save_json

DATA_PATH = "data/resource_assignments.json"

class ResourceAssignment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.assignments = load_json(DATA_PATH)

    def save(self):
        save_json(DATA_PATH, self.assignments)

    @commands.command(name="assign_resource")
    async def assign_resource(self, ctx, unit: str, resource: str, quantity: int):
        self.assignments.setdefault(unit, {})
        self.assignments[unit][resource] = self.assignments[unit].get(resource, 0) + quantity
        self.save()
        await ctx.send(f"Assigned {quantity} of {resource} to {unit}.")
