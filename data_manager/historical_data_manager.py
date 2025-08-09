import pandas as pd
from collections import deque
from datetime import datetime

from .data_manager_base import DataStorageBase

class HistoricalDataStorage(DataStorageBase):
    """
    Implements DataStorageBase for historical backtesting data.
    Provides data sequentially from a pre-loaded DataFrame with a rolling window.
    """
    def __init__(self, data_df: pd.DataFrame, window_size: int = 500):
        super().__init__(pd.DataFrame()) # Initialize DataStorageBase with empty DF
        
        # Ensure datetime column is proper datetime objects
        if 'datetime' in data_df.columns:
            data_df['datetime'] = pd.to_datetime(data_df['datetime'])
        else:
            data_df['datetime'] = pd.to_datetime(data_df['timestamp'], unit='ms')
        
        # Ensure data is sorted by timestamp
        data_df = data_df.sort_values(by='timestamp').reset_index(drop=True)

        self._full_data = data_df # Store the full historical data
        self._current_index = 0 # Index for iterating through _full_data
        self.window_size = window_size
        
        # Initialize the rolling window deque with the first 'window_size' candles
        # or all available data if less than window_size
        initial_window_data = self._full_data.iloc[:min(len(self._full_data), window_size)].values.tolist()
        self._rolling_window = deque(initial_window_data, maxlen=self.window_size)
        
        # The data_df for the IndicatorProcessor will be built from this rolling window
        self.data_df = pd.DataFrame(list(self._rolling_window), columns=data_df.columns) # Preserve columns

    async def get_next_processed_data(self):
        if self.has_more_data:
            # Get the next candle from the full data
            next_candle_raw = self._full_data.iloc[self._current_index]
            self._current_index += 1

            # Add it to the rolling window
            self._rolling_window.append(next_candle_raw.values.tolist())
            
            # Rebuild data_df from the rolling window
            self.data_df = pd.DataFrame(list(self._rolling_window), columns=self._full_data.columns)

            # The current candle is always the last one in the rolling window
            current_candle = self.data_df.iloc[-1]
            historical_data = self.data_df # The entire rolling window is the historical data

            return current_candle, historical_data
        return None, None

    def current_candle(self) -> pd.Series:
        if not self.data_df.empty:
            return self.data_df.iloc[-1]
        return None

    def previous_candle_of(self, day_count: int) -> pd.Series:
        # Access from the rolling window DataFrame
        if len(self.data_df) >= (day_count + 1):
            return self.data_df.iloc[-(day_count + 1)]
        return None

    @property
    def has_more_data(self) -> bool:
        return self._current_index < len(self._full_data)

    @property
    def current_date(self):
        if not self.data_df.empty:
            return self.data_df.iloc[-1]['datetime']
        return None

    @property
    def current_step(self) -> int:
        return self._current_index

    async def connect(self):
        pass # No connection needed for historical data

    async def close(self):
        pass # No connection to close for historical data
