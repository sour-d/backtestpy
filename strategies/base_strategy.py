from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    def __init__(self, env, portfolio, **params):
        self.env = env
        self.portfolio = portfolio
        self.params = params
        self.risk_pct = self.params.get("risk_pct", 0.01)

    @abstractmethod
    def buy_signal(self):
        """
        Define the conditions for entering a long position.
        Should return a tuple of (price, stop_loss) or (None, None).
        For backward compatibility, can also return just price or None.
        """
        pass

    @abstractmethod
    def sell_signal(self):
        """
        Define the conditions for entering a short position.
        Should return a tuple of (price, stop_loss) or (None, None).
        For backward compatibility, can also return just price or None.
        """
        pass

    @abstractmethod
    def close_long_signal(self):
        """
        Define the conditions for exiting a long position.
        Should return a tuple of (price, reason) or (None, None).
        """
        pass

    @abstractmethod
    def close_short_signal(self):
        """
        Define the conditions for exiting a short position.
        Should return a tuple of (price, reason) or (None, None).
        """
        pass

    def _take_position(self, trade_type, price, stop_loss=None):
        # Calculate risk per share (difference between entry and stop loss)
        if stop_loss is None:
            # Fallback: use default risk percentage if no stop loss provided
            risk_per_share = price * self.risk_pct
        else:
            risk_per_share = abs(price - stop_loss)
        
        self.portfolio.open_position(
            trade_type=trade_type,
            price=price,
            stop_loss=stop_loss,
            risk_per_share=risk_per_share,
            entry_date=self.env.get_current_date(),
            entry_step=self.env.current_step,
        )

    def _liquidate(self, price, reason="signal_exit"):
        self.portfolio.close_position(
            price=price,
            exit_date=self.env.get_current_date(),
            exit_step=self.env.current_step,
            action=reason,
        )

    def run_backtest(self):
        while self.env.has_data:
            trade = self.portfolio.current_trade
            if trade:
                # Check for exit signals based on trade type
                if trade["type"] == "buy":
                    exit_price, reason = self.close_long_signal()
                    if exit_price:
                        self._liquidate(exit_price, reason)
                elif trade["type"] == "sell":
                    exit_price, reason = self.close_short_signal()
                    if exit_price:
                        self._liquidate(exit_price, reason)
            else:
                # Check for entry signals if not in a trade
                buy_result = self.buy_signal()
                if isinstance(buy_result, tuple) and len(buy_result) == 2:
                    buy_price, stop_loss = buy_result
                    if buy_price:
                        self._take_position("buy", buy_price, stop_loss)
                else:
                    # Handle legacy single return value
                    buy_price = buy_result
                    if buy_price:
                        self._take_position("buy", buy_price)
                
                if not self.portfolio.current_trade:  # Only check sell if no buy position was taken
                    sell_result = self.sell_signal()
                    if isinstance(sell_result, tuple) and len(sell_result) == 2:
                        sell_price, stop_loss = sell_result
                        if sell_price:
                            self._take_position("sell", sell_price, stop_loss)
                    else:
                        # Handle legacy single return value
                        sell_price = sell_result
                        if sell_price:
                            self._take_position("sell", sell_price)

            self.env.move()

        # Close any open position at the end of the backtest
        if self.portfolio.current_trade:
            self._liquidate(self.env.now[self.env.primary_timeframe]["close"], reason="end_of_data")

        return self.portfolio.summary()
