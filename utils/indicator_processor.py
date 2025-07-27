import pandas as pd
from .indicators import ma_high, ma_low, calculate_supertrend, exponential_moving_average

class IndicatorProcessor:
    def __init__(self, data):
        self.data = data.copy()

    def process(self, indicator_configs):
        """
        Processes a list of indicator configurations.

        :param indicator_configs: A list of dicts, e.g.,
          [{'name': 'ma_high', 'period': 20}, {'name': 'supertrend', 'period': 10, 'multiplier': 3}]
        """
        for config in indicator_configs:
            name = config.get("name", "").lower()
            if not name:
                print("Warning: Indicator config missing 'name'.")
                continue

            try:
                if name == "ma_high":
                    period = config.get("period", 20)
                    self.data[f'ma{period}high'] = ma_high(self.data, period)
                elif name == "ma_low":
                    period = config.get("period", 20)
                    self.data[f'ma{period}low'] = ma_low(self.data, period)
                elif name == "supertrend":
                    period = config.get("period", 10)
                    multiplier = config.get("multiplier", 3)
                    self.data = calculate_supertrend(self.data, period, multiplier)
                elif name == "ema":
                    period = config.get("period")
                    if period is None:
                        print(f"Warning: EMA indicator config missing 'period'. Skipping.")
                        continue
                    column = config.get("column", "close")
                    self.data[f'EMA_{period}'] = exponential_moving_average(self.data, period, column)
                else:
                    print(f"Warning: Indicator '{name}' not recognized.")
            except Exception as e:
                print(f"Error adding indicator '{name}': {e}")

        # Drop rows with NaN values resulting from indicator calculations
        self.data.dropna(inplace=True) # Re-enable dropping NaNs
        self.data.reset_index(drop=True, inplace=True)
        return self.data

    def save_to_csv(self, filepath):
        """Saves the enriched DataFrame to a CSV file."""
        self.data.to_csv(filepath, index=False)
        print(f"Enriched data saved to {filepath}")