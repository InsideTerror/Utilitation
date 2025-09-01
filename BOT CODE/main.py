import discord
from discord.ext import commands
import aiohttp
import asyncio
import threading
import os

# ====== TOKENS ======
MAIN_BOT_TOKEN = "No"
PUPPET_BOT_TOKEN = "nuh,uh"

# ====== MAIN BOT SETUP ======
main_intents = discord.Intents.default()
main_intents.guilds = True
main_intents.guild_messages = True
main_intents.message_content = True

main_bot = commands.Bot(command_prefix="!", intents=main_intents)

@main_bot.event
async def on_ready():
    print(f"✅ Main Bot Logged in as {main_bot.user}")

# Load all cogs from cogs folder
@main_bot.event
async def setup_hook():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await main_bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Loaded cog: {filename}")
            except Exception as e:
                print(f"❌ Failed to load cog {filename}: {e}")

    try:
        synced = await main_bot.tree.sync()
        print(f"🔁 Synced {len(synced)} global slash commands.")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

# ====== STRUCTURE IMPORT COMMAND ======
@main_bot.command()
@commands.has_permissions(administrator=True)
async def importjson(ctx, url: str):
    await ctx.send("📥 Downloading structure file...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return await ctx.send("❌ Failed to fetch the file.")
                data = await resp.json()
    except Exception as e:
        return await ctx.send(f"❌ Error loading file: `{e}`")

    guild = ctx.guild

    # === Roles ===
    for role_info in data.get("roles", []):
        name = role_info.get("name")
        color = int(role_info.get("color", "0xffffff").replace("#", "0x"), 16)
        permissions_list = role_info.get("permissions", [])

        perms = discord.Permissions.none()
        for p in permissions_list:
            if hasattr(perms, p):
                setattr(perms, p, True)

        if discord.utils.get(guild.roles, name=name):
            await ctx.send(f"⚠️ Role `{name}` already exists, skipping.")
            continue

        try:
            await guild.create_role(name=name, color=discord.Color(color), permissions=perms)
            await asyncio.sleep(1)
            await ctx.send(f"✅ Created role: `{name}`")
        except Exception as e:
            await ctx.send(f"❌ Failed to create role `{name}`: {e}")

    # === Categories and Channels ===
    for cat_info in data.get("categories", []):
        cat_name = cat_info.get("name")
        category = discord.utils.get(guild.categories, name=cat_name)
        if not category:
            category = await guild.create_category(name=cat_name)
            await ctx.send(f"📁 Created category: `{cat_name}`")
            await asyncio.sleep(1)

        for channel_info in cat_info.get("channels", []):
            chan_name = channel_info.get("name")
            chan_type = channel_info.get("type", "text")
            existing = discord.utils.get(category.channels, name=chan_name)
            if existing:
                await ctx.send(f"⚠️ Channel `{chan_name}` already exists, skipping.")
                continue

            try:
                if chan_type == "text":
                    await guild.create_text_channel(name=chan_name, category=category)
                elif chan_type == "voice":
                    await guild.create_voice_channel(name=chan_name, category=category)
                await ctx.send(f"📨 Created channel: `{chan_name}`")
                await asyncio.sleep(1)
            except Exception as e:
                await ctx.send(f"❌ Error creating channel `{chan_name}`: {e}")

# ====== PUPPET BOT SETUP ======
puppet_intents = discord.Intents.default()
puppet_intents.message_content = True
puppet_intents.guilds = True
puppet_intents.messages = True

puppet_bot = discord.Client(intents=puppet_intents)

@puppet_bot.event
async def on_ready():
    print(f"🤖 Puppet Bot Logged in as {puppet_bot.user}")

@puppet_bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("<<"):
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

# ====== THREADING RUNNER ======
def run_puppet():
    asyncio.run(puppet_bot.start(PUPPET_BOT_TOKEN))

threading.Thread(target=run_puppet, name="PuppetBotThread", daemon=True).start()

# ====== START MAIN BOT ======
async def main():
    await main_bot.start(MAIN_BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
