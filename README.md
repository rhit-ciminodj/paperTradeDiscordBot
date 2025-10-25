# paperTradeDiscordBot

A Discord bot for paper trading and real-time market data analysis using yfinance.

## Features

- **Stock Price Lookup**: Fetch current prices for individual stocks or lists (popular, S&P 500, Nasdaq-100).
- **News Headlines**: Scrape recent news headlines for stocks.
- **Market Data Analysis**: Get stock info, historical data, and price trends.
- **Paper Trading**: Buy/sell stocks with virtual funds and track your portfolio.
- **Discord Integration**: Interact with market data directly from Discord commands.

## Setup

### Prerequisites

- Python 3.8+
- Discord bot token
- Docker (optional, for containerized deployment)

### Local Setup

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
   DISCORD_BOT_TOKEN=your_discord_bot_token
   ```

5. Run the bot:
   ```bash
   python src/main.py
   ```

### Docker Setup

1. Create a `.env` file with your token:
   ```bash
   echo "DISCORD_BOT_TOKEN=your_token_here" > .env
   ```

2. Build and run:
   ```bash
   sudo docker-compose up --build
   ```

3. Run in background:
   ```bash
   sudo docker-compose up -d
   ```

4. View logs:
   ```bash
   sudo docker-compose logs -f
   ```

5. Stop the bot:
   ```bash
   sudo docker-compose stop
   ```

6. Start the bot again:
   ```bash
   sudo docker-compose start
   ```

7. Restart the bot:
   ```bash
   sudo docker-compose restart
   ```

## Commands

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

## Database

The bot uses SQLite (`user_data.db`) to store:
- User portfolios
- Trade history
- Holdings and P&L

With Docker, the database is mounted as a volume and persists between container restarts.

## Troubleshooting

### Docker permission denied
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Database not persisting
Ensure `docker-compose.yml` has:
```yaml
volumes:
  - .:/app
```

## License

MIT

## Contributing

Pull requests welcome!