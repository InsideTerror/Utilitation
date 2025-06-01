import discord
from discord.ext import commands
from discord import app_commands
import os

intents = discord.Intents.default()
intents.message_content = True  # enable if you want message content, slash commands don't require it

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Load cogs
COGS = [
    "cogs.military_resources",
    "cogs.military_documents",
    "cogs.personnel_db"
]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"Loaded cog: {cog}")
        except Exception as e:
            print(f"Failed to load cog {cog}: {e}")

@bot.event
async def on_connect():
    await load_cogs()

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN environment variable not set.")
        exit(1)
    bot.run(TOKEN)
