import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv
import os
import random

import yfinanceMain as yfMain
import database as db
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
async def investor(ctx, starting_funds):
    role = discord.utils.get(ctx.guild.roles, name="Investor")
    if role:
        try:
            starting_funds = float(starting_funds)
            if starting_funds <= 0:
                await ctx.send(f"⚠️ {ctx.author.mention}, starting funds must be greater than 0.")
                return
            await ctx.author.add_roles(role)
            await ctx.send(f"✅ {ctx.author.mention}, you are now an investor, escape the 9 to 5!")
            db.add_user(ctx.author.id, ctx.author.name, starting_funds)
        except ValueError:
            await ctx.send(f"⚠️ {ctx.author.mention}, please provide a valid number for starting funds.")
    else:
        await ctx.send("⚠️ Investor role not found. Please contact an admin.")

@bot.command()
async def stop_grinding(ctx):
    role = discord.utils.get(ctx.guild.roles, name = "Investor")
    if role:
        if role not in ctx.author.roles:
            await ctx.send(f"⚠️ {ctx.author.mention}, you are not an investor.")
            return
        await ctx.author.remove_roles(role)
        await ctx.send(f"✅ {ctx.author.mention}, you are no longer an investor. Back to the trenches!")
        db.remove_user(ctx.author.id)
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

@bot.command()
@commands.has_role('Investor')
async def get_funds(ctx):
    try:
        funds = db.get_user_funds(ctx.author.id)
        if funds is not None:
            await ctx.send(f"💰 {ctx.author.mention}, your available funds are: ${funds}")
        else:
            await ctx.send(f" You are broke.")
    except Exception as e:
        await ctx.send(f"⚠️ Error fetching funds: {e}")

@get_funds.error
async def get_funds_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("⚠️ You need to be an Investor to use this command. Use /investor to get the role.")

@bot.command()
@commands.has_role('Investor')
async def finBERTsays(ctx, symbol):
    try:
        analysis = analyze_stock_headlines(symbol.upper())
        await ctx.send(f"FinBERT Analysis loading for {symbol.upper()}:\n{analysis}")
    except Exception as e:
        await ctx.send(f"⚠️ Error fetching FinBERT analysis for {symbol.upper()}: {e}")

@finBERTsays.error
async def finBERTsays_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("⚠️ You need to be an Investor to use this command. Use /investor to get the role.")

@bot.command()
@commands.has_role('Investor')
async def advice(ctx, symbol):
    try:
        advice_text = investment_advice(symbol.upper())
        await ctx.send(f"Investment Advice for {symbol.upper()}:\n{advice_text}")
    except Exception as e:
        await ctx.send(f"⚠️ Error fetching investment advice for {symbol.upper()}: {e}")

@advice.error
async def advice_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("⚠️ You need to be an Investor to use this command. Use /investor to get the role.")


@bot.command()
@commands.has_role('Investor')
async def graph(ctx, symbol):
    try:
        closing_prices, img_buffer = graph_closing_prices(symbol.upper())
        if img_buffer is None:
            await ctx.send("⚠️ Could not generate graph. Please check the symbol and try again.")
        else:
            await ctx.send(file=discord.File(img_buffer, filename="graph.png"))
    except Exception as e:
        await ctx.send(f"⚠️ Error generating graph for {symbol.upper()}: {e}")

@graph.error
async def graph_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("⚠️ You need to be an Investor to use this command. Use /investor to get the role.")

@bot.command()
@commands.has_role('Investor')
async def buy_shares(ctx, symbol: str, shares: float):
    try:
        current_price = yfMain.get_stock_price(symbol.upper())
        if current_price is None:
            await ctx.send(f"⚠️ Could not fetch price for {symbol.upper()}. Please check the symbol and try again.")
            return
        total_cost = current_price * shares
        user_funds = db.get_user_funds(ctx.author.id)
        if user_funds is None or user_funds < total_cost:
            await ctx.send(f"⚠️ Insufficient funds to buy {shares} shares of {symbol.upper()}. You need ${total_cost}, but have ${user_funds}.")
            return
        db.update_user_funds(ctx.author.id, user_funds - total_cost)
        db.add_to_portfolio(ctx.author.id, symbol.upper(), shares, current_price)
        db.log_trade(ctx.author.id, symbol.upper(), 'buy', shares, current_price)
        await ctx.send(f"✅ Successfully bought {shares} shares of {symbol.upper()} at ${current_price} per share for a total of ${total_cost}.")
    except Exception as e:
        await ctx.send(f"⚠️ Error buying shares for {symbol.upper()}: {e}")

