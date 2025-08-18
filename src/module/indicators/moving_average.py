import pandas as pd
from .base import Indicator

class MAHighIndicator(Indicator):
    def apply(self, data_df: pd.DataFrame) -> pd.DataFrame:
        period = self.params.get("period", 20)
        column_name = self.output_name or f'ma{period}high'
        data_df[column_name] = data_df['high'].rolling(window=period).mean()
        return data_df

class MALowIndicator(Indicator):
    def apply(self, data_df: pd.DataFrame) -> pd.DataFrame:
        period = self.params.get("period", 20)
        column_name = self.output_name or f'ma{period}low'
        data_df[column_name] = data_df['low'].rolling(window=period).mean()
        return data_df