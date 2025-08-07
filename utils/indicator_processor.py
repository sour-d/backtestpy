import pandas as pd
from .indicators import ma_high, ma_low, calculate_supertrend, exponential_moving_average

class IndicatorProcessor:
    def __init__(self, indicator_configs: list):
        self.indicator_configs = indicator_configs

    def process(self, data_df: pd.DataFrame) -> pd.DataFrame:
        """
        Processes a DataFrame by adding all configured indicators.
        Returns a new DataFrame with indicators added.
        """
        processed_data = data_df.copy() # Work on a copy

        for config in self.indicator_configs:
            name = config.get("name", "").lower()
            if not name:
                print("Warning: Indicator config missing 'name'.")
                continue

            try:
                if name == "ma_high":
                    period = config.get("period", 20)
                    processed_data[f'ma{period}high'] = ma_high(processed_data, period)
                elif name == "ma_low":
                    period = config.get("period", 20)
                    processed_data[f'ma{period}low'] = ma_low(processed_data, period)
                elif name == "supertrend":
                    period = config.get("period", 10)
                    multiplier = config.get("multiplier", 3)
                    processed_data = calculate_supertrend(processed_data, period, multiplier)
                elif name == "ema":
                    period = config.get("period")
                    if period is None:
                        print(f"Warning: EMA indicator config missing 'period'. Skipping.")
                        continue
                    column = config.get("column", "close")
                    processed_data[f'EMA_{period}'] = exponential_moving_average(processed_data, period, column)
                else:
                    print(f"Warning: Indicator '{name}' not recognized.")
            except Exception as e:
                print(f"Error adding indicator '{name}': {e}")

        return processed_data

    def save_to_csv(self, data_df: pd.DataFrame, filepath):
        """
        Saves the enriched DataFrame to a CSV file.
        This method is primarily for backtesting/debugging.
        """
        data_df.to_csv(filepath, index=False)
        print(f"Enriched data saved to {filepath}")
