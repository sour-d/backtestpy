import pandas as pd


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

    def process(self, indicator_configs):
        """
        Processes a list of indicator configurations.

        :param indicator_configs: A list of dicts, e.g.,
          [{'name': 'sma', 'period': 50}, {'name': 'ema', 'period': 20}]
        """
        for config in indicator_configs:
            name = config.get("name").lower()
            period = config.get("period")
            if name == "sma":
                self.add_sma(period)
            elif name == "ema":
                self.add_ema(period)
            # Add other indicators here as elif blocks
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
