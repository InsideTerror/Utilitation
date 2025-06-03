import discord
from discord.ext import commands
from discord import app_commands
import os
import datetime
from utils.file_io import load_json, save_json

DATA_PATH = "data/military_documents.json"

class MilitaryDocuments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.documents = load_json(DATA_PATH).get("documents", [])

    def save(self):
        save_json(DATA_PATH, {"documents": self.documents})

    # /create_document or !create_document
    @commands.command(name="create_document")
    async def create_document_prefix(self, ctx, title: str, *, content: str):
        doc = {
            "title": title,
            "author_id": str(ctx.author.id),
            "content": content,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        self.documents.append(doc)
        self.save()
        await ctx.send(f"📄 Document '{title}' created.")

    @app_commands.command(name="createdocument", description="Create a military document")
    async def create_document_slash(self, interaction: discord.Interaction, title: str, content: str):
        doc = {
            "title": title,
            "author_id": str(interaction.user.id),
            "content": content,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        self.documents.append(doc)
        self.save()
        await interaction.response.send_message(f"📄 Document '{title}' created.", ephemeral=True)

    # !view_documents
    @commands.command(name="view_documents")
    async def view_documents_prefix(self, ctx):
        if not self.documents:
            await ctx.send("No documents available.")
            return
        msg = "\n".join([f"- {doc['title']} (by <@{doc['author_id']}>)" for doc in self.documents])
        await ctx.send(f"📚 Documents:\n{msg}")

    @app_commands.command(name="viewdocuments", description="View all military documents")
    async def view_documents_slash(self, interaction: discord.Interaction):
        if not self.documents:
            await interaction.response.send_message("No documents available.", ephemeral=True)
            return
        msg = "\n".join([f"- {doc['title']} (by <@{doc['author_id']}>)" for doc in self.documents])
        await interaction.response.send_message(f"📚 Documents:\n{msg}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MilitaryDocuments(bot))
