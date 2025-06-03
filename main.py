import discord
from discord.ext import commands
import asyncio
import os

# You can set your token here directly if fps.ms keeps it secure
TOKEN = "NOT HERE_HEHEHEHEHEHEHE"  # <- Replace with your real token

# Set up intents
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.members = True

# Both slash (application) and prefix command support
bot = commands.Bot(command_prefix="!", intents=intents)

bot.remove_command("help")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("🔁 Syncing slash commands...")
    synced = await bot.tree.sync()
    print(f"✅ Synced {len(synced)} global slash commands.")
    print("🟢 Bot is ready.")

async def load_extensions():
    extensions = [
        "cogs.help_cog",
        "cogs.military_documents",
        "cogs.military_resources",
        "cogs.personnel_units",
        "cogs.resource_assignment",
    ]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Loaded extension: {ext}")
        except Exception as e:
            print(f"❌ Failed to load extension {ext}: {e}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
