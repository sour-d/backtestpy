# Multi-Timeframe Strategy Framework Documentation

## Overview

This framework provides a sophisticated multi-timeframe backtesting environment with professional risk management. It combines:

1. **Multi-Timeframe Analysis**: Use higher timeframes for trend analysis, lower for execution
2. **Professional Risk Management**: Fixed risk percentage with proper position sizing
3. **High Performance**: Pre-calculated indicators across all timeframes
4. **Flexible Architecture**: Event-driven execution with vectorized preprocessing

## Workflow

1. **Configuration**: Define trading pairs, timeframes, and indicators in `config.yaml`
2. **Data Processing**: Download and process data for all specified timeframes
3. **Indicator Calculation**: Technical indicators calculated efficiently for each timeframe
4. **Multi-Timeframe Execution**: Strategy runs with access to all timeframe data simultaneously
5. **Risk Management**: Position sizing based on actual stop loss distances

---

## 1. Multi-Timeframe Configuration

```yaml
# Define multiple timeframes per trading pair
trading_pairs:
  - { symbol: "BTC/USDT", timeframes: [
          "1h",
          "4h",
          "1d",
        ], start: "2024-01-01", end: "2024-12-31", prefix: "BTC_2024" } # Multiple timeframes

# Indicators calculated for ALL timeframes
indicators:
  - { name: "ma_high", period: 20 }
  - { name: "ma_low", period: 20 }
  - { name: "supertrend", period: 10, multiplier: 2 }
  - { name: "EMA", period: 12 }
  - { name: "EMA", period: 26 }

# Professional risk management
portfolio:
  initial_capital: 100000
  fee_pct: 0.05 # 0.05% per trade
  risk_pct: 5 # Risk 5% of capital per trade

# Strategy with timeframe specification
strategy:
  class_name: "MultiTimeframeMomentumStrategy"
  timeframe: "1h" # Primary execution timeframe
  parameters:
    higher_timeframe: "4h" # Trend analysis timeframe
    ema_fast_col: "EMA_12"
    ema_slow_col: "EMA_26"
    take_profit_pct: 0.02
```

---

## 2. Strategy Development

### Single Timeframe Strategy

```python
# strategies/my_strategy.py
from .base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self, env, portfolio, **params):
        super().__init__(env, portfolio, **params)
        self.primary_tf = self.env.primary_timeframe

    def buy_signal(self):
        current_data = self.env.now[self.primary_tf]
        if current_data is None:
            return None, None

        # Example: Buy when close > ma20high
        if current_data['close'] > current_data['ma20high']:
            entry_price = current_data['close']
            stop_loss = current_data['close'] * 0.97  # 3% stop
            return entry_price, stop_loss
        return None, None

    def sell_signal(self):
        # Implement short logic if needed
        return None, None

    def close_long_signal(self):
        current_data = self.env.now[self.primary_tf]
        if current_data is None or not self.portfolio.current_trade:
            return None, None

        # Exit conditions
        if current_data['close'] < current_data['ma20low']:
            return current_data['close'], "ma_exit"
        return None, None

    def close_short_signal(self):
        return None, None
```

### Multi-Timeframe Strategy

```python
# strategies/my_multi_tf_strategy.py
from .multi_timeframe_base_strategy import MultiTimeframeBaseStrategy

class MyMultiTFStrategy(MultiTimeframeBaseStrategy):
    def __init__(self, env, portfolio, **params):
        super().__init__(env, portfolio, **params)
        self.primary_tf = self.env.primary_timeframe  # e.g., "1h"
        self.higher_tf = self.params.get("higher_timeframe", "4h")
        self.take_profit_pct = self.params.get("take_profit_pct", 0.02)

    def buy_signal(self):
        # Get data for both timeframes
        primary_data = self.env.now[self.primary_tf]
        higher_tf_data = self.env.now[self.higher_tf]

        if primary_data is None or higher_tf_data is None:
            return None, None

        # Higher timeframe: Check trend
        higher_tf_bullish = higher_tf_data['superTrendDirection'] == 'Buy'

        # Primary timeframe: Entry signal
        primary_signal = primary_data['EMA_12'] > primary_data['EMA_26']

        if higher_tf_bullish and primary_signal:
            entry_price = primary_data['close']
            stop_loss = primary_data['ma20low']  # Use technical level
            return entry_price, stop_loss
        return None, None

    def sell_signal(self):
        # Similar logic for short entries
        return None, None

    def close_long_signal(self):
        primary_data = self.env.now[self.primary_tf]
        if primary_data is None or not self.portfolio.current_trade:
            return None, None

        # Take profit
        take_profit_price = self.portfolio.current_trade["entry_price"] * (1 + self.take_profit_pct)
        if primary_data['close'] >= take_profit_price:
            return primary_data['close'], "take_profit"

        # Stop loss or trend change
        if primary_data['EMA_12'] < primary_data['EMA_26']:
            return primary_data['close'], "trend_change"

        return None, None

    def close_short_signal(self):
        return None, None
```

