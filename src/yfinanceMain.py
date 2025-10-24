import yfinance as yf
import pandas as pd
import requests
from io import StringIO


def get_stock_price(symbol):
    """Get the current market price of a stock"""
    try:
        ticker = yf.Ticker(symbol)
        # Get the most recent data
        data = ticker.history(period='1d', interval='1m')
        
        if data.empty:
            return None
        
        current_price = data['Close'].iloc[-1]
        return round(current_price, 2)
    
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None
    
def get_multiple_stock_prices(symbols):
    prices = {}
    for symbol in symbols:
        price = get_stock_price(symbol)
        prices[symbol] = price
    return prices

def calculate_percentage_change(old_price, symbol):
    current_price = get_stock_price(symbol)
    if current_price is None or old_price is None:
        return None
    try:
        change = ((current_price - old_price) / old_price) * 100
        return round(change, 2)
    except ZeroDivisionError:
        return None
    
def calculate_price_difference(old_price, symbol):
    current_price = get_stock_price(symbol)
    if current_price is None or old_price is None:
        return None
    difference = current_price - old_price
    return round(difference, 2)

def calculate_price_to_stocks(price, symbol):
    current_stock_price = get_stock_price(symbol)
    if current_stock_price is None or current_stock_price == 0:
        return None
    try:
        num_stocks = price / current_stock_price
        return round(num_stocks, 4)
    except ZeroDivisionError:
        return None
    
def calculate_stocks_to_price(num_stocks, symbol):
    current_stock_price = get_stock_price(symbol)
    if current_stock_price is None:
        return None
    total_price = num_stocks * current_stock_price
    return round(total_price, 2)

def get_stock_info(symbol):
    """Get basic information about a stock"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        data = {
            'symbol': symbol,
            'shortName': info.get('shortName', 'N/A'),
            'longName': info.get('longName', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'website': info.get('website', 'N/A'),
            'marketCap': info.get('marketCap', 'N/A'),
            'previousClose': info.get('previousClose', 'N/A'),
            'open': info.get('open', 'N/A'),
            'dayHigh': info.get('dayHigh', 'N/A'),
            'dayLow': info.get('dayLow', 'N/A'),
        }
        return data
    except Exception as e:
        print(f"Error fetching info for {symbol}: {e}")
        return None
    
def get_current_most_popular_stocks():
    """Get a list of currently popular stocks"""
    popular_stocks = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'TSLA', 'NVDA', 'META', 'BRK-B', 'JPM', 'V']
    return popular_stocks

def list_all_stocks(source: str = "popular", limit: int | None = None):
    """
    Return a list of stock symbols from:
      - "popular"  : small hardcoded list
      - "sp500"    : S&P 500 constituents from Wikipedia
      - "nasdaq100": Nasdaq-100 constituents from Wikipedia
    """
    source = (source or "popular").lower()
    symbols = []

    if source == "popular":
        symbols = get_current_most_popular_stocks()

    elif source == "sp500":
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            tables = pd.read_html(StringIO(resp.text))
            df = tables[0]
            col = "Symbol" if "Symbol" in df.columns else df.columns[0]
            symbols = df[col].astype(str).str.replace(".", "-", regex=False).tolist()
        except Exception as e:
            print("Failed to fetch S&P 500 list:", e)
            symbols = []

    elif source == "nasdaq100":
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            tables = pd.read_html(StringIO(resp.text))
            df = None
            for t in tables:
                cols = [c.lower() for c in t.columns.astype(str)]
                if any(x in cols for x in ("ticker", "ticker symbol", "symbol")):
                    df = t
                    break
            if df is None:
                df = tables[0]
            possible = [c for c in df.columns if c.lower() in ("ticker", "ticker symbol", "symbol")]
            col = possible[0] if possible else df.columns[0]
            symbols = df[col].astype(str).str.replace(".", "-", regex=False).tolist()
        except Exception as e:
            print("Failed to fetch Nasdaq-100 list:", e)
            symbols = []

    else:
        raise ValueError(f"unknown source: {source}")

    if limit:
        return symbols[:limit]
    return symbols