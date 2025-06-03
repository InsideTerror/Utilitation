import discord
from discord.ext import commands

AUTHORIZED_ROLE_NAMES = ["High Command", "Admin", "General"]  # Customize as needed

# Check if user has an authorized role
def has_required_role(member: discord.Member) -> bool:
    return any(role.name in AUTHORIZED_ROLE_NAMES for role in member.roles)

# ✅ Prefix (!) command decorator
def is_authorized_prefix():
    def predicate(ctx: commands.Context):
        return has_required_role(ctx.author)
    return commands.check(predicate)

# ✅ Slash (/) command permission check
async def is_authorized_slash(user: discord.User | discord.Member) -> bool:
    if isinstance(user, discord.User):
        return False  # User has no roles
    return has_required_role(user)
