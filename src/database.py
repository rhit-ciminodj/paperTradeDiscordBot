import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
              user_id INTEGER PRIMARY KEY,
              username TEXT,
              join_date TIMESTAMP,
              total_funds REAL,
              starting_funds REAL
              )''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS portfolios (
              user_id INTEGER,
              symbol TEXT,
              shares REAL,
              entry_price REAL,
              total_invested REAL,
              PRIMARY KEY (user_id, symbol)
              )''')
              
    
    c.execute('''CREATE TABLE IF NOT EXISTS trades (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER,
              symbol TEXT,
              action TEXT,
              shares REAL,
              price REAL,
              timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
              )''')

    c.execute('''CREATE TABLE IF NOT EXISTS trade_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            symbol TEXT,
            entry_price REAL,
            sell_price REAL,
            shares REAL,
            profit_loss REAL,
            profit_loss_pct REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS watchlist (
            user_id INTEGER,
            symbol TEXT,
            PRIMARY KEY (user_id, symbol)
            )''')
    
    conn.commit()
    conn.close()

def add_user(user_id, username, funds):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO users (user_id, username, join_date, total_funds, starting_funds)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, datetime.now(), funds, funds))
    conn.commit()
    conn.close()

def get_user_funds(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('SELECT total_funds FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return round(result[0], 2) if result else None

def get_user_starting_funds(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('SELECT starting_funds FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return round(result[0], 2) if result else None

def get_user_stock_total(user_id, current_prices):
    """Calculate current total value of stocks in portfolio.
    
    Args:
        user_id: Discord user ID
        current_prices: dict like {"AAPL": 160.50, "TSLA": 245.30}
    
    Returns:
        Total current value of all holdings
    """
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('SELECT symbol, shares FROM portfolios WHERE user_id = ?', (user_id,))
    holdings = c.fetchall()
    conn.close()
    
    total_value = 0
    for symbol, shares in holdings:
        current_price = current_prices.get(symbol, 0)
        total_value += shares * current_price
    
    return round(total_value, 2)

def update_user_funds(user_id, new_funds):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('UPDATE users SET total_funds = ? WHERE user_id = ?', (new_funds, user_id))
    conn.commit()
    conn.close()

def add_to_portfolio(user_id, symbol, shares, entry_price):
    """Add shares to portfolio, calculate weighted average entry price."""
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    total_invested = shares * entry_price
    c.execute('''
        SELECT shares, entry_price, total_invested FROM portfolios 
        WHERE user_id = ? AND symbol = ?
    ''', (user_id, symbol))
    existing = c.fetchone()
    
    if existing is None:
        # First purchase
        c.execute('''
            INSERT INTO portfolios (user_id, symbol, shares, entry_price, total_invested)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, symbol, shares, entry_price, total_invested))
    else:
        # Add to existing position, calculate weighted average
        existing_shares, existing_price, existing_total = existing
        total_shares = existing_shares + shares
        avg_price = (existing_shares * existing_price + shares * entry_price) / total_shares
        total_invested = existing_total + total_invested
        c.execute('''
            UPDATE portfolios
            SET shares = ?, entry_price = ?, total_invested = ?
            WHERE user_id = ? AND symbol = ?
        ''', (total_shares, avg_price, total_invested, user_id, symbol))
    
    conn.commit()
    conn.close()

