import yfinance as yf

def get_stock_headlines(symbol, count=5):
    """Fetch recent news headlines for a given stock symbol."""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        
        if not news:
            return []
        
        headlines = []
        for item in news[:count]:
            # yfinance news items have different keys; try common ones
            title = item.get('title') or item.get('headline') or item.get('summary') or str(item)
            if title:
                headlines.append(title)
        
        return headlines
    
    except Exception as e:
        print(f"Error fetching news for {symbol}: {e}")
        return []