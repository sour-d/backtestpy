from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    def __init__(self, env, portfolio, **params):
        self.env = env
        self.portfolio = portfolio
        self.params = params
        self.risk_pct = self.params.get("risk_pct", 0.01)
        self.trailing_stop_enabled = self.params.get("trailing_stop_enabled", False)
        self.trailing_stop_pct = self.params.get("trailing_stop_pct", 0.02)  # 2% trailing stop
        self.debug_trailing_stops = self.params.get("debug_trailing_stops", False)

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
        if stop_loss is None:
            risk_per_share = price * self.risk_pct
            if trade_type == "buy":
                stop_loss = price - risk_per_share
            else:
                stop_loss = price + risk_per_share
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

    def _update_trailing_stop(self, trade, current_candle):
        """Update trailing stop loss based on current price movement."""
        if not self.trailing_stop_enabled:
            return
            
        current_high = current_candle["high"]
        current_low = current_candle["low"]
        current_stop = trade["stop_loss"]
        new_stop = None
        
        if trade["type"] == "buy":
            # For long positions, trail the stop up when price moves favorably
            new_trailing_stop = current_high * (1 - self.trailing_stop_pct)
            
            # Only update if the new trailing stop is higher than current stop
            if new_trailing_stop > current_stop:
                new_stop = new_trailing_stop
                
        elif trade["type"] == "sell":
            # For short positions, trail the stop down when price moves favorably
            new_trailing_stop = current_low * (1 + self.trailing_stop_pct)
            
            # Only update if the new trailing stop is lower than current stop
            if new_trailing_stop < current_stop:
                new_stop = new_trailing_stop
        
        # Update the stop loss in the portfolio
        if new_stop is not None:
            if self.debug_trailing_stops:
                print(f"📈 Trailing stop updated: {current_stop:.4f} -> {new_stop:.4f} ({trade['type']} position)")
            self.portfolio.update_stop_loss(new_stop)

    def _check_stop_loss(self, trade, current_candle):
        stop_loss_hit = False
        
        if trade["type"] == "buy":
            if current_candle["low"] <= trade["stop_loss"]:
                self._liquidate(trade["stop_loss"], "stop_loss")
                stop_loss_hit = True
        elif trade["type"] == "sell":
            if current_candle["high"] >= trade["stop_loss"]:
                self._liquidate(trade["stop_loss"], "stop_loss")
                stop_loss_hit = True
        
        # Update trailing stop after checking for stop loss
        if not stop_loss_hit:
            self._update_trailing_stop(trade, current_candle)
        
        return stop_loss_hit

    def _check_exit_signals(self, trade):
        """Check for strategy-based exit signals. Returns True if position was closed."""
        if trade["type"] == "buy":
            exit_price, reason = self.close_long_signal()
            if exit_price:
                self._liquidate(exit_price, reason)
                return True
        elif trade["type"] == "sell":
            exit_price, reason = self.close_short_signal()
            if exit_price:
                self._liquidate(exit_price, reason)
                return True
        return False

    def _check_entry_signals(self):
        if not self.portfolio.current_trade:
            buy_result = self.buy_signal()
            if isinstance(buy_result, tuple) and len(buy_result) == 2:
                buy_price, stop_loss = buy_result
                if buy_price:
                    self._take_position("buy", buy_price, stop_loss)
            else:
                buy_price = buy_result
                if buy_price:
                    self._take_position("buy", buy_price)

        if not self.portfolio.current_trade:
            sell_result = self.sell_signal()
            if isinstance(sell_result, tuple) and len(sell_result) == 2:
                sell_price, stop_loss = sell_result
                if sell_price:
                    self._take_position("sell", sell_price, stop_loss)
            else:
                sell_price = sell_result
                if sell_price:
                    self._take_position("sell", sell_price)

    def run_backtest(self):
        while self.env.has_data:
            trade = self.portfolio.current_trade
            if trade:
                current_candle = self.env.now[self.env.primary_timeframe]
                
                if not self._check_stop_loss(trade, current_candle):
                    self._check_exit_signals(trade)
            else:
                self._check_entry_signals()

            self.env.move()

        if self.portfolio.current_trade:
            self._liquidate(self.env.now[self.env.primary_timeframe]["close"], reason="end_of_data")

        return self.portfolio.summary()
