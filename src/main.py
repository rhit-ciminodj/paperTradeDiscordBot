import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv
import os
import random
import sqlite3

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

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for all commands."""
    if isinstance(error, commands.MissingRole):
        await ctx.send("⚠️ You need to be an Investor to use this command. Use `/investor` to get the role.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("⚠️ Command not found. Use `/help_investor` for available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Missing required argument: {error.param}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("⚠️ Invalid argument provided.")
    else:
        await ctx.send(f"⚠️ An error occurred: {error}")
        print(f"Error: {error}")

def generate_current_prices():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('SELECT DISTINCT symbol FROM portfolios')
    symbols = [row[0] for row in c.fetchall()]
    conn.close()

    current_prices = {}
    for symbol in symbols:
        price = yfMain.get_stock_price(symbol)
        if price is not None:
            current_prices[symbol] = price
    return current_prices

def calculate_roi(portfolio, current_prices, starting_funds):
    total_invested = sum(entry_price * shares for symbol, shares, entry_price in portfolio)
    current_value = sum(current_prices.get(symbol, 0) * shares for symbol, shares, entry_price in portfolio)
    total_value = current_value + (starting_funds - total_invested)
    roi = ((total_value - starting_funds) / starting_funds) * 100 if starting_funds > 0 else 0
    return round(roi, 2)

@bot.command()
async def investor(ctx, starting_funds):
    role = discord.utils.get(ctx.guild.roles, name="Investor")
    if role:
        try:
            if role in ctx.author.roles:
                await ctx.send(f"⚠️ {ctx.author.mention}, you are already an investor.")
                return
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

@bot.command()
@commands.has_role('Investor')
async def finBERTsays(ctx, symbol):
    try:
        analysis = analyze_stock_headlines(symbol.upper())
        await ctx.send(f"FinBERT Analysis loading for {symbol.upper()}:\n{analysis}")
    except Exception as e:
        await ctx.send(f"⚠️ Error fetching FinBERT analysis for {symbol.upper()}: {e}")

@bot.command()
@commands.has_role('Investor')
async def advice(ctx, symbol):
    try:
        advice_text = investment_advice(symbol.upper())
        await ctx.send(f"Investment Advice for {symbol.upper()}:\n{advice_text}")
    except Exception as e:
        await ctx.send(f"⚠️ Error fetching investment advice for {symbol.upper()}: {e}")

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
async def leaderboard(ctx):
    try:
        current_prices = generate_current_prices()
        
        # Get leaderboard with current prices
        leaderboard = db.get_leaderboard(current_prices)
        if not leaderboard:
            await ctx.send("⚠️ No users found for leaderboard.")
            return
        message = "🏆 **Leaderboard - Top Investors by Net Worth:**\n"
        rank = 1
        for user_id, net_worth in leaderboard:
            user = await bot.fetch_user(user_id)
            message += f"{rank}. {user.name} - Net Worth: ${net_worth}\n"
            rank += 1
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"⚠️ Error fetching leaderboard: {e}")

@bot.command()
@commands.has_role('Investor')
async def networth(ctx):
    try:
        current_prices = generate_current_prices()
        net_worth = db.calculate_user_net_worth(ctx.author.id, current_prices)
        if net_worth is None:
            await ctx.send(f"⚠️ Could not calculate net worth for {ctx.author.mention}.")
            return
        await ctx.send(f"💼 {ctx.author.mention}, your total net worth is: ${net_worth}")
    except Exception as e:
        await ctx.send(f"⚠️ Error calculating net worth: {e}")

@bot.command()
@commands.has_role('Investor')
async def total_return(ctx):
    try:
        current_prices = generate_current_prices()
        user_networth = db.calculate_user_net_worth(ctx.author.id, current_prices)
        starting_funds = db.get_user_starting_funds(ctx.author.id)
        if user_networth is None or starting_funds is None:
            await ctx.send(f"⚠️ Could not calculate total return for {ctx.author.mention}.")
            return
        total_return = round(((user_networth - starting_funds) / starting_funds) * 100, 2)
        await ctx.send(f"📈 {ctx.author.mention}, your total return since becoming an investor is {total_return}%")
    except Exception as e:
        await ctx.send(f"⚠️ Error calculating total return: {e}")

@bot.command()
@commands.has_role('Investor')
async def watchlist(ctx, symbol):
    try:
        db.add_to_watchlist(ctx.author.id, symbol.upper())
        await ctx.send(f"✅ {ctx.author.mention}, {symbol.upper()} has been added to your watchlist.")
    except Exception as e:
        await ctx.send(f"⚠️ Error adding {symbol.upper()} to watchlist: {e}")

@bot.command()
@commands.has_role('Investor')
async def unwatch(ctx, symbol):
    try:
        db.remove_from_watchlist(ctx.author.id, symbol.upper())
        await ctx.send(f"✅ {ctx.author.mention}, {symbol.upper()} has been removed from your watchlist.")
    except Exception as e:
        await ctx.send(f"⚠️ Error removing {symbol.upper()} from watchlist: {e}")

@bot.command()
@commands.has_role('Investor')
async def my_watchlist(ctx):
    try:
        symbols = db.get_watchlist(ctx.author.id)
        if not symbols:
            await ctx.send(f"📃 {ctx.author.mention}, your watchlist is empty.")
            return
        await ctx.send(f"📃 {ctx.author.mention}, your watchlist is:\n" + "\n".join(symbols))
    except Exception as e:
        await ctx.send(f"⚠️ Error fetching watchlist: {e}")

@bot.command()
@commands.has_role('Investor')
async def get_best_trades(ctx, top_n: int = 5):
    try:
        trades = db.get_best_trades(ctx.author.id, top_n)
        if not trades:
            await ctx.send(f"📜 {ctx.author.mention}, you have no trade history.")
            return
        message = f"🏅 {ctx.author.mention}, your top {top_n} best trades:\n"
        for symbol, entry_price, sell_price, shares, profit_loss, profit_loss_pct, timestamp in trades:
            message += f"- {symbol}: Bought at ${entry_price}, Sold at ${sell_price}, Shares: {shares}, P/L: ${profit_loss} ({profit_loss_pct}%) on {timestamp}\n"
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"⚠️ Error fetching best trades: {e}")

@bot.command()
@commands.has_role('Investor')
async def get_worst_trades(ctx, top_n: int = 5):
    try:
        trades = db.get_worst_trades(ctx.author.id, top_n)
        if not trades:
            await ctx.send(f"📜 {ctx.author.mention}, you have no trade history.")
            return
        message = f"💀 {ctx.author.mention}, your top {top_n} worst trades:\n"
        for symbol, entry_price, sell_price, shares, profit_loss, profit_loss_pct, timestamp in trades:
            message += f"- {symbol}: Bought at ${entry_price}, Sold at ${sell_price}, Shares: {shares}, P/L: ${profit_loss} ({profit_loss_pct}%) on {timestamp}\n"
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"⚠️ Error fetching worst trades: {e}")

@bot.command()
@commands.has_role('Investor')
async def stats(ctx):
    try:
        trades = db.get_trade_history(ctx.author.id)
        if not trades:
            await ctx.send(f"📊 You haven't made any trades yet.")
            return
        
        completed_trades = db.get_best_trades(ctx.author.id, 999)  # Get all trades
        if not completed_trades:
            await ctx.send(f"📊 You haven't completed any trades yet.")
            return
        
        total_trades = len(completed_trades)
        winning_trades = sum(1 for t in completed_trades if t[4] > 0)  # profit_loss > 0
        total_profit_loss = sum(t[4] for t in completed_trades)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        message = f"📊 **Your Trading Stats:**\n"
        message += f"Total Trades: {total_trades}\n"
        message += f"Winning Trades: {winning_trades}\n"
        message += f"Win Rate: {win_rate:.1f}%\n"
        message += f"Total P&L: ${total_profit_loss:.2f}\n"
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"⚠️ Error fetching stats: {e}")

@bot.command()
@commands.has_role('Investor')
async def check_portfolio(ctx, user: discord.Member):
    try:
        if user.id == ctx.author.id:
            await ctx.send("⚠️ You cannot check your own portfolio with this command. Use `/portfolio` instead.")
            return
        if not discord.utils.get(ctx.guild.roles, name = 'Investor') in user.roles:
            await ctx.send(f"⚠️ {user.mention} is not an investor.")
            return
        portfolio = db.get_portfolio(user.id)
        if not portfolio:
            await ctx.send(f"📂 {user.mention}'s portfolio is empty.")
            return
        message = f"📂 {user.mention}'s portfolio:\n"
        for symbol, shares, entry_price in portfolio:
            message += f"- {symbol}: {shares} shares at ${entry_price}\n"
        message += f"\nTotal Net Worth: ${db.calculate_user_net_worth(user.id, generate_current_prices())}"
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"⚠️ Error checking portfolio: {e}")

@bot.command()
@commands.has_role('Investor')
async def compare_portfolio(ctx, user: discord.Member):
    try:
        if user.id == ctx.author.id:
            await ctx.send("⚠️ You cannot compare your own portfolio with this command. Use `/portfolio` instead.")
            return
        if not discord.utils.get(ctx.guild.roles, name = 'Investor') in user.roles:
            await ctx.send(f"⚠️ {user.mention} is not an investor.")
            return
        
        user_portfolio = db.get_portfolio(ctx.author.id)
        other_portfolio = db.get_portfolio(user.id)
        
        if not user_portfolio:
            await ctx.send(f"📂 {ctx.author.mention}, your portfolio is empty.")
            return
        if not other_portfolio:
            await ctx.send(f"📂 {user.mention}'s portfolio is empty.")
            return
        
        message = f"📊 **Portfolio Comparison between {ctx.author.mention} and {user.mention}:**\n\n"
        
        message += f"**{ctx.author.mention}'s Portfolio:**\n"
        for symbol, shares, entry_price in user_portfolio:
            message += f"- {symbol}: {shares} shares at ${entry_price}\n"
        
        message += f"\n**{user.mention}'s Portfolio:**\n"
        for symbol, shares, entry_price in other_portfolio:
            message += f"- {symbol}: {shares} shares at ${entry_price}\n"

        message += f"\nTotal Net Worth:\n"
        message += f"- {ctx.author.mention}: ${db.calculate_user_net_worth(ctx.author.id, generate_current_prices())}\n"
        message += f"- {user.mention}: ${db.calculate_user_net_worth(user.id, generate_current_prices())}\n"
        message += f"- Return on Investment Comparison:\n"
        message += f"- {ctx.author.mention}: {calculate_roi(user_portfolio, generate_current_prices(), db.get_user_starting_funds(ctx.author.id))}%\n"
        message += f"- {user.mention}: {calculate_roi(other_portfolio, generate_current_prices(), db.get_user_starting_funds(user.id))}%\n"
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"⚠️ Error comparing portfolios: {e}")

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
    - `/leaderboard`: View the top investors by net worth. Displays top 5.
    - `/networth`: Check your total net worth (funds + stock value).
    - `/total_return`: Check your total return percentage since becoming an investor.
    - `/watchlist <symbol>`: Add a stock to your watchlist.
    - `/unwatch <symbol>`: Remove a stock from your watchlist.
    - `/my_watchlist`: View your current watchlist.
    - `/get_best_trades <top_n>`: View your top N best trades (default 5).
    - `/get_worst_trades <top_n>`: View your top N worst trades (default 5).
    - `/stats`: View your trading statistics. Caps out at reading 999 trades.
    - `/check_portfolio @user`: View another investor's portfolio.
    - `/compare_portfolio @user`: Compare your portfolio with another investor's portfolio.
    """
    await ctx.send(help_message)            
            

bot.run(DISCORD_BOT_TOKEN)