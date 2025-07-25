# Advanced Indicators Example

## What's Now Available

Your backtesting framework now supports these advanced indicators:

### 📈 **Trend Indicators**

- **SMA/EMA**: Simple & Exponential Moving Averages
- **ADX**: Average Directional Index (trend strength)

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

  # Trend Strength
  - { name: "ADX", period: 14 }
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
        strong_trend = now['ADX_14'] > 25

        if rsi_oversold and macd_bullish and above_bb_middle and strong_trend:
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

✅ **Vectorized Calculations**: All indicators use optimized pandas/numpy operations
✅ **Library Integration**: Fallback to TA-Lib when available for even better performance  
✅ **Manual Implementations**: Pure pandas calculations when libraries aren't available
✅ **Flexible Configuration**: Easy to add/remove indicators via config.yaml

## Available Libraries Status

- ✅ **pandas-ta**: Installed and available
- ✅ **ta**: Installed and available
- ❌ **TA-Lib**: Not installed (requires system dependencies)

To install TA-Lib (optional, for maximum performance):

```bash
# On Ubuntu/Debian:
sudo apt-get install build-essential
pip install TA-Lib

# On macOS:
brew install ta-lib
pip install TA-Lib
```

Your framework now supports professional-grade technical analysis! 🚀
