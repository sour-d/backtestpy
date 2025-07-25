from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """
    Base class for trading strategies.
    
    Child classes must implement buy_signal and sell_signal methods
    to define their trading logic.
    """
    
    def __init__(self, env):
        """
        Initialize the strategy with a trading environment.
        
        Args:
            env: TradingEnvironment instance
        """
        self.env = env
        
    @abstractmethod
    def buy_signal(self) -> dict:
        """
        Define buy signal logic.
        
        Returns:
            dict: {
                'should_buy': bool,
                'risk_amount': float,
                'price': float
            } or None if no buy signal
        """
        pass
    
    @abstractmethod
    def sell_signal(self) -> dict:
        """
        Define sell signal logic.
        
        Returns:
            dict: {
                'should_sell': bool,
                'risk_amount': float,
                'price': float
            } or None if no sell signal
        """
        pass
    
    @abstractmethod
    def liquidate_signal(self) -> dict:
        """
        Define liquidation signal logic for exiting current positions.
        
        Returns:
            dict: {
                'should_liquidate': bool,
                'price': float,
                'action': str
            } or None if no liquidation signal
        """
        pass
    
    def execute_step(self):
        """
        Execute one step of the strategy.
        
        This method handles the main trading logic flow:
        1. Check for buy/sell signals when not in trade
        2. Check for liquidation signals when in trade
        3. Execute the trades based on signals
        """
        now = self.env.now()
        
        if not self.env.current_trade:
            # Check for buy signal
            buy_signal = self.buy_signal()
            if buy_signal and buy_signal.get('should_buy', False):
                self.env.take_position(
                    risk=buy_signal['risk_amount'],
                    price=buy_signal['price'],
                    trade_type="buy"
                )
                return
            
            # Check for sell signal
            sell_signal = self.sell_signal()
            if sell_signal and sell_signal.get('should_sell', False):
                self.env.take_position(
                    risk=sell_signal['risk_amount'],
                    price=sell_signal['price'],
                    trade_type="sell"
                )
        else:
            # Check for liquidation signal
            liquidate_signal = self.liquidate_signal()
            if liquidate_signal and liquidate_signal.get('should_liquidate', False):
                self.env.exit_position(
                    price=liquidate_signal['price'],
                    action=liquidate_signal.get('action', 'liquidate')
                )
    
    def liquidate(self, price=None, action="manual_liquidate"):
        """
        Manually liquidate the current position.
        
        Args:
            price (float, optional): Price to liquidate at. If None, uses current close price.
            action (str): Reason for liquidation
        """
        if self.env.current_trade:
            liquidation_price = price if price is not None else self.env.now()["close"]
            self.env.exit_position(price=liquidation_price, action=action)
    
    def run_backtest(self):
        """
        Run the complete backtest using this strategy.
        
        Returns:
            dict: Summary of the backtest results
        """
        while self.env.has_data():
            # Check if we have enough data for the strategy calculations
            if self._has_sufficient_data():
                self.execute_step()
            
            self.env.move()
        
        # Close any open position at the end
        if self.env.current_trade:
            final_price = self.env.now()["close"]
            print(f"Closing open position at end of backtest at price: {final_price}")
            self.liquidate(price=final_price, action="end_of_data")
        
        return self.env.summary()
    
    def _has_sufficient_data(self):
        """
        Override this method in child classes if you need to check
        for sufficient data before executing strategy logic.
        
        Returns:
            bool: True if there's sufficient data to execute the strategy
        """
        return True
    
    def print_summary(self, summary):
        """
        Print a formatted summary of the backtest results.
        
        Args:
            summary (dict): Summary dictionary from env.summary()
        """
        print(f"Final Capital: {summary['final_capital']:.2f}")
        print(f"Profit: {summary['profit']:.2f}")
        print(f"Total Trades: {summary['total_trades']}")
        print(f"Total Fees Paid: {summary['total_fees_paid']:.2f}")
        print(f"Net Profit After Fees: {summary['net_profit_after_fees']:.2f}")
