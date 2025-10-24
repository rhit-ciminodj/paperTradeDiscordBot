# paperTradeDiscordBot

A Discord bot for paper trading and real-time market data analysis using yfinance.

## Features

- **Stock Price Lookup**: Fetch current prices for individual stocks or lists (popular, S&P 500, Nasdaq-100).
- **News Headlines**: Scrape recent news headlines for stocks.
- **Market Data Analysis**: Get stock info, historical data, and price trends.
- **Discord Integration**: Interact with market data directly from Discord commands.

## Setup

### Prerequisites

- Python 3.8+
- Discord bot token

### Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd paperTradeDiscordBot
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your credentials:
   ```
   DISCORD_TOKEN=your_discord_bot_token
   ```

### Usage

Run the Discord bot:
```bash
python3 main.py
```

Or test individual modules:
```bash
# Test stock prices
python3 yfinanceMain.py

# Test news scraper
python3 -c "from src.headlineNewsScraper import get_stock_headlines; print(get_stock_headlines('AAPL'))"
```

## Modules

- **`yfinanceMain.py`**: Price lookup and list fetching (popular, S&P 500, Nasdaq-100).
- **`src/headlineNewsScraper.py`**: Fetch recent news headlines for stocks.

## API Integrations

- **yfinance**: Stock prices, historical data, and fundamental information.
- **Discord**: Bot commands and messaging.

## Data Sources

- **yfinance**: Free stock data from Yahoo Finance (~15-20min delay).
- **Wikipedia**: S&P 500 and Nasdaq-100 constituent lists.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DISCORD_TOKEN` | Discord bot token |

## Troubleshooting

### HTTP 403 Forbidden (Wikipedia scraping)
- Already handled with User-Agent headers; if it persists, check your internet connection.

### No data returned for a stock
- Verify the stock symbol is valid (e.g., `AAPL`, `TSLA`).
- yfinance data may be delayed or unavailable for certain symbols.

## License

MIT

## Contributing

Pull requests welcome. For major changes, open an issue first.