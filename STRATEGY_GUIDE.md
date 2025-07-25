# Strategy Framework Documentation (v4)

## Overview

This framework provides a robust and modular structure for developing and backtesting trading strategies. It is designed with a clean separation of concerns, where the `BaseStrategy` class orchestrates the trading logic, and child classes provide specific entry and exit signals for long and short positions.

- **`TradingEnvironment`**: Acts as the data provider.
- **`Portfolio`**: Manages all financial aspects (capital, trades, P&L).
- **`BaseStrategy`**: The engine that runs the backtest and requires you to implement four signal-generating methods.

## Creating a Custom Strategy

To create a new strategy, you must inherit from `BaseStrategy` and implement four abstract methods, which define your entry and exit logic for both long and short positions.

### 1. Inherit from `BaseStrategy`

```python
from strategies.base_strategy import BaseStrategy
from utils.indicators import simple_moving_average

class MyCustomStrategy(BaseStrategy):
    def __init__(self, env, portfolio, my_param=10):
        super().__init__(env, portfolio)
        self.my_param = my_param
```

### 2. Implement Entry Signals

#### `buy_signal(self)`
Define conditions for entering a **long** position. Return the entry price or `None`.

```python
    def buy_signal(self):
        sma = simple_moving_average(self.env.get_historical_data(20), 20)
        if sma and self.env.now['close'] > sma:
            return self.env.now['close'] # Return price to buy at
        return None
```

#### `sell_signal(self)`
Define conditions for entering a **short** position. Return the entry price or `None`. For long-only strategies, simply `return None`.

```python
    def sell_signal(self):
        return None # This is a long-only strategy
```

### 3. Implement Exit Signals

#### `close_long_signal(self)`
Define conditions for exiting a **long** position. Return a tuple of `(price, reason)` or `(None, None)`.

```python
    def close_long_signal(self):
        now = self.env.now
        trade = self.portfolio.current_trade

        # Stop Loss
        if now['low'] < trade['stop_loss']:
            return trade['stop_loss'], "stop_loss"

        # Signal-based exit
        sma = simple_moving_average(self.env.get_historical_data(20), 20)
        if sma and now['close'] < sma:
            return now['close'], "signal_exit"
            
        return None, None
```

#### `close_short_signal(self)`
Define conditions for exiting a **short** position. Return `(price, reason)` or `(None, None)`. For long-only strategies, simply `return None, None`.

```python
    def close_short_signal(self):
        return None, None # This is a long-only strategy
```

## How It Works

The `run_backtest` method in `BaseStrategy` is the engine. On each candle, it checks if a trade is open.
- If a **long** trade is open, it calls your `close_long_signal()` method.
- If a **short** trade is open, it calls your `close_short_signal()` method.
- If no trade is open, it calls `buy_signal()` and `sell_signal()`.

The base class uses your signals to automatically manage the portfolio.

## Key Benefits of this Architecture

1.  **Maximum Clarity**: Logic is separated by both position type (long/short) and action type (entry/exit). This is a highly organized and readable structure.
2.  **Symmetry**: The method pairs (`buy_signal`/`close_long_signal` and `sell_signal`/`close_short_signal`) create an intuitive and easy-to-understand design.
3.  **Reduced Complexity**: Child strategies are extremely focused. Each method has one, and only one, job to do.