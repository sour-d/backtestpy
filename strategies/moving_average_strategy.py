from .base_strategy import BaseStrategy
import pandas as pd

class MovingAverageStrategy(BaseStrategy):
    def __init__(self, env, portfolio, ma_period=20, supertrend_period=10, supertrend_multiplier=3):
        super().__init__(env, portfolio)
        self.ma_period = ma_period
        self.supertrend_period = supertrend_period
        self.supertrend_multiplier = supertrend_multiplier

    def _get_current_and_previous_day_data(self):
        """Helper to get today's and yesterday's data."""
        if self.env.current_step < 1:
            return None, None
        today = self.env.data.iloc[self.env.current_step]
        yesterday = self.env.data.iloc[self.env.current_step - 1]
        return today, yesterday

    def _calculate_body(self, day_data):
        """Helper to calculate candle body."""
        return day_data['close'] - day_data['open']

    def buy_signal(self):
        today, yesterday = self._get_current_and_previous_day_data()
        if today is None or yesterday is None:
            return None

        today_body = self._calculate_body(today)
        yesterday_body = self._calculate_body(yesterday)

        ma20high_today = today[f'ma{self.ma_period}high']
        ma20low_today = today[f'ma{self.ma_period}low']
        supertrend_direction_today = today['superTrendDirection']

        # Conditions for Buy Order
        if (
            today['close'] > ma20high_today
            and today_body > 0
            and yesterday_body > 0
            and supertrend_direction_today == "Buy"
        ):
            buying_price = today['close']
            initial_stop_loss = ma20low_today

            if initial_stop_loss >= buying_price:
                return None

            return buying_price
        return None

    def sell_signal(self):
        today, yesterday = self._get_current_and_previous_day_data()
        if today is None or yesterday is None:
            return None

        today_body = self._calculate_body(today)
        yesterday_body = self._calculate_body(yesterday)

        ma20high_today = today[f'ma{self.ma_period}high']
        ma20low_today = today[f'ma{self.ma_period}low']
        supertrend_direction_today = today['superTrendDirection']

        # Conditions for Sell Order (Short)
        if (
            today['close'] < ma20low_today
            and today_body < 0
            and yesterday_body < 0
            and supertrend_direction_today == "Sell"
        ):
            selling_price = today['close']
            initial_stop_loss = ma20high_today

            if initial_stop_loss <= selling_price:
                return None

            return selling_price
        return None

    def close_long_signal(self):
        today, yesterday = self._get_current_and_previous_day_data()
        if today is None or yesterday is None:
            return None, None

        today_body = self._calculate_body(today)

        ma20high_today = today[f'ma{self.ma_period}high']
        ma20low_today = today[f'ma{self.ma_period}low']
        supertrend_direction_today = today['superTrendDirection']

        # Condition 1 (MA20High Crossover & Negative Body)
        if (
            ma20high_today > today['close']
            and ma20high_today > today['open']
            and today_body < 0
        ):
            return today['close'], "MA20High Crossover & Negative Body"

        # Condition 2 (Consecutive MA20High Crossover & Negative Body)
        ma20high_yesterday = yesterday[f'ma{self.ma_period}high']
        if (
            ma20high_yesterday > yesterday['close']
            and ma20high_today > today['close']
            and today_body < 0
        ):
            return today['close'], "Consecutive MA20High Crossover & Negative Body"

        # Condition 3 (SuperTrend Sell Signal)
        if supertrend_direction_today == "Sell":
            return today['close'], "SuperTrend Sell Signal"

        return None, None

    def close_short_signal(self):
        today, yesterday = self._get_current_and_previous_day_data()
        if today is None or yesterday is None:
            return None, None

        today_body = self._calculate_body(today)

        ma20high_today = today[f'ma{self.ma_period}high']
        ma20low_today = today[f'ma{self.ma_period}low']
        supertrend_direction_today = today['superTrendDirection']

        # Condition 1 (MA20Low Crossover & Positive Body)
        if (
            today['close'] > ma20low_today
            and today['open'] > ma20low_today
            and today_body > 0
        ):
            return today['close'], "MA20Low Crossover & Positive Body"

        # Condition 2 (Consecutive MA20Low Crossover & Positive Body)
        ma20low_yesterday = yesterday[f'ma{self.ma_period}low']
        if (
            yesterday['close'] > ma20low_yesterday
            and today['close'] > ma20low_today
            and today_body > 0
        ):
            return today['close'], "Consecutive MA20Low Crossover & Positive Body"

        # Condition 3 (SuperTrend Buy Signal)
        if supertrend_direction_today == "Buy":
            return today['close'], "SuperTrend Buy Signal"

        return None, None
