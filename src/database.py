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
              total_funds REAL
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
              timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
              ''')
    
    conn.commit()
    conn.close()

def add_user(user_id, username, funds):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO users (user_id, username, join_date, total_funds)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, datetime.now(), funds))
    conn.commit()
    conn.close()

def get_user_funds(user_id):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('SELECT total_funds FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

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
    elif previous_shares == shares:
        # Sold all shares, delete position
        c.execute('DELETE FROM portfolios WHERE user_id = ? AND symbol = ?', (user_id, symbol))
    else:
        # Sold some shares, update position
        remaining_shares = previous_shares - shares
        # Scale total_invested proportionally
        remaining_invested = total_invested * (remaining_shares / previous_shares)
        c.execute('''
            UPDATE portfolios
            SET shares = ?, total_invested = ?
            WHERE user_id = ? AND symbol = ?
        ''', (remaining_shares, remaining_invested, user_id, symbol))
    
    conn.commit()
    conn.close()

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
    conn.commit()
    conn.close()

# Initialize the database when the module is imported
init_db()

