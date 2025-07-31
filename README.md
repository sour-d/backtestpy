# Backtesty - Advanced Multi-Timeframe Trading Strategy Backtester

A powerful, flexible backtesting framework for cryptocurrency trading strategies that combines multi-timeframe analysis, sophisticated risk management, and high-performance vectorized calculations.

## 🚀 Key Features

- **Multi-Timeframe Architecture**: Analyze higher timeframes for trends, execute on lower timeframes
- **Advanced Risk Management**: Position sizing based on actual stop loss distances and fixed risk percentages
- **Hybrid Performance**: Pre-calculated indicators + event-driven backtesting for optimal speed and flexibility
- **Multi-Asset Support**: Test strategies across multiple trading pairs and timeframes simultaneously
- **Rich Indicator Library**: Built-in technical indicators (SMA, EMA, RSI, MACD, SuperTrend, etc.)
- **Configurable Everything**: Single YAML configuration file controls all aspects of your backtest
- **Professional Portfolio Management**: Proper position sizing, risk control, and comprehensive fee calculation
- **Strategy Templates**: MovingAverageStrategy and MultiTimeframeMomentumStrategy included

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
│   ├── base_strategy.py    # Base strategy class with risk management
│   ├── multi_timeframe_base_strategy.py  # Multi-timeframe base
│   ├── moving_average_strategy.py        # MA strategy with proper stops
│   ├── multi_timeframe_momentum_strategy.py  # Multi-TF momentum
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
# Trading pairs to test with multiple timeframes
trading_pairs:
  - { symbol: "BTC/USDT", timeframes: [
          "1h",
          "4h",
          "1d",
        ], start: "2024-01-01", end: "2024-12-31", prefix: "BTC_2024" } # Multiple timeframes

# Pre-calculate these indicators for all timeframes
indicators:
  - { name: "ma_high", period: 20 }
  - { name: "ma_low", period: 20 }
  - { name: "supertrend", period: 10, multiplier: 2 }
  - { name: "EMA", period: 12 }
  - { name: "EMA", period: 26 }

# Portfolio settings with proper risk management
portfolio:
  initial_capital: 100000
  fee_pct: 0.05 # 0.05% fee per trade
  risk_pct: 5 # Risk 5% of capital per trade

# Strategy configuration with timeframe specification
strategy:
  class_name: "MultiTimeframeMomentumStrategy"
  timeframe: "1h" # Primary execution timeframe
  parameters:
    higher_timeframe: "4h" # Trend analysis timeframe
    ema_fast_col: "EMA_12"
    ema_slow_col: "EMA_26"
    take_profit_pct: 0.02
```

## 📖 Strategy Development

For detailed instructions on creating custom trading strategies, see our comprehensive **[Strategy Development Guide](STRATEGY_GUIDE.md)**.

### Quick Example

```python
from .multi_timeframe_base_strategy import MultiTimeframeBaseStrategy

class MyMultiTimeframeStrategy(MultiTimeframeBaseStrategy):
    def __init__(self, env, portfolio, **params):
        super().__init__(env, portfolio, **params)
        self.primary_tf = self.env.primary_timeframe  # e.g., "1h"
        self.higher_tf = self.params.get("higher_timeframe", "4h")

    def buy_signal(self):
        # Get current data for primary timeframe
        current_data = self.env.now[self.primary_tf]
        # Get higher timeframe data for trend analysis
        higher_tf_data = self.env.now[self.higher_tf]

        if (higher_tf_data['superTrendDirection'] == 'Buy' and
            current_data['EMA_12'] > current_data['EMA_26']):
            # Return both entry price and stop loss
            entry_price = current_data['close']
            stop_loss = current_data['close'] * 0.97  # 3% stop
            return entry_price, stop_loss
        return None, None

    def sell_signal(self):
        # Implement short selling logic with proper stop loss
        return None, None

    def close_long_signal(self):
        current_data = self.env.now[self.primary_tf]
        if not self.portfolio.current_trade:
            return None, None

        # Take profit at 2%
        take_profit = self.portfolio.current_trade["entry_price"] * 1.02
        if current_data['close'] >= take_profit:
            return current_data['close'], "take_profit"
        return None, None

    def close_short_signal(self):
        return None, None
```

## 🎯 Available Strategies

- **MovingAverageStrategy**: Single timeframe MA strategy with adaptive stop losses
- **MultiTimeframeMomentumStrategy**: Higher timeframe trend + lower timeframe execution
- **SMA Crossover**: Classic moving average crossover strategy
- **Base Strategy Templates**: For custom single and multi-timeframe strategies

## 🚀 Risk Management Features

- **Fixed Risk Percentage**: Risk a consistent percentage of capital per trade
- **Position Sizing**: Automatically calculates quantity based on stop loss distance
- **Adaptive Stops**: Combines technical levels with percentage-based stops
- **Professional Risk Control**: Never risk more than your defined percentage

## 📊 Multi-Timeframe Capabilities

- **Trend Analysis**: Use higher timeframes (4h, 1d) for trend direction
- **Execution Precision**: Execute trades on lower timeframes (1h, 5m) for better fills
- **Data Synchronization**: Automatically handles timeframe alignment
- **Flexible Configuration**: Mix and match any timeframe combinations

## 📊 Supported Indicators

- **Moving Averages**: SMA, EMA, ma_high, ma_low
- **Trend Indicators**: SuperTrend, MACD
- **Momentum**: RSI, Stochastic
- **Volatility**: Bollinger Bands, ATR
- **Custom Indicators**: Easy to add via indicator processor

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
