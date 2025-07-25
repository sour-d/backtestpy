# Strategy Framework Documentation

## Overview

The strategy framework provides a flexible base class for implementing trading strategies. The base class handles the main trading loop, while child classes only need to implement the specific buy/sell/liquidate logic.

## Base Strategy Class

The `BaseStrategy` class provides:

- **Main trading loop**: Handles data iteration and trade execution
- **Liquidation functionality**: Can exit any current position (buy or sell)
- **Abstract methods**: Forces child classes to implement specific logic
- **Summary printing**: Formatted output of backtest results

## Required Methods to Implement

### 1. `buy_signal(self) -> dict`

Returns buy signal information when conditions are met for a long position.

**Return format:**

```python
{
    'should_buy': bool,      # Whether to execute buy
    'risk_amount': float,    # Risk amount for position sizing
    'price': float          # Entry price
}
```

### 2. `sell_signal(self) -> dict`

Returns sell signal information when conditions are met for a short position.

**Return format:**

```python
{
    'should_sell': bool,     # Whether to execute sell
    'risk_amount': float,    # Risk amount for position sizing
    'price': float          # Entry price
}
```

### 3. `liquidate_signal(self) -> dict`

Returns liquidation signal to exit current position (either buy or sell).

**Return format:**

```python
{
    'should_liquidate': bool, # Whether to liquidate
    'price': float,          # Exit price
    'action': str           # Reason for liquidation
}
```

## Optional Methods to Override

### `_has_sufficient_data(self) -> bool`

Override this to check if there's enough data for your strategy calculations (e.g., for moving averages).

## Available Strategy Examples

### 1. SMACrossoverStrategy

- **Type**: Long-only strategy
- **Logic**: Buys on fast SMA > slow SMA, liquidates on opposite signal or stop loss
- **Parameters**: `fast_period`, `slow_period`, `risk_pct`

### 2. SimpleStrategy

- **Type**: Long-only strategy
- **Logic**: Buys when price > SMA, liquidates when price < SMA
- **Parameters**: `sma_period`, `risk_amount`

### 3. LongShortSMAStrategy

- **Type**: Long/Short strategy
- **Logic**: Goes long on fast SMA > slow SMA, goes short on fast SMA < slow SMA
- **Parameters**: `fast_period`, `slow_period`, `risk_pct`

## Usage Example

```python
from env.trading_env import TradingEnvironment
from utils.data_loader import load_data
from strategies import SMACrossoverStrategy

# Load data and create environment
data = load_data("data/raw/btcusdt_1h.csv")
env = TradingEnvironment(data)

# Initialize strategy
strategy = SMACrossoverStrategy(
    env,
    fast_period=50,
    slow_period=200,
    risk_pct=0.01
)

# Run backtest
summary = strategy.run_backtest()

# Print results
strategy.print_summary(summary)
```

## Manual Liquidation

You can manually liquidate positions using the `liquidate()` method:

```python
# Liquidate at current market price
strategy.liquidate()

# Liquidate at specific price with custom reason
strategy.liquidate(price=50000, action="manual_exit")
```

## Creating Custom Strategies

```python
from strategies.base_strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def __init__(self, env, custom_param=10):
        super().__init__(env)
        self.custom_param = custom_param

    def buy_signal(self):
        # Your buy logic here
        now = self.env.now()
        if your_buy_condition:
            return {
                'should_buy': True,
                'risk_amount': now["close"] * 0.02,
                'price': now["close"]
            }
        return None

    def sell_signal(self):
        # Your sell logic here (or return None for long-only)
        return None

    def liquidate_signal(self):
        # Your exit logic here
        if your_exit_condition:
            return {
                'should_liquidate': True,
                'price': self.env.now()["close"],
                'action': 'custom_exit'
            }
        return None
```

## Key Benefits

1. **Separation of Concerns**: Trading logic is separate from execution logic
2. **Reusability**: Base class handles common operations
3. **Flexibility**: Supports both long-only and long/short strategies
4. **Consistency**: Standardized interface for all strategies
5. **Easy Testing**: Each strategy can be easily backtested and compared
