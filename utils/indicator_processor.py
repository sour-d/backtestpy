import pandas as pd
import numpy as np


class IndicatorProcessor:
    def __init__(self, data):
        self.data = data.copy()

    def add_sma(self, period, column="close"):
        """Adds a Simple Moving Average column to the DataFrame."""
        indicator_name = f"SMA_{period}"
        self.data[indicator_name] = self.data[column].rolling(window=period).mean()
        print(f"Added {indicator_name}")

    def add_ema(self, period, column="close"):
        """Adds an Exponential Moving Average column to the DataFrame."""
        indicator_name = f"EMA_{period}"
        self.data[indicator_name] = (
            self.data[column].ewm(span=period, adjust=False).mean()
        )
        print(f"Added {indicator_name}")

    def add_rsi(self, period=14, column="close"):
        """Adds RSI (Relative Strength Index) using manual calculation."""
        indicator_name = f"RSI_{period}"
        
        # Manual RSI calculation
        delta = self.data[column].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        self.data[indicator_name] = 100 - (100 / (1 + rs))
        print(f"Added {indicator_name}")

    def add_macd(self, fast=12, slow=26, signal=9, column="close"):
        """Adds MACD indicator using manual calculation."""
        # Manual MACD calculation
        ema_fast = self.data[column].ewm(span=fast).mean()
        ema_slow = self.data[column].ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        self.data[f"MACD_{fast}_{slow}"] = macd_line
        self.data[f"MACD_Signal_{signal}"] = signal_line
        self.data[f"MACD_Hist"] = histogram
        print(f"Added MACD ({fast}, {slow}, {signal})")

    def add_bollinger_bands(self, period=20, std_dev=2, column="close"):
        """Adds Bollinger Bands using manual calculation."""
        # Manual Bollinger Bands calculation
        sma = self.data[column].rolling(window=period).mean()
        std = self.data[column].rolling(window=period).std()
        self.data[f"BB_Upper_{period}"] = sma + (std * std_dev)
        self.data[f"BB_Middle_{period}"] = sma
        self.data[f"BB_Lower_{period}"] = sma - (std * std_dev)
        print(f"Added Bollinger Bands ({period}, {std_dev})")

    def add_stochastic(self, k_period=14, d_period=3, column_high="high", column_low="low", column_close="close"):
        """Adds Stochastic Oscillator using manual calculation."""
        # Manual Stochastic calculation
        lowest_low = self.data[column_low].rolling(window=k_period).min()
        highest_high = self.data[column_high].rolling(window=k_period).max()
        k_percent = 100 * ((self.data[column_close] - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        self.data[f"STOCH_K_{k_period}"] = k_percent
        self.data[f"STOCH_D_{d_period}"] = d_percent
        print(f"Added Stochastic ({k_period}, {d_period})")

    def add_atr(self, period=14, column_high="high", column_low="low", column_close="close"):
        """Adds Average True Range using manual calculation."""
        # Manual ATR calculation
        high_low = self.data[column_high] - self.data[column_low]
        high_close = np.abs(self.data[column_high] - self.data[column_close].shift())
        low_close = np.abs(self.data[column_low] - self.data[column_close].shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        self.data[f"ATR_{period}"] = true_range.rolling(window=period).mean()
        print(f"Added ATR ({period})")

    def add_adx(self, period=14, column_high="high", column_low="low", column_close="close"):
        """Adds Average Directional Index - complex manual implementation."""
        # ADX is quite complex to implement manually
        # For now, we'll skip it or implement a simplified version
        print(f"ADX indicator skipped - requires complex manual implementation")
        # If you need ADX, consider installing TA-Lib: pip install TA-Lib

    def process(self, indicator_configs):
        """
        Processes a list of indicator configurations.

        :param indicator_configs: A list of dicts, e.g.,
          [{'name': 'sma', 'period': 50}, {'name': 'ema', 'period': 20}]
        """
        for config in indicator_configs:
            name = config.get("name").lower()
            period = config.get("period", 14)  # Default period
            
            if name == "sma":
                self.add_sma(period)
            elif name == "ema":
                self.add_ema(period)
            elif name == "rsi":
                self.add_rsi(period)
            elif name == "macd":
                fast = config.get("fast", 12)
                slow = config.get("slow", 26)
                signal = config.get("signal", 9)
                self.add_macd(fast, slow, signal)
            elif name == "bollinger" or name == "bb":
                std_dev = config.get("std_dev", 2)
                self.add_bollinger_bands(period, std_dev)
            elif name == "stochastic" or name == "stoch":
                d_period = config.get("d_period", 3)
                self.add_stochastic(period, d_period)
            elif name == "atr":
                self.add_atr(period)
            elif name == "adx":
                self.add_adx(period)
            else:
                print(f"Warning: Indicator '{name}' not recognized.")

        # Drop rows with NaN values resulting from indicator calculations
        self.data.dropna(inplace=True)
        self.data.reset_index(drop=True, inplace=True)
        return self.data

    def save_to_csv(self, filepath):
        """Saves the enriched DataFrame to a CSV file."""
        self.data.to_csv(filepath, index=False)
        print(f"Enriched data saved to {filepath}")
