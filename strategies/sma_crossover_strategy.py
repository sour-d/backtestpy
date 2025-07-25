from .base_strategy import BaseStrategy


class SMACrossoverStrategy(BaseStrategy):
    """
    Simple Moving Average Crossover Strategy.
    
    Buys when fast SMA crosses above slow SMA.
    Sells when fast SMA crosses below slow SMA.
    Liquidates on stop loss or opposite signal.
    """
    
    def __init__(self, env, fast_period=50, slow_period=200, risk_pct=0.01):
        """
        Initialize the SMA Crossover strategy.
        
        Args:
            env: TradingEnvironment instance
            fast_period (int): Period for fast moving average
            slow_period (int): Period for slow moving average
            risk_pct (float): Risk percentage per trade (as decimal, e.g., 0.01 for 1%)
        """
        super().__init__(env)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.risk_pct = risk_pct
    
    def buy_signal(self) -> dict:
        """
        Generate buy signal when fast SMA crosses above slow SMA.
        
        Returns:
            dict: Buy signal information or None
        """
        now = self.env.now()
        fast_sma = self.env.simple_moving_average(self.fast_period)
        slow_sma = self.env.simple_moving_average(self.slow_period)
        
        # Skip if we don't have enough data for moving averages
        if fast_sma is None or slow_sma is None:
            return None
            
        if fast_sma > slow_sma:
            # Calculate risk amount as percentage of current price
            risk_amount = now["close"] * self.risk_pct
            return {
                'should_buy': True,
                'risk_amount': risk_amount,
                'price': now["close"]
            }
        
        return None
    
    def sell_signal(self) -> dict:
        """
        Generate sell signal when fast SMA crosses below slow SMA.
        
        Returns:
            dict: Sell signal information or None
        """
        now = self.env.now()
        fast_sma = self.env.simple_moving_average(self.fast_period)
        slow_sma = self.env.simple_moving_average(self.slow_period)
        
        # Skip if we don't have enough data for moving averages
        if fast_sma is None or slow_sma is None:
            return None
            
        if fast_sma < slow_sma:
            # Calculate risk amount as percentage of current price
            risk_amount = now["close"] * self.risk_pct
            return {
                'should_sell': True,
                'risk_amount': risk_amount,
                'price': now["close"]
            }
        
        return None
    
    def liquidate_signal(self) -> dict:
        """
        Generate liquidate signal based on stop loss or opposite SMA signal.
        
        Returns:
            dict: Liquidate signal information or None
        """
        now = self.env.now()
        fast_sma = self.env.simple_moving_average(self.fast_period)
        slow_sma = self.env.simple_moving_average(self.slow_period)
        current_trade = self.env.current_trade
        
        # Check stop loss first
        if current_trade["type"] == "buy" and now["low"] < current_trade["stop_loss"]:
            return {
                'should_liquidate': True,
                'price': current_trade["stop_loss"],
                'action': 'stop_loss'
            }
        elif current_trade["type"] == "sell" and now["high"] > current_trade["stop_loss"]:
            return {
                'should_liquidate': True,
                'price': current_trade["stop_loss"],
                'action': 'stop_loss'
            }
        
        # Check for opposite SMA signal
        if fast_sma is not None and slow_sma is not None:
            # If we're in a buy position and fast SMA crosses below slow SMA
            if current_trade["type"] == "buy" and fast_sma < slow_sma:
                return {
                    'should_liquidate': True,
                    'price': now["close"],
                    'action': 'sma_crossover_exit'
                }
            # If we're in a sell position and fast SMA crosses above slow SMA
            elif current_trade["type"] == "sell" and fast_sma > slow_sma:
                return {
                    'should_liquidate': True,
                    'price': now["close"],
                    'action': 'sma_crossover_exit'
                }
        
        return None
    
    def _has_sufficient_data(self):
        """
        Check if we have enough data for both moving averages.
        
        Returns:
            bool: True if there's sufficient data
        """
        return (self.env.current_step >= self.slow_period and 
                self.env.simple_moving_average(self.fast_period) is not None and
                self.env.simple_moving_average(self.slow_period) is not None)