def sell_from_portfolio(user_id, symbol, shares, sell_price):
    """Sell shares from portfolio."""
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('''
        SELECT shares, entry_price, total_invested FROM portfolios 
        WHERE user_id = ? AND symbol = ?
    ''', (user_id, symbol))
    existing = c.fetchone()
    
    if existing is None:
        conn.close()
        raise ValueError("Position doesn't exist")
    
    previous_shares, entry_price, total_invested = existing
    if previous_shares < shares:
        conn.close()
        raise ValueError("Not enough shares to sell")
    
    log_completed_trade(user_id, symbol, entry_price, sell_price, shares)
    
    if previous_shares == shares:
        # Sold all shares, delete position
        c.execute('DELETE FROM portfolios WHERE user_id = ? AND symbol = ?', (user_id, symbol))
    else:
        # Sold some shares, update position
        remaining_shares = previous_shares - shares
        remaining_invested = total_invested * (remaining_shares / previous_shares)
        c.execute('''
            UPDATE portfolios
            SET shares = ?, total_invested = ?
            WHERE user_id = ? AND symbol = ?
        ''', (remaining_shares, remaining_invested, user_id, symbol))
    
    conn.commit()
    conn.close()

def log_completed_trade(user_id, symbol, entry_price, sell_price, shares):
    profit_loss = (sell_price - entry_price) * shares
    profit_loss_pct = (profit_loss / (entry_price * shares)) * 100 if entry_price * shares != 0 else 0
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO trade_analytics (user_id, symbol, entry_price, sell_price, shares, profit_loss, profit_loss_pct, timestamp) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, symbol, entry_price, sell_price, shares, profit_loss, profit_loss_pct, datetime.now()))
    conn.commit()
    conn.close()

def get_best_trades(user_id, top_n=5):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('''
        SELECT symbol, entry_price, sell_price, shares, profit_loss, profit_loss_pct, timestamp 
        FROM trade_analytics 
        WHERE user_id = ? 
        ORDER BY profit_loss_pct DESC 
        LIMIT ?
    ''', (user_id, top_n))
    trades = c.fetchall()
    conn.close()
    return trades

def get_worst_trades(user_id, top_n=5):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('''
              SELECT symbol, entry_price, sell_price, shares, profit_loss, profit_loss_pct, timestamp
              FROM trade_analytics
              WHERE user_id = ?
              ORDER BY profit_loss_pct ASC
              LIMIT ?
              ''', (user_id, top_n))
    trades = c.fetchall()
    conn.close()
    return trades

def log_trade(user_id, symbol, action, shares, price):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO trades (user_id, symbol, action, shares, price)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, symbol, action, shares, price))
    conn.commit()
    conn.close()

def get_portfolio(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('SELECT symbol, shares, entry_price, total_invested FROM portfolios WHERE user_id = ?', (user_id,))
    portfolio = c.fetchall()
    conn.close()
    return portfolio

def get_trade_history(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('SELECT symbol, action, shares, price, timestamp FROM trades WHERE user_id = ? ORDER BY timestamp DESC', (user_id,))
    trades = c.fetchall()
    conn.close()
    return trades

def remove_user(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM portfolios WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM trades WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM watchlist WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM trade_analytics WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def calculate_user_net_worth(user_id, current_prices):
    funds = get_user_funds(user_id)
    stock_total = get_user_stock_total(user_id, current_prices)
    if funds is None or stock_total is None:
        return None
    return round(funds + stock_total, 2)

def get_leaderboard(current_prices):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    users = c.fetchall()
    user_dict = {}
    for user_id in users:
        net_worth = calculate_user_net_worth(user_id[0], current_prices)
        if net_worth is not None:
            user_dict[user_id[0]] = net_worth
    conn.close()
    # Sort users by net worth
    sorted_leaderboard = sorted(user_dict.items(), key=lambda x: x[1], reverse=True)
    return sorted_leaderboard[:5]

def add_to_watchlist(user_id, symbol):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO watchlist (user_id, symbol) VALUES (?, ?)', (user_id, symbol))
    conn.commit()
    conn.close()

def remove_from_watchlist(user_id, symbol):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM watchlist WHERE user_id = ? AND symbol = ?', (user_id, symbol))
    conn.commit()
    conn.close()

def get_watchlist(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('SELECT symbol FROM watchlist WHERE user_id = ?', (user_id,))
    symbols = c.fetchall()
    conn.close()
    return [symbol[0] for symbol in symbols]

# Initialize the database when the module is imported
init_db()

