from strategies.base_strategy import BaseStrategy
from abc import abstractmethod

class MultiTimeframeBaseStrategy(BaseStrategy):
    def __init__(self, env, portfolio, **params):
        super().__init__(env, portfolio, **params)
        # The env will now hold a dictionary of dataframes, one for each timeframe
        # The primary timeframe data is still accessible via self.env.data
        # Secondary timeframe data will be accessible via self.env.get_data_for_timeframe(timeframe)

    @abstractmethod
    def buy_signal(self):
        pass

    @abstractmethod
    def sell_signal(self):
        pass

    @abstractmethod
    def close_long_signal(self):
        pass

    @abstractmethod
    def close_short_signal(self):
        pass
