from .base_strategy import BaseStrategy
import pandas as pd


class MovingAverageStrategy(BaseStrategy):
    def __init__(self, data_storage, portfolio, **params):
        super().__init__(data_storage, portfolio, **params)
        self.ma_period = self.params.get("ma_period", 20)
        self.supertrend_period = self.params.get("supertrend_period", 10)
        self.supertrend_multiplier = self.params.get("supertrend_multiplier", 3)

    def _calculate_body(self, day_data):
        """Helper to calculate candle body."""
        return day_data["close"] - day_data["open"]

    def buy_signal(self):
        today = self.data_storage.current_candle()
        yesterday = self.data_storage.previous_candle_of(1)

        if today is None or yesterday is None:
            return None, None

        today_body = self._calculate_body(today)
        yesterday_body = self._calculate_body(yesterday)

        ma20high_today = today["ma20high"]
        supertrend_direction_today = today["superTrendDirection"]

        # Conditions for Buy Order
        if (
            today["close"] > ma20high_today
            and today_body > 0
            and yesterday_body > 0
            and supertrend_direction_today == "Buy"
        ):
            buying_price = today["close"]
            initial_stop_loss = buying_price * 0.96  # 4% stop loss with gap buffer

            return buying_price, initial_stop_loss
        return None, None

    def sell_signal(self):
        today = self.data_storage.current_candle()
        yesterday = self.data_storage.previous_candle_of(1)

        if today is None or yesterday is None:
            return None, None

        today_body = self._calculate_body(today)
        yesterday_body = self._calculate_body(yesterday)

        ma20low_today = today["ma20low"]
        supertrend_direction_today = today["superTrendDirection"]

        # Conditions for Sell Order (Short)
        if (
            today["close"] < ma20low_today
            and today_body < 0
            and yesterday_body < 0
            and supertrend_direction_today == "Sell"
        ):
            selling_price = today["close"]
            initial_stop_loss = selling_price * 1.04  # 4% stop loss with gap buffer

            return selling_price, initial_stop_loss
        return None, None

    def close_long_signal(self):
        today = self.data_storage.current_candle()
        yesterday = self.data_storage.previous_candle_of(1)

        if today is None or yesterday is None:
            return None, None

        today_body = self._calculate_body(today)

        ma20high_yesterday = yesterday["ma20high"]
        if ma20high_yesterday > today["low"] and today_body < 0:
            return ma20high_yesterday, "MA20High Crossover & Negative Body"

        return None, None

    def close_short_signal(self):
        today = self.data_storage.current_candle()
        yesterday = self.data_storage.previous_candle_of(1)

        if today is None or yesterday is None:
            return None, None

        today_body = self._calculate_body(today)
        ma20low_yesterday = yesterday["ma20low"]
        if today["high"] > ma20low_yesterday and today_body > 0:
            return ma20low_yesterday, "MA20Low Crossover & Positive Body"

        return None, None
