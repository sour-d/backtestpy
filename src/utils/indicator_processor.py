import pandas as pd
from module.indicators.factory import create_indicator

class IndicatorProcessor:
    def __init__(self, indicator_configs: list):
        """
        Initializes the IndicatorProcessor by creating a list of indicator
        instances based on the provided configurations.
        """
        self.indicators = []
        for config in indicator_configs:
            # Make a copy so we don't modify the original config dict
            config_copy = config.copy()
            name = config_copy.pop("name")
            # The rest of the config dict is now just the parameters
            indicator = create_indicator(name, **config_copy)
            self.indicators.append(indicator)

    def process(self, data_df: pd.DataFrame) -> pd.DataFrame:
        """
        Processes a DataFrame by applying all configured indicators in sequence.
        """
        processed_data = data_df.copy()
        for indicator in self.indicators:
            processed_data = indicator.apply(processed_data)
        return processed_data