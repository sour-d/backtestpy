import pandas as pd


class TradingEnvironment:
    def __init__(self, all_timeframe_data, primary_timeframe, initial_lookback=20):
        self.all_timeframe_data = all_timeframe_data
        self.primary_timeframe = primary_timeframe
        
        # The primary data will drive the iteration
        self.data = self.all_timeframe_data[self.primary_timeframe]
        self.current_step = initial_lookback
        self.initial_lookback = initial_lookback

    @property
    def has_data(self):
        return self.current_step < len(self.data) - 1

    @property
    def now(self):
        # Return a dictionary of current rows for all timeframes
        current_datetime = self.data.index[self.current_step]
        current_rows = {}
        for tf, df in self.all_timeframe_data.items():
            # Find the row in the current timeframe that corresponds to or is just before current_datetime
            # using asof for efficient lookup
            current_rows[tf] = df.asof(current_datetime)
        return current_rows

    def get_historical_data(self, n, timeframe=None):
        if timeframe is None:
            timeframe = self.primary_timeframe
        
        df = self.all_timeframe_data[timeframe]
        current_datetime = self.data.index[self.current_step]
        
        # Find the index in the target timeframe that corresponds to current_datetime
        idx_in_target_tf = df.index.get_loc(current_datetime, method='pad') # 'pad' means use previous if exact not found
        
        if idx_in_target_tf - n < 0:
            return None
        return df.iloc[idx_in_target_tf - n : idx_in_target_tf]

    def move(self):
        if self.has_data:
            self.current_step += 1
            return True
        return False

    def get_current_date(self):
        return self.data.index[self.current_step]

    def get_current_row_for_timeframe(self, timeframe):
        # This is a helper for strategies to get the current row for a specific timeframe
        # It's essentially what 'now' does for a single timeframe
        current_datetime = self.data.index[self.current_step]
        df = self.all_timeframe_data[timeframe]
        return df.asof(current_datetime)

    def get_data_for_timeframe(self, timeframe):
        # Returns the full DataFrame for a given timeframe
        return self.all_timeframe_data.get(timeframe)