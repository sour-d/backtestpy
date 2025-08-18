from abc import ABC, abstractmethod
import pandas as pd

class Indicator(ABC):
    """
    Abstract base class for all indicators.
    """
    def __init__(self, **params):
        """
        Initializes the indicator with its parameters.
        It also checks for a 'custom_name' parameter to allow for user-defined column names.
        """
        self.params = params
        # Pop 'custom_name' from params so it's not passed to the calculation logic.
        self.output_name = self.params.pop('custom_name', None)

    @abstractmethod
    def apply(self, data_df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies the indicator calculation to the DataFrame.

        :param data_df: The input DataFrame with market data (OHLCV).
        :return: The DataFrame with the indicator data added.
        """
        pass
