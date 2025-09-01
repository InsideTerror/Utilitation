import discord
from discord.ext import commands, tasks
import asyncio

# Replace this with your Utilitation 2 bot token
SECONDARY_BOT_TOKEN = "sorry, no API keys for you today"

# Intents for secondary bot
puppet_intents = discord.Intents.default()
puppet_intents.message_content = True
puppet_intents.guilds = True
puppet_intents.messages = True

# Secondary client (Utilitation 2)
puppet_bot = discord.Client(intents=puppet_intents)

class PuppetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_puppet_bot.start()

    def cog_unload(self):
        self.start_puppet_bot.cancel()

    @tasks.loop(count=1)
    async def start_puppet_bot(self):
        # Run puppet_bot in a background thread
        loop = asyncio.get_event_loop()
        loop.create_task(puppet_bot.start(SECONDARY_BOT_TOKEN))

    @start_puppet_bot.before_loop
    async def before_start(self):
        await self.bot.wait_until_ready()

# Message handling for the secondary bot
@puppet_bot.event
async def on_ready():
    print(f"🤖 Utilitation 2 (puppet) ready as {puppet_bot.user}")

@puppet_bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith(">>"):
        new_content = message.content[2:].lstrip()

        try:
            await message.delete()
        except discord.Forbidden:
            print(f"❌ Can't delete message in {message.channel}")
        except discord.HTTPException as e:
            print(f"❌ Failed to delete message: {e}")

        try:
            await message.channel.send(new_content)
        except Exception as e:
            print(f"❌ Failed to resend message: {e}")

# Setup for main bot to load the cog
async def setup(bot):
    await bot.add_cog(PuppetCog(bot))
