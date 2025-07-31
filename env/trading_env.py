import pandas as pd


class TradingEnvironment:
    def __init__(self, all_timeframe_data, primary_timeframe, initial_lookback=20):
        self.all_timeframe_data = all_timeframe_data
        self.primary_timeframe = primary_timeframe
        
        # The primary data will drive the iteration
        self.data = self.all_timeframe_data[self.primary_timeframe]
        self.current_step = initial_lookback
        self.initial_lookback = initial_lookback
        
        # Cache for current row data to avoid repeated asof operations
        self._current_rows_cache = None
        self._cache_step = -1

    @property
    def has_data(self):
        return self.current_step < len(self.data) - 1

    @property
    def now(self):
        # Use cached result if we're still on the same step
        if self._cache_step == self.current_step and self._current_rows_cache is not None:
            return self._current_rows_cache
            
        # Return a dictionary of current rows for all timeframes
        current_datetime = self.data.index[self.current_step]
        current_rows = {}
        for tf, df in self.all_timeframe_data.items():
            # Find the row in the current timeframe that corresponds to or is just before current_datetime
            # using asof for efficient lookup
            row = df.asof(current_datetime)
            # Convert Series to dict for easier access, handle NaN case
            if row is not None and not (isinstance(row, pd.Series) and row.isna().all()):
                current_rows[tf] = row.to_dict() if isinstance(row, pd.Series) else row
            else:
                current_rows[tf] = None
        
        # Cache the result
        self._current_rows_cache = current_rows
        self._cache_step = self.current_step
        return current_rows

    def get_historical_data(self, n, timeframe=None):
        if timeframe is None:
            timeframe = self.primary_timeframe
        
        df = self.all_timeframe_data[timeframe]
        current_datetime = self.data.index[self.current_step]
        
        # Find the index in the target timeframe that corresponds to current_datetime
        # Use searchsorted to find the position, then handle edge cases
        try:
            idx_in_target_tf = df.index.get_indexer([current_datetime], method='pad')[0]
            if idx_in_target_tf == -1:  # No valid index found
                return None
        except:
            # Fallback: find the closest index manually
            try:
                idx_in_target_tf = df.index.get_loc(current_datetime)
            except KeyError:
                # If exact match not found, find the nearest previous timestamp
                idx_in_target_tf = df.index.searchsorted(current_datetime) - 1
                if idx_in_target_tf < 0:
                    return None
        
        if idx_in_target_tf - n < 0:
            return None
        return df.iloc[idx_in_target_tf - n : idx_in_target_tf]

    def move(self):
        if self.has_data:
            self.current_step += 1
            # Invalidate cache when moving to next step
            self._current_rows_cache = None
            self._cache_step = -1
            return True
        return False

    def get_current_date(self):
        return self.data.index[self.current_step]

    def get_current_row_for_timeframe(self, timeframe):
        # This is a helper for strategies to get the current row for a specific timeframe
        # It's essentially what 'now' does for a single timeframe
        current_datetime = self.data.index[self.current_step]
        df = self.all_timeframe_data[timeframe]
        row = df.asof(current_datetime)
        # Convert Series to dict for easier access, handle NaN case
        if row is not None and not (isinstance(row, pd.Series) and row.isna().all()):
            return row.to_dict() if isinstance(row, pd.Series) else row
        return None

    def get_data_for_timeframe(self, timeframe):
        # Returns the full DataFrame for a given timeframe
        return self.all_timeframe_data.get(timeframe)