import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv
import os

import yfinanceMain as yfMain
from finBERTAIlogic import analyze_stock_headlines
from logicFile import investment_advice, graph_closing_prices



load_dotenv()
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
intents = discord.Intents.default()

intents.message_content = True
intents.members = True
#add more bot permissions if needed

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

@bot.command()
async def investor(ctx):
    role = discord.utils.get(ctx.guild.roles, name="Investor")
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"✅ {ctx.author.mention}, you are now an investor, escape the 9 to 5!")
    else:
        await ctx.send("⚠️ Investor role not found. Please contact an admin.")

@bot.command()
async def price(ctx, symbol):
    """Get the current market price of a stock."""
    stock_price = yfMain.get_stock_price(symbol.upper())
    if stock_price is not None:
        await ctx.send(f"The current price of {symbol.upper()} is ${stock_price}")
    else:
        await ctx.send(f"⚠️ Could not fetch price for {symbol.upper()}. Please check the symbol and try again.")