@buy_shares.error
async def buy_shares_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("⚠️ You need to be an Investor to use this command. Use /investor to get the role.")

@bot.command()
@commands.has_role('Investor')
async def buy_dollars(ctx, symbol: str, dollars: float):
    try:
        current_price = yfMain.get_stock_price(symbol.upper())
        if current_price is None:
            await ctx.send(f"⚠️ Could not fetch price for {symbol.upper()}. Please check the symbol and try again.")
            return
        shares_to_buy = dollars / current_price
        user_funds = db.get_user_funds(ctx.author.id)
        if user_funds is None or user_funds < dollars:
            await ctx.send(f"⚠️ Insufficient funds to buy ${dollars} worth of {symbol.upper()}. You have ${user_funds}.")
            return
        db.update_user_funds(ctx.author.id, user_funds - dollars)
        db.add_to_portfolio(ctx.author.id, symbol.upper(), shares_to_buy, current_price)
        db.log_trade(ctx.author.id, symbol.upper(), 'buy', shares_to_buy, current_price)
        await ctx.send(f"✅ Successfully bought {shares_to_buy} shares of {symbol.upper()} at ${current_price} per share for a total of ${dollars}.")
    except Exception as e:
        await ctx.send(f"⚠️ Error buying shares for {symbol.upper()}: {e}")

@buy_dollars.error
async def buy_dollars_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("⚠️ You need to be an Investor to use this command. Use /investor to get the role.")

@bot.command()
@commands.has_role('Investor')
async def sell_shares(ctx, symbol: str, shares: float):
    try:
        current_price = yfMain.get_stock_price(symbol.upper())
        if current_price is None:
            await ctx.send(f"⚠️ Could not fetch price for {symbol.upper()}. Please check the symbol and try again.")
            return
        portfolio = db.get_portfolio(ctx.author.id)
        owned_shares = 0
        for sym, sh, entry_price, total_invested in portfolio:
            if sym == symbol.upper():
                owned_shares = sh
                break
        if owned_shares < shares:
            await ctx.send(f"⚠️ You do not own enough shares of {symbol.upper()} to sell {shares} shares. You own {owned_shares} shares.")
            return
        total_revenue = current_price * shares
        user_funds = db.get_user_funds(ctx.author.id)
        new_user_funds = user_funds + total_revenue
        db.update_user_funds(ctx.author.id, new_user_funds)
        db.sell_from_portfolio(ctx.author.id, symbol.upper(), shares, current_price)
        db.log_trade(ctx.author.id, symbol.upper(), 'sell', shares, current_price)
        await ctx.send(f"✅ Successfully sold {shares} shares of {symbol.upper()} at ${current_price} per share for a total of ${total_revenue}.")
    except Exception as e:
        await ctx.send(f"⚠️ Error selling shares for {symbol.upper()}: {e}")

@sell_shares.error
async def sell_shares_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("⚠️ You need to be an Investor to use this command. Use /investor to get the role.")

@bot.command()
@commands.has_role('Investor')
async def sell_dollars(ctx, symbol: str, dollars: float):
    try:
        ticker = symbol.upper()
        current_price = yfMain.get_stock_price(ticker)
        if current_price is None:
            await ctx.send(f"⚠️ Could not fetch price for {ticker}. Please check the symbol and try again.")
            return
        shares_to_sell = dollars /  current_price
        portfolio = db.get_portfolio(ctx.author.id)
        owned_shares = 0
        for sym, sh, entry_price, total_invested in portfolio:
            if sym == symbol.upper():
                owned_shares = sh
                break
        if owned_shares < shares_to_sell:
            await ctx.send(f"⚠️ You do not own enough shares of {ticker} to sell ${dollars} worth. You own {owned_shares} shares.")
            return
        total_revenue = current_price * shares_to_sell
        user_funds = db.get_user_funds(ctx.author.id)
        new_user_funds = user_funds + total_revenue
        db.update_user_funds(ctx.author.id, new_user_funds)
        db.sell_from_portfolio(ctx.author.id, ticker, shares_to_sell, current_price)
        db.log_trade(ctx.author.id, ticker, 'sell', shares_to_sell, current_price)
        await ctx.send(f"✅ Successfully sold {shares_to_sell} shares of {ticker} at ${current_price} per share for a total of ${total_revenue}.")
    except Exception as e:
        await ctx.send(f"⚠️ Error selling shares for {ticker}: {e}")

