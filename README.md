# paperTradeDiscordBot

A Discord bot for paper trading and real-time market data analysis using yfinance.

## Features

- **Stock Price Lookup**: Fetch current prices for individual stocks or lists (popular, S&P 500, Nasdaq-100).
- **News Headlines**: Scrape recent news headlines for stocks with FinBERT sentiment analysis.
- **Market Data Analysis**: Get stock info, historical data, charts, and price trends.
- **Paper Trading**: Buy/sell stocks with virtual funds and track your portfolio.
- **Performance Analytics**: Track trades, calculate P&L, win rates, and ROI.
- **Leaderboard**: Compete with other investors and see rankings by net worth.
- **Watchlist**: Monitor stocks without buying them.
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
   sudo docker-compose logs -f bot
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

### Account Management
- `/investor <starting_funds>` - Become an investor with specified starting funds.
- `/stop_grinding` - Remove investor role and all associated data.
- `/get_funds` - Check your available cash funds.

### Trading
- `/buy_shares <symbol> <shares>` - Buy a specific number of shares.
- `/buy_dollars <symbol> <dollars>` - Buy shares worth a specific dollar amount.
- `/sell_shares <symbol> <shares>` - Sell a specific number of shares.
- `/sell_dollars <symbol> <dollars>` - Sell shares worth a specific dollar amount.
- `/portfolio` - View your current portfolio with entry prices and totals.
- `/trade_history` - View your complete trade history.

### Market Data
- `/price <symbol>` - Get current market price of a stock.
- `/get_info <symbol>` - Get detailed stock information (sector, P/E ratio, market cap, etc.).
- `/search_stocks <query> <num_results>` - Search for stocks. Query: 'popular', 'sp500', or 'nasdaq100'. Num results optional (default 10).
- `/graph <symbol>` - Get a chart of closing prices for a stock.
- `/finBERTsays <symbol>` - Get FinBERT sentiment analysis of stock news.
- `/advice <symbol>` - Get investment advice and analysis for a stock.

### Portfolio Analytics
- `/networth` - Check your total net worth (cash + current stock value).
- `/total_return` - Check your total return percentage since becoming an investor.
- `/stats` - View your trading statistics (total trades, win rate, total P&L).
- `/get_best_trades <top_n>` - View your top N best trades by profit % (default 5).
- `/get_worst_trades <top_n>` - View your top N worst trades by loss % (default 5).
- `/leaderboard` - View the top 5 investors by net worth.

### Watchlist
- `/watchlist <symbol>` - Add a stock to your watchlist.
- `/unwatch <symbol>` - Remove a stock from your watchlist.
- `/my_watchlist` - View your current watchlist with current prices.

### Social Features
- `/check_portfolio @user` - View another investor's portfolio.
- `/compare_portfolio @user` - Compare your portfolio with another investor (side-by-side with ROI).

### Help
- `/help_investor` - Display all available commands.

## Database

The bot uses SQLite (`user_data.db`) to store:
- **Users**: Account info, starting funds, total funds
- **Portfolios**: Current holdings with average entry prices and total invested
- **Trades**: Complete buy/sell transaction history
- **Trade Analytics**: Completed trades with profit/loss calculations for performance tracking
- **Watchlist**: Monitored stocks per user

With Docker, the database is mounted as a volume and persists between container restarts.

## Architecture

### File Structure
```
src/
├── main.py                 # Discord bot commands
├── database.py             # SQLite database operations
├── yfinanceMain.py         # Stock data fetching
├── finBERTAIlogic.py       # Sentiment analysis
└── logicFile.py            # Investment advice & charting
```

### Key Features
- **Weighted Average Entry Price**: Accurately tracks cost basis when buying at different prices
- **P&L Tracking**: Automatic profit/loss calculation on each sale
- **Real-time Pricing**: Fetches current prices from yfinance
- **Global Error Handler**: Consistent error messages across all commands

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

### Database schema errors
If you modify the database schema, delete the old database and restart:
```bash
sudo docker-compose down
rm user_data.db
sudo docker-compose up --build -d
```

## Performance Tips

- Use `/search_stocks` to find new trading opportunities
- Use `/watchlist` to monitor stocks before buying
- Check `/leaderboard` to see how you rank against other investors
- Review `/get_best_trades` and `/get_worst_trades` to learn from your mistakes

## License

MIT

## Contributing

Pull requests welcome!