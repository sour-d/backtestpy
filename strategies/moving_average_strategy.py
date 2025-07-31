from .base_strategy import BaseStrategy
import pandas as pd

class MovingAverageStrategy(BaseStrategy):
    def __init__(self, env, portfolio, **params):
        super().__init__(env, portfolio, **params)
        self.ma_period = self.params.get('ma_period', 20)
        self.supertrend_period = self.params.get('supertrend_period', 10)
        self.supertrend_multiplier = self.params.get('supertrend_multiplier', 3)
        self.primary_tf = self.env.primary_timeframe

    def _get_current_and_previous_day_data(self):
        """Helper to get today's and yesterday's data."""
        # Get current data from multi-timeframe environment
        current_data = self.env.now[self.primary_tf]
        if current_data is None:
            return None, None
            
        # Get previous data using historical data method
        historical_data = self.env.get_historical_data(2, self.primary_tf)
        if historical_data is None or len(historical_data) < 2:
            return None, None
            
        yesterday = historical_data.iloc[-1]  # Previous row
        return current_data, yesterday

    def _calculate_body(self, day_data):
        """Helper to calculate candle body."""
        return day_data['close'] - day_data['open']

    def buy_signal(self):
        today, yesterday = self._get_current_and_previous_day_data()
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
            
            # Use the closer of ma20low or a 5% stop loss to avoid unrealistically wide stops
            percentage_stop = buying_price * 0.95  # 5% stop loss
            ma_stop = ma20low_today
            
            # Use the tighter stop loss (higher value for buy orders)
            initial_stop_loss = max(percentage_stop, ma_stop)

            if initial_stop_loss >= buying_price:
                return None, None

            return buying_price, initial_stop_loss
        return None, None

    def sell_signal(self):
        today, yesterday = self._get_current_and_previous_day_data()
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
            
            # Use the closer of ma20high or a 5% stop loss to avoid unrealistically wide stops
            percentage_stop = selling_price * 1.05  # 5% stop loss
            ma_stop = ma20high_today
            
            # Use the tighter stop loss (lower value for sell orders)
            initial_stop_loss = min(percentage_stop, ma_stop)

            if initial_stop_loss <= selling_price:
                return None, None

            return selling_price, initial_stop_loss
        return None, None

    def close_long_signal(self):
        today, yesterday = self._get_current_and_previous_day_data()
        if today is None or yesterday is None:
            return None, None

        today_body = self._calculate_body(today)

        ma20high_today = today['ma20high']
        ma20low_today = today['ma20low']
        supertrend_direction_today = today['superTrendDirection']

        # Condition 1 (MA20High Crossover & Negative Body)
        if (
            ma20high_today > today['close']
            and ma20high_today > today['open']
            and today_body < 0
        ):
            return today['close'], "MA20High Crossover & Negative Body"

        # Condition 2 (Consecutive MA20High Crossover & Negative Body)
        ma20high_yesterday = yesterday['ma20high']
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

        ma20high_today = today['ma20high']
        ma20low_today = today['ma20low']
        supertrend_direction_today = today['superTrendDirection']

        # Condition 1 (MA20Low Crossover & Positive Body)
        if (
            today['close'] > ma20low_today
            and today['open'] > ma20low_today
            and today_body > 0
        ):
            return today['close'], "MA20Low Crossover & Positive Body"

        # Condition 2 (Consecutive MA20Low Crossover & Positive Body)
        ma20low_yesterday = yesterday['ma20low']
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
