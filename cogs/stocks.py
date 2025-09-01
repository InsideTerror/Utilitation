import asyncio
import random
import sqlite3
from contextlib import closing
from typing import Optional, Tuple, List

import discord
from discord import app_commands
from discord.ext import commands, tasks

# ============================
# Config
# ============================
DB_PATH = "data/stocks.sqlite3"  # Keep it small & local
PRICE_TICK_SECONDS = 600          # 10 minutes between market ticks
DAILY_DRIFT_PCT = 0.01            # Small mean reversion drift (1%)
MAX_JITTER_PCT = 0.05             # Max +/- 5% move per tick
MIN_PRICE = 1.0                   # Floor to avoid zero/negative prices

# Note on resource limits:
# - Uses only sqlite3 and small background loop.
# - No in-memory caches for large datasets; queries are on-demand.
# - Table schemas are minimal.


# ============================
# Helper / DB layer
# ============================
class StockDB:
    def __init__(self, path: str):
        self.path = path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _init_db(self):
        with self._connect() as con:
            cur = con.cursor()
            # Companies
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    price REAL NOT NULL
                );
                """
            )
            # Holdings
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS holdings (
                    user_id INTEGER NOT NULL,
                    company_id INTEGER NOT NULL,
                    shares INTEGER NOT NULL,
                    PRIMARY KEY (user_id, company_id),
                    FOREIGN KEY(company_id) REFERENCES companies(id)
                );
                """
            )
            # Balances (self-contained currency for trading)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS balances (
                    user_id INTEGER PRIMARY KEY,
                    balance REAL NOT NULL
                );
                """
            )
            # Simple price history (optional, trimmed)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS price_history (
                    company_id INTEGER NOT NULL,
                    ts INTEGER NOT NULL,
                    price REAL NOT NULL
                );
                """
            )
            con.commit()

    # ---------- Companies ----------
    def add_company(self, name: str, price: float) -> int:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("INSERT INTO companies (name, price) VALUES (?, ?)", (name, price))
            con.commit()
            return cur.lastrowid

    def remove_company(self, name: str) -> bool:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT id FROM companies WHERE name = ?", (name,))
            row = cur.fetchone()
            if not row:
                return False
            company_id = row[0]
            cur.execute("DELETE FROM holdings WHERE company_id = ?", (company_id,))
            cur.execute("DELETE FROM companies WHERE id = ?", (company_id,))
            con.commit()
            return True

    def set_price(self, name: str, price: float) -> bool:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("UPDATE companies SET price = ? WHERE name = ?", (price, name))
            con.commit()
            return cur.rowcount > 0

    def get_company(self, name: str) -> Optional[Tuple[int, str, float]]:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT id, name, price FROM companies WHERE name = ?", (name,))
            row = cur.fetchone()
            return row if row else None

    def list_companies(self) -> List[Tuple[int, str, float]]:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT id, name, price FROM companies ORDER BY name COLLATE NOCASE")
            return cur.fetchall()

    def update_price_by_id(self, company_id: int, new_price: float):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("UPDATE companies SET price = ? WHERE id = ?", (new_price, company_id))
            # Add history sample (keep table small by allowing it to be pruned externally if needed)
            cur.execute("INSERT INTO price_history (company_id, ts, price) VALUES (?, strftime('%s','now'), ?)", (company_id, new_price))
            con.commit()

    # ---------- Balances ----------
    def get_balance(self, user_id: int) -> float:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT balance FROM balances WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return float(row[0]) if row else 0.0

    def set_balance(self, user_id: int, new_balance: float):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO balances (user_id, balance) VALUES (?, ?)\n                 ON CONFLICT(user_id) DO UPDATE SET balance = excluded.balance",
                (user_id, new_balance),
            )
            con.commit()

    def add_balance(self, user_id: int, delta: float) -> float:
        bal = self.get_balance(user_id)
        bal += delta
        if bal < 0:
            raise ValueError("Insufficient funds")
        self.set_balance(user_id, bal)
        return bal

    # ---------- Holdings ----------
    def get_shares(self, user_id: int, company_id: int) -> int:
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT shares FROM holdings WHERE user_id = ? AND company_id = ?",
                (user_id, company_id),
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0

    def set_shares(self, user_id: int, company_id: int, shares: int):
        with self._connect() as con:
            cur = con.cursor()
            if shares <= 0:
                cur.execute(
                    "DELETE FROM holdings WHERE user_id = ? AND company_id = ?",
                    (user_id, company_id),
                )
            else:
                cur.execute(
                    "INSERT INTO holdings (user_id, company_id, shares) VALUES (?, ?, ?)\n                     ON CONFLICT(user_id, company_id) DO UPDATE SET shares = excluded.shares",
                    (user_id, company_id, shares),
                )
            con.commit()

    def get_portfolio(self, user_id: int) -> List[Tuple[str, int, float]]:
        """Returns list of (company_name, shares, current_price)."""
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT c.name, h.shares, c.price
                FROM holdings h
                JOIN companies c ON c.id = h.company_id
                WHERE h.user_id = ? AND h.shares > 0
                ORDER BY c.name COLLATE NOCASE
                """,
                (user_id,),
            )
            return cur.fetchall()


# ============================
# Cog
# ============================
class Stocks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = StockDB(DB_PATH)
        self.market_tick.start()

    def cog_unload(self):
        self.market_tick.cancel()

    # --------------------------
    # Background price simulation
    # --------------------------
    @tasks.loop(seconds=PRICE_TICK_SECONDS)
    async def market_tick(self):
        # Random, bounded jitter with a slight drift upward to keep activity interesting
        companies = self.db.list_companies()
        for cid, name, price in companies:
            if price <= 0:
                price = MIN_PRICE
            jitter = random.uniform(-MAX_JITTER_PCT, MAX_JITTER_PCT)
            drift = DAILY_DRIFT_PCT * (random.random() - 0.5)  # centered around 0
            new_price = max(MIN_PRICE, round(price * (1 + jitter + drift), 2))
            self.db.update_price_by_id(cid, new_price)
        # Avoid spamming logs; this loop is intentionally quiet.

    @market_tick.before_loop
    async def before_tick(self):
        await self.bot.wait_until_ready()

    # ============================
    # Utilities
    # ============================
    async def _ensure_company(self, name: str) -> Tuple[int, str, float]:
        row = self.db.get_company(name)
        if not row:
            raise commands.UserInputError(f"Company '{name}' does not exist.")
        return row

    # ============================
    # Admin Commands
    # ============================
    def admin_check():
        def predicate(ctx: commands.Context):
            # Manage Guild is a safe default for admin-like actions
            return ctx.author.guild_permissions.manage_guild
        return commands.check(predicate)

    @commands.command(name="addstock")
    @admin_check()
    async def addstock_prefix(self, ctx: commands.Context, name: str, initial_price: float):
        """Create a fictional company. Example: !addstock Halberd_Arms 100"""
        try:
            self.db.add_company(name, round(float(initial_price), 2))
            await ctx.reply(f"✅ Company **{name}** listed at **{round(float(initial_price), 2):.2f}**.")
        except sqlite3.IntegrityError:
            await ctx.reply("❌ A company with that name already exists.")

    @app_commands.command(name="addstock", description="Create a fictional company")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def addstock_slash(self, interaction: discord.Interaction, name: str, initial_price: float):
        try:
            self.db.add_company(name, round(float(initial_price), 2))
            await interaction.response.send_message(
                f"✅ Company **{name}** listed at **{round(float(initial_price), 2):.2f}**.",
                ephemeral=True,
            )
        except sqlite3.IntegrityError:
            await interaction.response.send_message("❌ A company with that name already exists.", ephemeral=True)

    @commands.command(name="removestock")
    @admin_check()
    async def removestock_prefix(self, ctx: commands.Context, name: str):
        ok = self.db.remove_company(name)
        if ok:
            await ctx.reply(f"🗑️ Company **{name}** delisted and holdings cleared.")
        else:
            await ctx.reply("❌ Company not found.")

    @app_commands.command(name="removestock", description="Remove a fictional company")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def removestock_slash(self, interaction: discord.Interaction, name: str):
        ok = self.db.remove_company(name)
        if ok:
            await interaction.response.send_message(
                f"🗑️ Company **{name}** delisted and holdings cleared.", ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ Company not found.", ephemeral=True)

    @commands.command(name="setprice")
    @admin_check()
    async def setprice_prefix(self, ctx: commands.Context, name: str, new_price: float):
        new_price = round(float(new_price), 2)
        ok = self.db.set_price(name, new_price)
        if ok:
            await ctx.reply(f"🔧 **{name}** price set to **{new_price:.2f}**.")
        else:
            await ctx.reply("❌ Company not found.")

    @app_commands.command(name="setprice", description="Manually set a stock price")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setprice_slash(self, interaction: discord.Interaction, name: str, new_price: float):
        new_price = round(float(new_price), 2)
        ok = self.db.set_price(name, new_price)
        if ok:
            await interaction.response.send_message(
                f"🔧 **{name}** price set to **{new_price:.2f}**.", ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ Company not found.", ephemeral=True)

    @commands.command(name="fund")
    @admin_check()
    async def fund_prefix(self, ctx: commands.Context, member: discord.Member, amount: float):
        amount = round(float(amount), 2)
        if amount <= 0:
            return await ctx.reply("Amount must be positive.")
        new_bal = self.db.add_balance(member.id, amount)
        await ctx.reply(f"💰 Funded {member.mention}: +{amount:.2f} (balance {new_bal:.2f})")

    @app_commands.command(name="fund", description="Credit a user's trading balance")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def fund_slash(self, interaction: discord.Interaction, member: discord.Member, amount: float):
        amount = round(float(amount), 2)
        if amount <= 0:
            return await interaction.response.send_message("Amount must be positive.", ephemeral=True)
        new_bal = self.db.add_balance(member.id, amount)
        await interaction.response.send_message(
            f"💰 Funded {member.mention}: +{amount:.2f} (balance {new_bal:.2f})",
            ephemeral=True,
        )

    @commands.command(name="defund")
    @admin_check()
    async def defund_prefix(self, ctx: commands.Context, member: discord.Member, amount: float):
        amount = round(float(amount), 2)
        if amount <= 0:
            return await ctx.reply("Amount must be positive.")
        try:
            new_bal = self.db.add_balance(member.id, -amount)
        except ValueError:
            return await ctx.reply("❌ Insufficient funds to remove.")
        await ctx.reply(f"🧾 Removed funds from {member.mention}: -{amount:.2f} (balance {new_bal:.2f})")

    @app_commands.command(name="defund", description="Debit a user's trading balance")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def defund_slash(self, interaction: discord.Interaction, member: discord.Member, amount: float):
        amount = round(float(amount), 2)
        if amount <= 0:
            return await interaction.response.send_message("Amount must be positive.", ephemeral=True)
        try:
            new_bal = self.db.add_balance(member.id, -amount)
        except ValueError:
            return await interaction.response.send_message("❌ Insufficient funds to remove.", ephemeral=True)
        await interaction.response.send_message(
            f"🧾 Removed funds from {member.mention}: -{amount:.2f} (balance {new_bal:.2f})",
            ephemeral=True,
        )

    # ============================
    # User Commands
    # ============================
    @commands.command(name="stocks")
    async def stocks_prefix(self, ctx: commands.Context):
        companies = self.db.list_companies()
        if not companies:
            return await ctx.reply("No companies listed yet. Admins can use !addstock.")
        embed = discord.Embed(title="📈 Fictional Market", color=discord.Color.blurple())
        for _id, name, price in companies:
            embed.add_field(name=name, value=f"{price:.2f}", inline=True)
        await ctx.reply(embed=embed)

    @app_commands.command(name="stocks", description="Show all companies and prices")
    async def stocks_slash(self, interaction: discord.Interaction):
        companies = self.db.list_companies()
        if not companies:
            return await interaction.response.send_message(
                "No companies listed yet. Admins can use /addstock.", ephemeral=True
            )
        embed = discord.Embed(title="📈 Fictional Market", color=discord.Color.blurple())
        for _id, name, price in companies:
            embed.add_field(name=name, value=f"{price:.2f}", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @commands.command(name="balance")
    async def balance_prefix(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        target = member or ctx.author
        bal = self.db.get_balance(target.id)
        await ctx.reply(f"{target.mention} balance: **{bal:.2f}**")

    @app_commands.command(name="balance", description="Show your (or another user's) trading balance")
    async def balance_slash(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        bal = self.db.get_balance(target.id)
        await interaction.response.send_message(f"{target.mention} balance: **{bal:.2f}**", ephemeral=True)

    @commands.command(name="buy")
    async def buy_prefix(self, ctx: commands.Context, company: str, shares: int):
        await self._buy(ctx, ctx.author, company, shares)

    @app_commands.command(name="buy", description="Buy shares of a company")
    async def buy_slash(self, interaction: discord.Interaction, company: str, shares: int):
        await self._buy(interaction, interaction.user, company, shares)

    async def _buy(self, origin, user: discord.User, company: str, shares: int):
        if shares <= 0:
            return await self._respond(origin, "Shares must be a positive integer.")
        try:
            cid, name, price = await self._ensure_company(company)
        except commands.UserInputError as e:
            return await self._respond(origin, str(e))

        cost = round(price * shares, 2)
        bal = self.db.get_balance(user.id)
        if bal < cost:
            return await self._respond(origin, f"❌ Not enough funds. Need {cost:.2f}, you have {bal:.2f}.")
        # Deduct & add shares atomically-ish (single thread event loop)
        self.db.add_balance(user.id, -cost)
        current = self.db.get_shares(user.id, cid)
        self.db.set_shares(user.id, cid, current + shares)
        await self._respond(origin, f"✅ Bought **{shares}** of **{name}** at {price:.2f} each (cost {cost:.2f}).")

    @commands.command(name="sell")
    async def sell_prefix(self, ctx: commands.Context, company: str, shares: int):
        await self._sell(ctx, ctx.author, company, shares)

    @app_commands.command(name="sell", description="Sell shares of a company")
    async def sell_slash(self, interaction: discord.Interaction, company: str, shares: int):
        await self._sell(interaction, interaction.user, company, shares)

    async def _sell(self, origin, user: discord.User, company: str, shares: int):
        if shares <= 0:
            return await self._respond(origin, "Shares must be a positive integer.")
        try:
            cid, name, price = await self._ensure_company(company)
        except commands.UserInputError as e:
            return await self._respond(origin, str(e))

        owned = self.db.get_shares(user.id, cid)
        if owned < shares:
            return await self._respond(origin, f"❌ You only own {owned} shares of {name}.")
        proceeds = round(price * shares, 2)
        self.db.set_shares(user.id, cid, owned - shares)
        self.db.add_balance(user.id, proceeds)
        await self._respond(origin, f"✅ Sold **{shares}** of **{name}** at {price:.2f} each (received {proceeds:.2f}).")

    @commands.command(name="portfolio")
    async def portfolio_prefix(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        target = member or ctx.author
        await self._portfolio(ctx, target)

    @app_commands.command(name="portfolio", description="Show your stock holdings")
    async def portfolio_slash(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        await self._portfolio(interaction, target)

    async def _portfolio(self, origin, user: discord.User):
        rows = self.db.get_portfolio(user.id)
        bal = self.db.get_balance(user.id)
        if not rows:
            return await self._respond(origin, f"{user.mention} has no holdings. Balance **{bal:.2f}**.")
        total_value = 0.0
        embed = discord.Embed(title=f"💼 Portfolio — {user.display_name}", color=discord.Color.green())
        for name, shares, price in rows:
            line_value = round(price * shares, 2)
            total_value += line_value
            embed.add_field(name=name, value=f"{shares} @ {price:.2f} = {line_value:.2f}", inline=False)
        embed.add_field(name="Balance", value=f"{bal:.2f}", inline=False)
        embed.add_field(name="Portfolio Value", value=f"{total_value:.2f}", inline=False)
        embed.add_field(name="Net Worth", value=f"{(total_value + bal):.2f}", inline=False)
        await self._respond(origin, embed=embed)

    # Small helper to respond either ctx or interaction
    async def _respond(self, origin, content: Optional[str] = None, *, embed: Optional[discord.Embed] = None):
        if isinstance(origin, commands.Context):
            if embed:
                return await origin.reply(embed=embed)
            return await origin.reply(content)
        elif isinstance(origin, discord.Interaction):
            if origin.response.is_done():
                # Followup to avoid double response errors
                if embed:
                    return await origin.followup.send(embed=embed, ephemeral=False)
                return await origin.followup.send(content, ephemeral=True)
            else:
                if embed:
                    return await origin.response.send_message(embed=embed, ephemeral=False)
                return await origin.response.send_message(content, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Stocks(bot))
