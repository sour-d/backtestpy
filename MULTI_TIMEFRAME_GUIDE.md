# Multi-Timeframe Strategy Development Guide

## Overview

This backtesting framework supports sophisticated multi-timeframe strategies where you can:

- Analyze trends on higher timeframes (4h, 1d)
- Execute trades on lower timeframes (1h, 5m)
- Use different indicators across timeframes
- Implement professional risk management

## Key Concepts

### Timeframe Hierarchy

- **Higher Timeframe**: Used for trend analysis and market context (e.g., 4h, 1d)
- **Primary Timeframe**: Used for trade execution and precise entry/exit (e.g., 1h, 15m)
- **Data Synchronization**: Framework automatically aligns data across timeframes

### Risk Management

- **Fixed Risk**: Risk a consistent percentage of initial capital per trade
- **Position Sizing**: Automatically calculated based on stop loss distance
- **Professional Approach**: Never risk more than your defined percentage

## Configuration Example

```yaml
trading_pairs:
  - { symbol: "BTC/USDT", timeframes: [
          "1h",
          "4h",
          "1d",
        ], start: "2024-01-01", end: "2024-12-31", prefix: "BTC_2024" } # All timeframes to download

strategy:
  class_name: "MultiTimeframeMomentumStrategy"
  timeframe: "1h" # Primary execution timeframe
  parameters:
    higher_timeframe: "4h" # Trend analysis timeframe
    take_profit_pct: 0.02 # 2% take profit

portfolio:
  risk_pct: 5 # Risk 5% of initial capital per trade
```

## Multi-Timeframe Strategy Template

```python
from .multi_timeframe_base_strategy import MultiTimeframeBaseStrategy

class MyMultiTimeframeStrategy(MultiTimeframeBaseStrategy):
    def __init__(self, env, portfolio, **params):
        super().__init__(env, portfolio, **params)
        self.primary_tf = self.env.primary_timeframe  # From config
        self.higher_tf = self.params.get("higher_timeframe", "4h")
        self.take_profit_pct = self.params.get("take_profit_pct", 0.02)

    def buy_signal(self):
        # Get current data for both timeframes
        primary_data = self.env.now[self.primary_tf]
        higher_data = self.env.now[self.higher_tf]

        if primary_data is None or higher_data is None:
            return None, None

        # Step 1: Check higher timeframe trend
        higher_tf_bullish = higher_data['superTrendDirection'] == 'Buy'

        # Step 2: Check primary timeframe entry signal
        ema_cross_up = primary_data['EMA_12'] > primary_data['EMA_26']

        # Step 3: Combine signals
        if higher_tf_bullish and ema_cross_up:
            entry_price = primary_data['close']
            # Use tighter of technical or percentage stop
            tech_stop = primary_data['ma20low']
            pct_stop = entry_price * 0.97  # 3% stop
            stop_loss = max(tech_stop, pct_stop)  # Tighter stop for buys

            return entry_price, stop_loss

        return None, None

    def sell_signal(self):
        # Similar logic for short entries
        primary_data = self.env.now[self.primary_tf]
        higher_data = self.env.now[self.higher_tf]

        if primary_data is None or higher_data is None:
            return None, None

        higher_tf_bearish = higher_data['superTrendDirection'] == 'Sell'
        ema_cross_down = primary_data['EMA_12'] < primary_data['EMA_26']

        if higher_tf_bearish and ema_cross_down:
            entry_price = primary_data['close']
            tech_stop = primary_data['ma20high']
            pct_stop = entry_price * 1.03  # 3% stop
            stop_loss = min(tech_stop, pct_stop)  # Tighter stop for sells

            return entry_price, stop_loss

        return None, None

    def close_long_signal(self):
        primary_data = self.env.now[self.primary_tf]
        higher_data = self.env.now[self.higher_tf]

        if (primary_data is None or higher_data is None or
            not self.portfolio.current_trade):
            return None, None

        # Take profit
        entry_price = self.portfolio.current_trade["entry_price"]
        take_profit_price = entry_price * (1 + self.take_profit_pct)

        if primary_data['close'] >= take_profit_price:
            return primary_data['close'], "take_profit"

        # Exit on trend change (higher timeframe)
        if higher_data['superTrendDirection'] == 'Sell':
            return primary_data['close'], "higher_tf_trend_change"

        # Exit on signal reversal (primary timeframe)
        if primary_data['EMA_12'] < primary_data['EMA_26']:
            return primary_data['close'], "primary_tf_signal_exit"

        return None, None

    def close_short_signal(self):
        # Similar logic for closing short positions
        primary_data = self.env.now[self.primary_tf]
        higher_data = self.env.now[self.higher_tf]

        if (primary_data is None or higher_data is None or
            not self.portfolio.current_trade):
            return None, None

        entry_price = self.portfolio.current_trade["entry_price"]
        take_profit_price = entry_price * (1 - self.take_profit_pct)

        if primary_data['close'] <= take_profit_price:
            return primary_data['close'], "take_profit"

        if higher_data['superTrendDirection'] == 'Buy':
            return primary_data['close'], "higher_tf_trend_change"

        if primary_data['EMA_12'] > primary_data['EMA_26']:
            return primary_data['close'], "primary_tf_signal_exit"

        return None, None
```

