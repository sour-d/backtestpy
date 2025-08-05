from .base_strategy import BaseStrategy
import pandas as pd

class MovingAverageStrategy(BaseStrategy):
    def __init__(self, data_storage, portfolio, **params):
        super().__init__(data_storage, portfolio, **params)
        self.ma_period = self.params.get('ma_period', 20)
        self.supertrend_period = self.params.get('supertrend_period', 10)
        self.supertrend_multiplier = self.params.get('supertrend_multiplier', 3)

    def _calculate_body(self, day_data):
        """Helper to calculate candle body."""
        return day_data['close'] - day_data['open']

    def buy_signal(self):
        today = self.data_storage.current_candle()
        yesterday = self.data_storage.previous_candle_of(1)

        if today is None or yesterday is None:
            return None, None

        today_body = self._calculate_body(today)
        yesterday_body = self._calculate_body(yesterday)

        ma20high_today = today['ma20high']
        ma20low_today = today['ma20low']
        supertrend_direction_today = today['superTrendDirection']

        # Conditions for Buy Order
        if (
            today['close'] > ma20high_today
            and today_body > 0
            and yesterday_body > 0
            and supertrend_direction_today == "Buy"
        ):
            buying_price = today['close']
            
            # FIXED: Always use 4% stop loss to account for gap risk
            # Use 4% instead of 5% to leave buffer for gaps
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

        ma20high_today = today['ma20high']
        ma20low_today = today['ma20low']
        supertrend_direction_today = today['superTrendDirection']

        # Conditions for Sell Order (Short)
        if (
            today['close'] < ma20low_today
            and today_body < 0
            and yesterday_body < 0
            and supertrend_direction_today == "Sell"
        ):
            selling_price = today['close']
            
            # FIXED: Always use 4% stop loss to account for gap risk
            # Use 4% instead of 5% to leave buffer for gaps
            initial_stop_loss = selling_price * 1.04  # 4% stop loss with gap buffer

            return selling_price, initial_stop_loss
        return None, None

    def close_long_signal(self):
        today = self.data_storage.current_candle()
        yesterday = self.data_storage.previous_candle_of(1)

        if today is None or yesterday is None:
            return None, None

        today_body = self._calculate_body(today)

        ma20high_today = today['ma20high']
        ma20low_today = today['ma20low']
        supertrend_direction_today = today['superTrendDirection']

        # Condition 1 (MA20High Crossover & Negative Body)
        if (
            ma20high_today > today['low']
            and today_body < 0
        ):
            return ma20high_today, "MA20High Crossover & Negative Body"

        # Condition 2 (Consecutive MA20High Crossover & Negative Body)
        ma20high_yesterday = yesterday['ma20high']
        if (
            ma20high_yesterday > yesterday['low']
            and ma20high_today > today['low']
            and today_body < 0
        ):
            return ma20high_today, "Consecutive MA20High Crossover & Negative Body"

        # Condition 3 (SuperTrend Sell Signal)
        if supertrend_direction_today == "Sell":
            return today['close'], "SuperTrend Sell Signal"

        return None, None

    def close_short_signal(self):
        today = self.data_storage.current_candle()
        yesterday = self.data_storage.previous_candle_of(1)

        if today is None or yesterday is None:
            return None, None

        today_body = self._calculate_body(today)

        ma20high_today = today['ma20high']
        ma20low_today = today['ma20low']
        supertrend_direction_today = today['superTrendDirection']

        # Condition 1 (MA20Low Crossover & Positive Body)
        if (
            today['high'] > ma20low_today
            and today_body > 0
        ):
            return ma20low_today, "MA20Low Crossover & Positive Body"

        # Condition 2 (Consecutive MA20Low Crossover & Positive Body)
        ma20low_yesterday = yesterday['ma20low']
        if (
            yesterday['high'] > ma20low_yesterday
            and today['high'] > ma20low_today
            and today_body > 0
        ):
            return ma20low_today, "Consecutive MA20Low Crossover & Positive Body"

        # Condition 3 (SuperTrend Buy Signal)
        if supertrend_direction_today == "Buy":
            return today['close'], "SuperTrend Buy Signal"

        return None, None
