import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio

# Load environment variables from .env
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not found. Please set it in your .env file.")

intents = discord.Intents.default()
intents.message_content = True  # Enable if your bot needs to read message content

bot = commands.Bot(command_prefix="/", intents=intents)

# List all your cog extensions here
COGS = [
    "cogs.military_resources",
    "cogs.military_documents",
    "cogs.personnel_db",
    "cogs.help_cog"
]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    # Sync all slash commands globally (can be adjusted per guild for faster updates)
    await bot.tree.sync()
    print("Slash commands synced.")

async def load_all_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"Loaded cog: {cog}")
        except Exception as e:
            print(f"Failed to load cog {cog}: {e}")

async def main():
    async with bot:
        await load_all_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
