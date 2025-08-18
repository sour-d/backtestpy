from strategies.multi_timeframe_base_strategy import MultiTimeframeBaseStrategy

class MultiTimeframeMomentumStrategy(MultiTimeframeBaseStrategy):
    def __init__(self, env, portfolio, **params):
        super().__init__(env, portfolio, **params)
        self.primary_tf = self.env.primary_timeframe # e.g., '1h'
        self.higher_tf = self.params.get("higher_timeframe", "4h") # Configurable higher timeframe
        self.ema_fast_col = self.params.get("ema_fast_col", "EMA_12")
        self.ema_slow_col = self.params.get("ema_slow_col", "EMA_26")
        self.take_profit_pct = self.params.get("take_profit_pct", 0.02) # Default to 2%
        
        # Cache for higher timeframe data to avoid repeated lookups
        self._higher_tf_cache = None

    def _get_higher_tf_data(self):
        """Get higher timeframe data with caching."""
        if self._higher_tf_cache is None:
            self._higher_tf_cache = self.env.now.get(self.higher_tf)
        return self._higher_tf_cache

    def _refresh_cache(self):
        """Refresh the higher timeframe cache."""
        self._higher_tf_cache = None

    def _is_higher_tf_bullish(self):
        higher_tf_data = self._get_higher_tf_data()
        if higher_tf_data is not None and higher_tf_data.get('superTrendDirection') == 'Buy':
            return True
        return False

    def _is_higher_tf_bearish(self):
        higher_tf_data = self._get_higher_tf_data()
        if higher_tf_data is not None and higher_tf_data.get('superTrendDirection') == 'Sell':
            return True
        return False

    def buy_signal(self):
        # Refresh cache at the start of each iteration
        self._refresh_cache()
        
        current_data = self.env.now[self.primary_tf]
        if current_data is None:
            return None

        higher_tf_bullish = self._is_higher_tf_bullish()

        # Check higher timeframe momentum
        if not higher_tf_bullish:
            return None

        # Lower timeframe signal: EMA crossover
        if current_data[self.ema_fast_col] > current_data[self.ema_slow_col]:
            return current_data['close']
        return None

    def sell_signal(self):
        current_data = self.env.now[self.primary_tf]
        if current_data is None:
            return None

        higher_tf_bearish = self._is_higher_tf_bearish()
        

        # Check higher timeframe momentum
        if not higher_tf_bearish:
            return None

        # Lower timeframe signal: EMA crossover
        if current_data[self.ema_fast_col] < current_data[self.ema_slow_col]:
            
            return current_data['close']
        return None

    def close_long_signal(self):
        current_data = self.env.now[self.primary_tf]
        if current_data is None:
            return (None, None)

        # Check if there's an active trade
        if not self.portfolio.current_trade:
            return (None, None)

        # Calculate take profit price
        take_profit_price = self.portfolio.current_trade["entry_price"] * (1 + self.take_profit_pct)
        if current_data['close'] >= take_profit_price:
            
            return (current_data['close'], "take_profit")

        # Exit if lower timeframe signal reverses (EMA crossover)
        if current_data[self.ema_fast_col] < current_data[self.ema_slow_col]:
            
            return (current_data['close'], "lower_tf_ema_cross_down")
        
        if self._is_higher_tf_bearish():
            
            return (current_data['close'], "higher_tf_bearish")

        return (None, None)

    def close_short_signal(self):
        current_data = self.env.now[self.primary_tf]
        if current_data is None:
            return (None, None)

        # Check if there's an active trade
        if not self.portfolio.current_trade:
            return (None, None)

        # Calculate take profit price
        take_profit_price = self.portfolio.current_trade["entry_price"] * (1 - self.take_profit_pct)
        if current_data['close'] <= take_profit_price:
            
            return (current_data['close'], "take_profit")

        # Exit if lower timeframe signal reverses (EMA crossover)
        if current_data[self.ema_fast_col] > current_data[self.ema_slow_col]:
            
            return (current_data['close'], "lower_tf_ema_cross_up")

        if self._is_higher_tf_bullish():
            
            return (current_data['close'], "higher_tf_bullish")

        return (None, None)

