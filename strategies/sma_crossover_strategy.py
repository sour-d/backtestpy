from .base_strategy import BaseStrategy


class SMACrossoverStrategy(BaseStrategy):
    def __init__(self, env, portfolio, **params):
        super().__init__(env, portfolio, **params)
        self.fast_sma_col = self.params.get("fast_sma_col", "SMA_50")
        self.slow_sma_col = self.params.get("slow_sma_col", "SMA_200")

    def buy_signal(self):
        now = self.env.now
        if now[self.fast_sma_col] > now[self.slow_sma_col]:
            return now["close"]
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
        if now[self.fast_sma_col] < now[self.slow_sma_col]:
            return now["close"], "sma_crossover_exit"

        return None, None

    def close_short_signal(self):
        # This is a long-only strategy
        return None, None
