import discord
from discord.ext import commands
from discord import app_commands
from utils.permissions import is_authorized_prefix, is_authorized_slash

class MilitaryDocuments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.documents = {}  # {title: content}

    @commands.command(name="create_document")
    @is_authorized_prefix()
    async def create_document_cmd(self, ctx, title: str, *, content: str):
        self.documents[title] = content
        await ctx.send(f"Document '{title}' created.")

    @app_commands.command(name="createdocument", description="Create a military document")
    async def create_document_slash(self, interaction: discord.Interaction, title: str, content: str):
        if not await is_authorized_prefix(interaction.user):
            await interaction.response.send_message("You are not authorized.", ephemeral=True)
            return
        self.documents[title] = content
        await interaction.response.send_message(f"Document '{title}' created.")

    @commands.command(name="view_document")
    async def view_document_cmd(self, ctx, title: str):
        content = self.documents.get(title)
        if content:
            await ctx.send(f"**{title}**\n{content}")
        else:
            await ctx.send("Document not found.")

    @app_commands.command(name="viewdocument", description="View a military document")
    async def view_document_slash(self, interaction: discord.Interaction, title: str):
        content = self.documents.get(title)
        if content:
            await interaction.response.send_message(f"**{title}**\n{content}")
        else:
            await interaction.response.send_message("Document not found.", ephemeral=True)

    @commands.command(name="list_documents")
    async def list_documents_cmd(self, ctx):
        if not self.documents:
            await ctx.send("No documents.")
        else:
            await ctx.send("Documents:\n" + "\n".join(self.documents.keys()))

    @app_commands.command(name="listdocuments", description="List all military documents")
    async def list_documents_slash(self, interaction: discord.Interaction):
        if not self.documents:
            await interaction.response.send_message("No documents.")
        else:
            await interaction.response.send_message("Documents:\n" + "\n".join(self.documents.keys()))

async def setup(bot):
    await bot.add_cog(MilitaryDocuments(bot))
