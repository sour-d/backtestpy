# Backtesty - Advanced Trading Strategy Backtester

A powerful, flexible backtesting framework for cryptocurrency trading strategies that combines high-performance vectorized indicator calculations with event-driven strategy execution.

## 🚀 Features

- **Hybrid Architecture**: Pre-calculated indicators + event-driven backtesting for optimal performance and flexibility
- **Multi-Asset Support**: Test strategies across multiple trading pairs simultaneously
- **Rich Indicator Library**: Built-in technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, etc.)
- **Configurable Everything**: Single YAML configuration file controls all aspects of your backtest
- **Advanced Portfolio Management**: Position sizing, risk management, and fee calculation
- **Visualization**: Interactive trading charts and performance analytics
- **Easy Strategy Development**: Clean, intuitive strategy API

## 📁 Project Structure

```
backtesty/
├── config.yaml              # Main configuration file
├── main.py                  # Entry point for backtesting
├── download_data.py         # Data downloading script
├── Makefile                 # Build and run commands
├── requirements.txt         # Python dependencies
├── STRATEGY_GUIDE.md        # 📖 Comprehensive strategy development guide
├── data/
│   ├── raw/                # Downloaded market data
│   ├── processed/          # Data with calculated indicators
│   └── result/             # Backtest results and reports
├── strategies/             # Trading strategy implementations
│   ├── base_strategy.py    # Base strategy class
│   └── sma_crossover_strategy.py
├── portfolio/              # Portfolio management
├── env/                    # Trading environment simulation
├── utils/                  # Data fetching, processing utilities
└── notebooks/              # Jupyter notebooks for analysis
```

## 🛠️ Quick Start

### 1. Install Dependencies

```bash
make install
# or manually:
pip install -r requirements.txt
```

### 2. Download Market Data

```bash
make download
```

This downloads cryptocurrency data for the pairs defined in `config.yaml`.

### 3. Run a Backtest

```bash
# Run backtest on first trading pair
make run index=0

# Run backtest on all trading pairs
make run index=all
```

### 4. View Results

Results are saved to `data/result/` and include:

- Performance metrics
- Trade log
- Interactive charts (if visualization is enabled)

## ⚙️ Configuration

The entire framework is controlled through `config.yaml`:

```yaml
# Trading pairs to test
trading_pairs:
  - {
      symbol: "BTC/USDT",
      timeframe: "1h",
      start: "2022-01-01",
      end: "2023-12-31",
    }
  - {
      symbol: "ETH/USDT",
      timeframe: "1h",
      start: "2022-01-01",
      end: "2022-12-31",
    }

# Pre-calculate these indicators
indicators:
  - { name: "SMA", period: 50 }
  - { name: "SMA", period: 200 }
  - { name: "RSI", period: 14 }

# Portfolio settings
portfolio:
  initial_capital: 100000
  fee_pct: 0.1

# Strategy configuration
strategy:
  class_name: "SMACrossoverStrategy"
  parameters:
    fast_sma_col: "SMA_50"
    slow_sma_col: "SMA_200"
    risk_pct: 0.01
```

## 📖 Strategy Development

For detailed instructions on creating custom trading strategies, see our comprehensive **[Strategy Development Guide](STRATEGY_GUIDE.md)**.

### Quick Example

```python
from .base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def buy_signal(self):
        now = self.env.now
        # Access pre-calculated indicators
        if now['close'] > now['SMA_50']:
            return now['close']  # Buy at current price
        return None

    def sell_signal(self):
        # Implement short selling logic
        return None

    def close_long_signal(self):
        now = self.env.now
        if now['close'] < now['SMA_50']:
            return now['close'], "stop_loss"
        return None, None

    def close_short_signal(self):
        return None, None
```

## 🎯 Available Strategies

- **SMA Crossover**: Moving average crossover strategy
- **Base Strategy**: Template for custom strategies

## 📊 Supported Indicators

- Simple Moving Average (SMA)
- Exponential Moving Average (EMA)
- Relative Strength Index (RSI)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Average True Range (ATR)
- And more...

## 🔧 Available Commands

```bash
make help          # Show all available commands
make install       # Install dependencies
make download      # Download market data
make run index=0   # Run backtest on first pair
make run index=all # Run backtest on all pairs
make clean         # Clean generated files
```

## 📈 Performance Features

- **Vectorized Calculations**: All indicators calculated efficiently upfront
- **Memory Efficient**: Processes data in optimized chunks
- **Fast Execution**: Event-driven loop optimized for speed
- **Parallel Processing**: Multiple trading pairs can be processed in parallel

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

- Check the [Strategy Guide](STRATEGY_GUIDE.md) for detailed documentation
- Review example strategies in the `strategies/` directory
- Look at the configuration examples in `config.yaml`

---

**Happy Trading! 📈**
