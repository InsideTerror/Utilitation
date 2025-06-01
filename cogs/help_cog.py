import discord
from discord.ext import commands
from discord import app_commands

def get_bot_commands_embed():
    embed = discord.Embed(
        title="🛡️ Halberd Institution RP Bot — Command Guide",
        description=(
            "Welcome to the Halberd RP Bot! Below are the main commands organized by category.\n"
            "**Note:** Some commands require specific roles. Responses are ephemeral."
        ),
        color=0x0055AA
    )

    embed.add_field(
        name="🔰 Military Resource Management",
        value=(
            "`/resources_view [unit]`\nView resource counts for a unit or all.\n\n"
            "`/resources_allocate <type> <amount> <unit>`\nAllocate resources to a unit (auto-creates unit).\n\n"
            "`/resources_consume <type> <amount> <operation>`\nConsume resources for an operation.\n\n"
            "`/resources_transfer <type> <amount> <to_unit>`\nTransfer resources between units."
        ),
        inline=False
    )

    embed.add_field(
        name="📜 Military IC Document Generator",
        value=(
            "`/order_new <type> <subject> <details> <target_unit>`\nCreate new military orders.\n\n"
            "`/report_submit <type> <operation_name> <summary>`\nSubmit after-action reports.\n\n"
            "`/fine_issue <unit> <offense> <amount> [notes]`\nIssue disciplinary fines."
        ),
        inline=False
    )

    embed.add_field(
        name="👥 Personnel Management",
        value=(
            "`/personnel_add <name> <rank> <unit> <status>`\nAdd new personnel.\n\n"
            "`/personnel_update <name> <field> <value>`\nUpdate personnel records.\n\n"
            "`/personnel_view <name>`\nView personnel details.\n\n"
            "`/personnel_list [filter_by] [filter_value]`\nList personnel, optionally filtered."
        ),
        inline=False
    )

    embed.add_field(
        name="ℹ️ Notes",
        value=(
            "- Role restrictions apply: Commander, Officer, Quartermaster, HR, etc.\n"
            "- Data is saved persistently.\n"
            "- Commands respond with ephemeral messages.\n"
            "- Units are auto-created upon resource allocation.\n"
        ),
        inline=False
    )

    return embed

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help_bot", description="Show the bot command guide")
    async def help_bot(self, interaction: discord.Interaction):
        embed = get_bot_commands_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
