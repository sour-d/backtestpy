import pandas as pd
import pandas_ta as ta

class IndicatorProcessor:
    def __init__(self, data):
        self.data = data.copy()

    def process(self, indicator_configs):
        """
        Processes a list of indicator configurations using pandas-ta.

        :param indicator_configs: A list of dicts, e.g.,
          [{'name': 'sma', 'length': 50}, {'name': 'ema', 'length': 20}]
        """
        for config in indicator_configs:
            name = config.pop("name", "").lower()
            if not name:
                print("Warning: Indicator config missing 'name'.")
                continue

            # Check if the indicator exists in pandas_ta
            if hasattr(self.data.ta, name):
                try:
                    # Call the indicator function with its parameters
                    getattr(self.data.ta, name)(**config, append=True)
                    print(f"Added {name.upper()} with params: {config}")
                except Exception as e:
                    print(f"Error adding indicator '{name}': {e}")
            else:
                print(f"Warning: Indicator '{name}' not recognized by pandas-ta.")

        # Drop rows with NaN values resulting from indicator calculations
        self.data.dropna(inplace=True)
        self.data.reset_index(drop=True, inplace=True)
        return self.data

    def save_to_csv(self, filepath):
        """Saves the enriched DataFrame to a CSV file."""
        self.data.to_csv(filepath, index=False)
        print(f"Enriched data saved to {filepath}")