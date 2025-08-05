from abc import ABC, abstractmethod
from data_storage.data_storage_base import DataStorageBase

class BaseStrategy(ABC):
    def __init__(self, data_storage: DataStorageBase, portfolio, **params):
        self.data_storage = data_storage
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
        """
        pass

    @abstractmethod
    def sell_signal(self):
        """
        Define the conditions for entering a short position.
        Should return a tuple of (price, stop_loss) or (None, None).
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
            entry_date=self.data_storage.current_date,
            entry_step=self.data_storage.current_step,
        )

    def _liquidate(self, price, reason="signal_exit"):
        self.portfolio.close_position(
            price=price,
            exit_date=self.data_storage.current_date,
            exit_step=self.data_storage.current_step,
            action=reason,
        )

    def _update_trailing_stop(self, trade):
        """Update trailing stop loss based on current price movement."""
        if not self.trailing_stop_enabled:
            return

        today = self.data_storage.current_candle()
        current_high = today["high"]
        current_low = today["low"]
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

    def _check_stop_loss(self, trade):
        today = self.data_storage.current_candle()
        stop_loss_hit = False
        
        if trade["type"] == "buy":
            if today["low"] <= trade["stop_loss"]:
                self._liquidate(trade["stop_loss"], "stop_loss")
                stop_loss_hit = True
        elif trade["type"] == "sell":
            if today["high"] >= trade["stop_loss"]:
                self._liquidate(trade["stop_loss"], "stop_loss")
                stop_loss_hit = True
        
        # Update trailing stop after checking for stop loss
        if not stop_loss_hit:
            self._update_trailing_stop(trade)
        
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
        while self.data_storage.has_more_data:
            trade = self.portfolio.current_trade
            today = self.data_storage.current_candle()
            if trade:
                if not self._check_stop_loss(trade):
                    self._check_exit_signals(trade)
            else:
                self._check_entry_signals()

            self.data_storage.next()

        if self.portfolio.current_trade:
            print("📈 Backtest ended with an open position. Liquidating...")
            self._liquidate(today["close"], reason="end_of_data")

        return self.portfolio.summary()
