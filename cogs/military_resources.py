import discord
from discord.ext import commands
import os
from utils.file_io import load_json, save_json

DATA_PATH = "data/military_resources.json"

class MilitaryResources(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.resources = load_json(DATA_PATH)

    def save(self):
        save_json(DATA_PATH, self.resources)

    @commands.command(name="add_resource")
    async def add_resource(self, ctx, name: str, quantity: int):
        self.resources[name] = self.resources.get(name, 0) + quantity
        self.save()
        await ctx.send(f"Added {quantity} of {name}. Total: {self.resources[name]}")

    @commands.command(name="remove_resource")
    async def remove_resource(self, ctx, name: str, quantity: int):
        if name in self.resources:
            self.resources[name] = max(self.resources[name] - quantity, 0)
            self.save()
            await ctx.send(f"Removed {quantity} of {name}. Remaining: {self.resources[name]}")
        else:
            await ctx.send(f"Resource {name} not found.")