@sell_dollars.error
async def sell_dollars_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("⚠️ You need to be an Investor to use this command. Use /investor to get the role.")

@bot.command()
@commands.has_role('Investor')
async def portfolio(ctx):
    try:
        portfolio = db.get_portfolio(ctx.author.id)
        if not portfolio:
            await ctx.send(f"📂 {ctx.author.mention}, your portfolio is empty.")
            return
        message = f"📂 {ctx.author.mention}, your portfolio:\n"
        for symbol, shares, entry_price, total_invested in portfolio:
            message += f"- {symbol}: {shares} shares, Entry Price: ${round(entry_price, 2)}, Total Invested: ${round(total_invested, 2)}\n"
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"⚠️ Error fetching portfolio: {e}")

@portfolio.error
async def portfolio_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("⚠️ You need to be an Investor to use this command. Use /investor to get the role.")

@bot.command()
@commands.has_role('Investor')
async def trade_history(ctx):
    try:
        trades = db.get_trade_history(ctx.author.id)
        if not trades:
            await ctx.send(f"📜 {ctx.author.mention}, you have no trade history.")
            return
        message = f"📜 {ctx.author.mention}, your trade history:\n"
        for symbol, action, shares, price, timestamp in trades:
            message += f"- {symbol}: {action} {shares} shares at ${price} on {timestamp}\n"
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"⚠️ Error fetching trade history: {e}")

@trade_history.error
async def trade_history_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("⚠️ You need to be an Investor to use this command. Use /investor to get the role.")

@bot.command()
@commands.has_role('Investor')
async def get_info(ctx, symbol):
    try:
        info = yfMain.get_stock_info(symbol.upper())
        if info is None:
            await ctx.send(f"⚠️ Could not fetch info for {symbol.upper()}. Please check the symbol and try again.")
            return
        message = f"📊 Stock Info for {symbol.upper()}:\n"
        for key, value in info.items():
            message += f"- {key}: {value}\n"
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"⚠️ Error fetching stock info for {symbol.upper()}: {e}")

@get_info.error
async def get_info_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("⚠️ You need to be an Investor to use this command. Use /investor to get the role.")

@bot.command()
async def search_stocks(ctx, query, num_results: int = 10):
    try:
        if query.lower() not in ["popular", "sp500", "nasdaq100"]:
            await ctx.send("⚠️ Invalid query. Please use 'popular', 'sp500', or 'nasdaq100'.")
            return
        symbols = yfMain.list_all_stocks(query.lower())
        if not symbols:
            await ctx.send(f"⚠️ No stocks found for query '{query}'.")
            return
        
        # Limit to avoid Discord message length error (2000 chars)
        if len(symbols) > num_results:
            symbols = random.sample(symbols, num_results)
        
        message = f"🔍 {num_results} stocks from '{query}':\n" + ", ".join(symbols)
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"⚠️ Error searching stocks for query '{query}': {e}")

@bot.command()
async def help_investor(ctx):
    help_message = """
    📚 **Available Commands:**
    - `/investor <starting_funds>`: Become an investor with specified starting funds.
    - `/stop_grinding`: Remove investor role and data.
    - `/price <symbol>`: Get current market price of a stock.
    - `/get_funds`: Check your available funds.
    - `/finBERTsays <symbol>`: Get FinBERT analysis of stock news.
    - `/advice <symbol>`: Get investment advice for a stock.
    - `/graph <symbol>`: Get a graph of closing prices for a stock.
    - `/buy_shares <symbol> <shares>`: Buy a specific number of shares.
    - `/buy_dollars <symbol> <dollars>`: Buy shares worth a specific dollar amount.
    - `/sell_shares <symbol> <shares>`: Sell a specific number of shares.
    - `/sell_dollars <symbol> <dollars>`: Sell shares worth a specific dollar amount.
    - `/portfolio`: View your current portfolio.
    - `/get_info <symbol>`: Get basic information about a stock.
    - `/search_stocks <query> <num_results>`: Search for stocks by 'popular', 'sp500', or 'nasdaq100'. Num results is optional (default 10). Tells you random stocks from the selected category.
    - `/trade_history`: View your trade history.
    """
    await ctx.send(help_message)            
            

bot.run(DISCORD_BOT_TOKEN)