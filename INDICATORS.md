# Technical Indicators - Pure Pandas Implementation

## What's Available

Your backtesting framework now supports these technical indicators using **pure pandas/numpy implementations** - no external libraries required!

### 📈 **Trend Indicators**

- **SMA/EMA**: Simple & Exponential Moving Averages
- ~~**ADX**: Average Directional Index~~ (skipped - complex implementation)

### ⚡ **Momentum Indicators**

- **RSI**: Relative Strength Index (overbought/oversold)
- **MACD**: Moving Average Convergence Divergence
- **Stochastic**: %K and %D oscillator

### 📊 **Volatility Indicators**

- **Bollinger Bands**: Price channels with standard deviation
- **ATR**: Average True Range (volatility measure)

## Example Configuration

```yaml
indicators:
  # Moving Averages
  - { name: "SMA", period: 50 }
  - { name: "EMA", period: 21 }

  # Momentum
  - { name: "RSI", period: 14 }
  - { name: "MACD", fast: 12, slow: 26, signal: 9 }
  - { name: "Stochastic", period: 14, d_period: 3 }

  # Volatility
  - { name: "Bollinger", period: 20, std_dev: 2 }
  - { name: "ATR", period: 14 }
```

## Example Advanced Strategy

```python
class AdvancedStrategy(BaseStrategy):
    def buy_signal(self):
        now = self.env.now

        # Multi-indicator buy signal
        rsi_oversold = now['RSI_14'] < 30
        macd_bullish = now['MACD_12_26'] > now['MACD_Signal_9']
        above_bb_middle = now['close'] > now['BB_Middle_20']
        low_volatility = now['ATR_14'] < now['ATR_14'].rolling(20).mean()

        if rsi_oversold and macd_bullish and above_bb_middle and low_volatility:
            return now['close']
        return None

    def close_long_signal(self):
        now = self.env.now

        # Exit conditions
        rsi_overbought = now['RSI_14'] > 70
        price_at_bb_upper = now['close'] >= now['BB_Upper_20']

        if rsi_overbought or price_at_bb_upper:
            return now['close'], "profit_take"
        return None, None
```

## Performance Benefits

✅ **Pure Pandas**: No external library dependencies or compatibility issues
✅ **Vectorized Calculations**: All indicators use optimized pandas/numpy operations  
✅ **Lightweight**: Minimal dependencies - just pandas and numpy
✅ **Reliable**: No version conflicts or installation issues
✅ **Fast**: Efficient implementations using pandas' optimized operations

## Available Indicators

| Indicator       | Implementation                      | Status        |
| --------------- | ----------------------------------- | ------------- |
| SMA             | ✅ Pure pandas rolling mean         | Working       |
| EMA             | ✅ Pure pandas EWM                  | Working       |
| RSI             | ✅ Manual calculation with pandas   | Working       |
| MACD            | ✅ EMA-based calculation            | Working       |
| Bollinger Bands | ✅ SMA + standard deviation         | Working       |
| Stochastic      | ✅ High/low range calculation       | Working       |
| ATR             | ✅ True range with rolling mean     | Working       |
| ADX             | ❌ Skipped (complex implementation) | Not available |

## Why This Approach?

1. **Simplicity**: No complex library installations
2. **Reliability**: No dependency conflicts
3. **Performance**: Pandas is already optimized for these operations
4. **Maintainability**: Easy to understand and modify the calculations
5. **Compatibility**: Works with any pandas/numpy version

Your framework now provides professional-grade technical analysis with zero external dependencies! 🚀
