import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
from utils.permissions import is_authorized

DATA_PATH = "data/documents.json"
DOCUMENT_TYPES = ["Order", "Report", "Fine", "Transfer", "Disciplinary"]

def load_documents():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_documents(docs):
    with open(DATA_PATH, "w") as f:
        json.dump(docs, f, indent=4)

class MilitaryDocuments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.documents = load_documents()

    def save(self):
        save_documents(self.documents)

    @app_commands.command(name="document_issue", description="Issue a military document (order, report, fine, etc.)")
    async def issue_document(
        self,
        interaction: discord.Interaction,
        doc_type: str,
        title: str,
        summary: str,
        target_unit: str = "N/A"
    ):
        if not await is_authorized(interaction.user, ["Commander", "Officer"]):
            await interaction.response.send_message("You are not authorized to issue documents.", ephemeral=True)
            return

        doc_type = doc_type.capitalize()
        if doc_type not in DOCUMENT_TYPES:
            await interaction.response.send_message(f"Invalid document type. Must be one of: {', '.join(DOCUMENT_TYPES)}", ephemeral=True)
            return

        document = {
            "type": doc_type,
            "title": title,
            "summary": summary,
            "target_unit": target_unit,
            "issued_by": interaction.user.name,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.documents.append(document)
        self.save()

        embed = discord.Embed(title=f"{doc_type} - {title}", color=discord.Color.orange())
        embed.add_field(name="Summary", value=summary, inline=False)
        embed.add_field(name="Target Unit", value=target_unit, inline=True)
        embed.add_field(name="Issued By", value=interaction.user.name, inline=True)
        embed.set_footer(text=f"Issued on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(MilitaryDocuments(bot))
