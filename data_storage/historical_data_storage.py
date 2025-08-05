import pandas as pd
from collections import deque
from datetime import datetime

from .data_storage_base import DataStorageBase

class HistoricalDataStorage(DataStorageBase):
    """
    Implements DataStorageBase for historical backtesting data.
    Provides data sequentially from a pre-loaded DataFrame.
    """
    def __init__(self, data_df: pd.DataFrame):
        super().__init__(data_df)
        self._current_step = 0
        if 'datetime' in self.data_df.columns:
            self.data_df['datetime'] = pd.to_datetime(self.data_df['datetime'])
        else:
            self.data_df['datetime'] = pd.to_datetime(self.data_df['timestamp'], unit='ms')
        
        self.data_df = self.data_df.sort_values(by='timestamp').reset_index(drop=True)

    def next(self):
        if self.has_more_data:
            self._current_step += 1

    def current_candle(self) -> pd.Series:
        if self.has_more_data:
            return self.data_df.iloc[self._current_step]
        return None

    def previous_candle_of(self, day_count: int) -> pd.Series:
        if self._current_step - day_count >= 0:
            return self.data_df.iloc[self._current_step - day_count]
        return None

    @property
    def has_more_data(self) -> bool:
        return self._current_step < len(self.data_df)

    @property
    def current_date(self):
        if self.has_more_data:
            return self.data_df.iloc[self._current_step]['datetime']
        return None

    @property
    def current_step(self) -> int:
        return self._current_step