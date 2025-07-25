# Strategy Framework Documentation (v6)

## Overview

This framework uses a powerful and efficient architecture that combines the flexibility of an event-driven backtester with the performance of pre-calculated indicators.

The workflow is as follows:
1.  **Configuration**: All settings are defined in `config.yaml`.
2.  **Indicator Pre-processing**: Technical indicators are calculated and added to the raw data in one efficient, vectorized step.
3.  **Backtest Execution**: The strategy is run on the "enriched" data using a flexible, step-by-step simulation loop.

This hybrid approach gives you high performance without sacrificing the ability to implement complex, path-dependent trading logic.

---

## 1. Configuration (`config.yaml`)

This is the single control center for your backtest.

```yaml
# --- Data Configuration ---
data:
  filepath: "data/raw/btcusdt_1h.csv"
  save_enriched_data: true # Set to true to save data with indicators for debugging
  enriched_filepath: "data/processed/btcusdt_1h_enriched.csv"

# --- Indicator Pre-processing ---
# Define all indicators you want to use here. They will be pre-calculated.
indicators:
  - { name: "SMA", period: 50 }
  - { name: "SMA", period: 200 }

# --- Portfolio & Strategy Config ---
portfolio:
  initial_capital: 100000
  fee_pct: 0.1

strategy:
  class_name: "SMACrossoverStrategy"
  parameters:
    # Pass the COLUMN NAMES of the indicators to the strategy
    fast_sma_col: "SMA_50"
    slow_sma_col: "SMA_200"
    risk_pct: 0.01
```

---

## 2. Creating a Custom Strategy

Your strategy code is now cleaner than ever. You inherit from `BaseStrategy` and implement the four signal methods. The key difference is that you **no longer calculate indicators inside the strategy**. You simply access them as columns.

### Step 1: Define Indicators in `config.yaml`

First, add the indicators your strategy needs to the `indicators` list in the config file. The `IndicatorProcessor` will automatically add them to the data.

### Step 2: Implement the Strategy

Access the pre-calculated indicator values from the `self.env.now` Series.

```python
# in strategies/my_custom_strategy.py
from .base_strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def __init__(self, env, portfolio, **params):
        super().__init__(env, portfolio, **params)
        # Get the column name from the parameters
        self.my_indicator_col = self.params.get("my_indicator_col")

    def buy_signal(self):
        now = self.env.now
        # Access the indicator value directly from the column
        if now['close'] > now[self.my_indicator_col]:
            return now['close']
        return None

    def sell_signal(self):
        return None

    def close_long_signal(self):
        now = self.env.now
        if now['close'] < now[self.my_indicator_col]:
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