## Common Patterns

### Trend Following

```python
# Higher timeframe confirms trend direction
higher_trend_up = higher_data['superTrendDirection'] == 'Buy'
# Primary timeframe provides entry timing
primary_entry = primary_data['EMA_12'] > primary_data['EMA_26']

if higher_trend_up and primary_entry:
    # Enter long position
```

### Mean Reversion

```python
# Higher timeframe in range/consolidation
higher_tf_ranging = abs(higher_data['EMA_12'] - higher_data['EMA_26']) < threshold
# Primary timeframe oversold/overbought
primary_oversold = primary_data['RSI_14'] < 30

if higher_tf_ranging and primary_oversold:
    # Enter contrarian position
```

### Breakout Strategy

```python
# Higher timeframe approaching resistance
near_resistance = higher_data['close'] > higher_data['ma20high'] * 0.98
# Primary timeframe volume confirmation
volume_surge = primary_data['volume'] > primary_data['volume_sma_20'] * 1.5

if near_resistance and volume_surge:
    # Enter breakout position
```

## Performance Optimizations

### Caching Higher Timeframe Data

```python
def __init__(self, env, portfolio, **params):
    super().__init__(env, portfolio, **params)
    self._higher_tf_cache = None

def _get_higher_tf_data(self):
    """Cache higher timeframe data to avoid repeated lookups."""
    if self._higher_tf_cache is None:
        self._higher_tf_cache = self.env.now.get(self.higher_tf)
    return self._higher_tf_cache

def buy_signal(self):
    # Refresh cache at start of each iteration
    self._higher_tf_cache = None
    higher_data = self._get_higher_tf_data()
    # Use cached data in other methods...
```

## Best Practices

1. **Timeframe Relationship**: Use 3-4x ratio (1h primary + 4h higher, 15m primary + 1h higher)
2. **Signal Hierarchy**: Higher timeframe determines direction, primary timeframe determines timing
3. **Exit Strategy**: Monitor both timeframes for exit signals
4. **Risk Management**: Always use stop losses appropriate for your timeframes
5. **Data Validation**: Always check for None data from both timeframes
6. **Performance**: Cache higher timeframe data when accessed multiple times per iteration

## Common Pitfalls

1. **Conflicting Timeframes**: Don't use primary timeframe higher than trend timeframe
2. **Over-Optimization**: Don't use too many timeframes (2-3 maximum)
3. **Data Misalignment**: Framework handles this, but be aware of timing differences
4. **Risk Scaling**: Higher timeframes may require wider stops, adjust risk accordingly
5. **Signal Lag**: Higher timeframe signals change less frequently than primary timeframe

## Testing Your Strategy

```python
# Test with different timeframe combinations
configurations = [
    {"primary": "1h", "higher": "4h"},
    {"primary": "15m", "higher": "1h"},
    {"primary": "4h", "higher": "1d"}
]

# Compare results across different risk levels
risk_levels = [1, 3, 5]  # 1%, 3%, 5% risk per trade
```
