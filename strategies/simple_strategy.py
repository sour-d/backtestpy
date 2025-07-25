from .base_strategy import BaseStrategy


class SimpleStrategy(BaseStrategy):
    """
    Simple strategy that buys when price is above 20 SMA 
    and sells when price drops below 20 SMA.
    """
    
    def __init__(self, env, sma_period=20, risk_amount=10):
        """
        Initialize the Simple strategy.
        
        Args:
            env: TradingEnvironment instance
            sma_period (int): Period for simple moving average
            risk_amount (float): Fixed risk amount per trade
        """
        super().__init__(env)
        self.sma_period = sma_period
        self.risk_amount = risk_amount
    
    def buy_signal(self) -> dict:
        """
        Generate buy signal when price is above SMA.
        
        Returns:
            dict: Buy signal information or None
        """
        current = self.env.now()
        sma = self.env.simple_moving_average(self.sma_period)
        
        if sma is not None and current["close"] > sma:
            return {
                'should_buy': True,
                'risk_amount': self.risk_amount,
                'price': current["close"]
            }
        
        return None
    
    def sell_signal(self) -> dict:
        """
        Generate sell signal - this simple strategy only does buy trades.
        
        Returns:
            dict: Always None for this strategy
        """
        return None
    
    def liquidate_signal(self) -> dict:
        """
        Generate liquidate signal when price drops below SMA.
        
        Returns:
            dict: Liquidate signal information or None
        """
        current = self.env.now()
        sma = self.env.simple_moving_average(self.sma_period)
        
        if sma is not None and current["close"] < sma:
            return {
                'should_liquidate': True,
                'price': current["close"],
                'action': 'sma_exit'
            }
        
        return None
    
    def _has_sufficient_data(self):
        """
        Check if we have enough data for the moving average.
        
        Returns:
            bool: True if there's sufficient data
        """
        return (self.env.current_step >= self.sma_period and 
                self.env.simple_moving_average(self.sma_period) is not None)
