import pandas as pd


class TradingEnvironment:
    def __init__(self, data, initial_lookback=20):
        self.original_data = data.copy()
        self.data = data.reset_index(drop=True)
        self.current_step = initial_lookback
        self.initial_lookback = initial_lookback

    @property
    def has_data(self):
        return self.current_step < len(self.data) - 1

    @property
    def now(self):
        return self.data.iloc[self.current_step]

    def get_historical_data(self, n):
        if self.current_step - n < 0:
            return None
        return self.data.iloc[self.current_step - n : self.current_step]

    def move(self):
        if self.has_data:
            self.current_step += 1
            return True
        return False

    def get_current_date(self):
        return self.original_data.index[self.current_step]