---

## 3. Risk Management

### Fixed Risk Percentage

The system uses professional risk management where you risk a fixed percentage of your initial capital per trade:

```python
# In config.yaml
portfolio:
  risk_pct: 5  # Risk 5% of initial capital per trade
```

### Position Sizing Formula

```
Position Size = (Capital × Risk%) ÷ (Entry Price - Stop Loss)
```

**Example:**

- Capital: $100,000
- Risk: 5% = $5,000
- Entry: $40,000
- Stop Loss: $38,000
- Risk per share: $2,000
- Position Size: $5,000 ÷ $2,000 = 2.5 BTC

### Stop Loss Strategies

1. **Technical Levels**: Use ma20low, support/resistance
2. **Percentage**: Fixed % from entry (3-5%)
3. **Hybrid**: `max(technical_level, percentage_stop)` for buy orders

---

## 4. Data Access Patterns

### Current Data Access

```python
# Single timeframe
current_data = self.env.now[self.primary_tf]
price = current_data['close']
indicator = current_data['EMA_12']

# Multi-timeframe
primary_data = self.env.now[self.primary_tf]    # e.g., 1h data
higher_data = self.env.now[self.higher_tf]      # e.g., 4h data
```

### Historical Data Access

```python
# Get last N rows for a specific timeframe
historical = self.env.get_historical_data(n=5, timeframe="1h")
yesterday = historical.iloc[-1]  # Previous row
```

---

## 5. Signal Return Format

### Entry Signals (buy_signal/sell_signal)

```python
# New format (recommended)
return entry_price, stop_loss

# Legacy format (still supported)
return entry_price  # Uses default % stop loss
```

### Exit Signals (close_long_signal/close_short_signal)

```python
return exit_price, reason
# or
return None, None  # No exit signal
```

---

## 6. Best Practices

1. **Always check for None data**: `if current_data is None: return None, None`
2. **Validate trade exists**: `if not self.portfolio.current_trade: return None, None`
3. **Use meaningful exit reasons**: "take_profit", "stop_loss", "trend_change"
4. **Test stop loss logic**: Ensure stop_loss < entry_price for buys
5. **Consider timeframe alignment**: Higher TF signals change less frequently

---

## 7. Available Indicators

- **ma20high**, **ma20low**: 20-period moving averages of high/low
- **superTrend**, **superTrendDirection**: SuperTrend indicator and signal
- **EMA_12**, **EMA_26**: Exponential moving averages
- **SMA_X**: Simple moving averages (where X is period)
- **RSI_X**: Relative Strength Index

Add more indicators by updating the `indicators` list in `config.yaml`.
return now['close'], "signal_exit"
return None, None

    def close_short_signal(self):
        return None, None

```

## Key Benefits of this Architecture

1.  **High Performance**: Heavy indicator calculations are done once, upfront, in a highly efficient vectorized operation.
2.  **Maximum Flexibility**: The event-driven loop allows for complex, stateful logic (like trailing stops) that vectorized backtesters struggle with.
3.  **Clean Code**: Strategy logic is simple and readable. It's focused purely on generating signals, not on data manipulation.
4.  **Easy Debugging**: By setting `save_enriched_data: true`, you get a CSV file showing the exact data and indicator values your strategy saw on every single timestep.
```
