import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend
import matplotlib.pyplot as plt
import yfinance as yf
from io import BytesIO

def graph_closing_prices(symbol, period='1mo', interval='1d'):
    """Fetch closing prices for a given stock symbol."""
    try:
        rets = yf.download(tickers=symbol, period=period, interval=interval, auto_adjust=True)
        closing_price = rets['Close']

        # Plotting
        plt.figure(figsize=(10, 5))
        closing_price.plot(title=f'Closing Prices for {symbol}')
        plt.xlabel('Date')
        plt.ylabel('Price (USD)')
        plt.tight_layout()

        # Save plot to a BytesIO buffer
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100)
        img_buffer.seek(0)  # Rewind the buffer to the beginning
        plt.close()  # Close the plot to free memory

        return rets['Close'], img_buffer   
    except Exception as e:
        print(f"Error fetching closing prices for {symbol}: {e}")
        return pd.Series(), None

def _annualize_return(total_return, period_str):
    """Convert total return over a period to annualized return."""
    period_map = {
        '1d': 252,
        '1mo': 12,
        '3mo': 4,
        '6mo': 2,
        '1y': 1,
        '2y': 0.5,
        '5y': 0.2,
    }
    periods_per_year = period_map.get(period_str, 1)
    annualized = (1 + total_return) ** periods_per_year - 1
    return annualized

def annualized_return(symbol, period='1y', interval='1d'):
    try:
        rets = yf.download(tickers=symbol, period=period, interval=interval, auto_adjust=True)
        daily_rets = rets['Close'].pct_change().dropna()
        total_return = (1 + daily_rets).prod() - 1
        
        if isinstance(total_return, pd.Series):
            total_return = total_return.iloc[0]

        annualized = _annualize_return(total_return, period)
        annualized_pct = round(annualized * 100, 2)
        return annualized_pct
    except Exception as e:
        print(f"Error calculating annualized return for {symbol}: {e}")
        return None

def annualized_volatility(symbol, period='1y', interval='1d'):
    try:
        rets = yf.download(tickers=symbol, period=period, interval=interval, auto_adjust=True)
        daily_rets = rets['Close'].pct_change().dropna()
        annual_volatility = daily_rets.std() * (periods_per_year := 252) ** 0.5
        if isinstance(annual_volatility, pd.Series):
            annual_volatility = annual_volatility.iloc[0]
        volatility = round(annual_volatility * 100, 2)
        return volatility
    except Exception as e:
        print(f"Error calculating annualized volatility for {symbol}: {e}")
        return None


def get_Sharpe_ratio(symbol):
    """Calculate Sharpe ratio: (return - risk_free_rate) / volatility
    
    Sharpe > 1.0 is considered good.
    Sharpe > 2.0 is considered very good.
    """
    try:
        annualized_return_value = annualized_return(symbol)
        annualized_volatility_value = annualized_volatility(symbol)

        if annualized_return_value is None or annualized_volatility_value is None or annualized_volatility_value == 0:
            return None
        
        # Sharpe = (return - risk_free_rate) / volatility

        #Calculate Risk Free Rate dynamically

        irx = yf.Ticker("^IRX")
        rfr = irx.history(period="1d")["Close"].iloc[-1] / 100 

        sharpe_ratio = (annualized_return_value / 100 - rfr) / (annualized_volatility_value / 100)
        return round(sharpe_ratio, 2)
    except Exception as e:
        print(f"Error calculating Sharpe ratio for {symbol}: {e}")
        return None

def investment_advice(symbol):
    sharpe = get_Sharpe_ratio(symbol)
    ann_ret = annualized_return(symbol)
    ann_vol = annualized_volatility(symbol)
    
    if sharpe is None:
        return "Could not calculate metrics."
    
    advice = ""
    if sharpe > 2.0:
        advice = f"✅ **Excellent - lil Dom** risk-adjusted returns (Sharpe: {sharpe})"
    elif sharpe > 1.0:
        advice = f"✅ **Good** risk-adjusted returns (Sharpe: {sharpe})"
    elif sharpe > 0.5:
        advice = f"⚠️ **Mediocre** risk-adjusted returns (Sharpe: {sharpe})"
    else:
        advice = f"❌ **Poor** risk-adjusted returns (Sharpe: {sharpe})"
    
    # Add context
    advice += f"\n  Return: {ann_ret}% | Volatility: {ann_vol}%"
    advice += f"\n  *Disclaimer: Not financial advice. Do your own research.*"
    
    return advice

