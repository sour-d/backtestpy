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
        Should return a price or None.
        """
        pass

    @abstractmethod
    def sell_signal(self):
        """
        Define the conditions for entering a short position.
        Should return a price or None.
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

    def _take_position(self, trade_type, price):
        risk_amount = price * self.risk_pct
        self.portfolio.open_position(
            trade_type=trade_type,
            price=price,
            risk_amount=risk_amount,
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
                buy_price = self.buy_signal()
                if buy_price:
                    self._take_position("buy", buy_price)
                else:
                    sell_price = self.sell_signal()
                    if sell_price:
                        self._take_position("sell", sell_price)

            self.env.move()

        # Close any open position at the end of the backtest
        if self.portfolio.current_trade:
            self._liquidate(self.env.now[self.env.primary_timeframe]["close"], reason="end_of_data")

        return self.portfolio.summary()
