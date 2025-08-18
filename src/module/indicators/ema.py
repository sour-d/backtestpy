import pandas as pd
from .base import Indicator

class EMAIndicator(Indicator):
    def apply(self, data_df: pd.DataFrame) -> pd.DataFrame:
        period = self.params.get("period")
        if period is None:
            raise ValueError("EMA indicator requires a 'period' parameter.")
        
        column = self.params.get("column", "close")
        column_name = self.output_name or f'EMA_{period}'
        data_df[column_name] = data_df[column].ewm(span=period, adjust=False).mean()
        return data_df
