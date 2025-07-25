from .base_strategy import BaseStrategy
from utils.indicators import simple_moving_average


class SMACrossoverStrategy(BaseStrategy):
    def __init__(self, env, portfolio, fast_period=50, slow_period=200, risk_pct=0.01):
        super().__init__(env, portfolio, risk_pct)
        self.fast_period = fast_period
        self.slow_period = slow_period

    def _get_indicators(self):
        history = self.env.get_historical_data(self.slow_period)
        if history is None:
            return None, None

        fast_sma = simple_moving_average(history, self.fast_period)
        slow_sma = simple_moving_average(history, self.slow_period)
        return fast_sma, slow_sma

    def buy_signal(self):
        fast_sma, slow_sma = self._get_indicators()
        if fast_sma is not None and slow_sma is not None and fast_sma > slow_sma:
            return self.env.now["close"]
        return None

    def sell_signal(self):
        # This is a long-only strategy
        return None

    def close_long_signal(self):
        now = self.env.now
        trade = self.portfolio.current_trade

        # Stop-loss check
        if now["low"] < trade["stop_loss"]:
            return trade["stop_loss"], "stop_loss"

        # Crossover exit check
        fast_sma, slow_sma = self._get_indicators()
        if fast_sma is not None and slow_sma is not None and fast_sma < slow_sma:
            return now["close"], "sma_crossover_exit"

        return None, None

    def close_short_signal(self):
        # This is a long-only strategy
        return None, None
