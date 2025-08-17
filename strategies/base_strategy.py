from abc import ABC, abstractmethod
import datetime
from data_manager.data_manager_base import DataStorageBase
from data_manager.historical_data_manager import HistoricalDataStorage
from data_manager.live_data_manager import LiveDataStorage

class BaseStrategy(ABC):
    def __init__(self, data_storage: DataStorageBase, portfolio, logger=None, **params):
        self.data_storage = data_storage
        self.portfolio = portfolio
        self.params = params
        self.risk_pct = self.params.get("risk_pct", 0.01)
        self.trailing_stop_enabled = self.params.get("trailing_stop_enabled", False)
        self.trailing_stop_pct = self.params.get("trailing_stop_pct", 0.02)  # 2% trailing stop
        self.debug_trailing_stops = self.params.get("debug_trailing_stops", False)
        self.logger = logger

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
        if self.logger:
            self.logger.info(f"Trade signal: {trade_type} at {price}")

    def _liquidate(self, price=0, reason="signal_exit"):
        if self.logger:
            self.logger.info(f"Liquidation signal: {reason} at {price}")
        # Use current_candle for liquidation price if not provided
        if price == 0 and self.data_storage.current_candle() is not None:
            price = self.data_storage.current_candle()["close"]

        # For end_of_data, use the last available candle's close price and datetime
        if reason == "end_of_data":
            last_candle = self.data_storage.previous_candle_of(0) # Get the very last candle processed
            if last_candle is not None:
                price = last_candle["close"]
                exit_date = last_candle["datetime"]
                exit_step = self.data_storage.current_step - 1 # Last completed step
            else:
                # Fallback if no candles were processed (e.g., empty data)
                price = 0
                exit_date = datetime.now()
                exit_step = self.data_storage.current_step
            
            self.portfolio.close_position(
                price=price,
                exit_date=exit_date,
                exit_step=exit_step,
                action="end_of_data",
            )
        else:
            self.portfolio.close_position(
                price=price,
                exit_date=self.data_storage.current_date,
                exit_step=self.data_storage.current_step,
                action=reason,
            )

    def _update_trailing_stop(self, trade):
        """Update trailing stop loss based on current price movement, ensuring it doesn't immediately liquidate."""
        if not self.trailing_stop_enabled:
            return

        today = self.data_storage.current_candle()
        current_high = today["high"]
        current_low = today["low"]
        current_close = today["close"]
        current_stop = trade["stop_loss"]
        previous_candle = self.data_storage.previous_candle_of(0)  # Get the last processed candle
        previous_high = previous_candle["high"]
        previous_low = previous_candle["low"]
        previous_close = previous_candle["close"]
        
        # Calculate the potential new stop based purely on the trailing logic
        potential_new_stop = None

        if trade["type"] == "buy":
            # For long positions, trail the stop up when price moves favorably
            potential_new_stop = current_close * (1 - self.trailing_stop_pct)
            
            # Check if this potential new stop is more favorable than the current stop
            if potential_new_stop > current_stop:
                # Now, check if setting this potential_new_stop would cause immediate liquidation
                # For a buy, immediate liquidation means potential_new_stop >= current_close
                if potential_new_stop >= current_close:
                    # If it would liquidate immediately, do NOT update the stop. Keep the old one.
                    if self.logger:
                        self.logger.info(f"Trailing stop (Buy) not updated: Potential {potential_new_stop:.4f} would liquidate immediately (Close: {current_close:.4f}). Keeping old stop {current_stop:.4f}.")
                    return # Keep the old stop
                else:
                    # It's favorable and won't liquidate immediately, so update.
                    new_stop = potential_new_stop
            else:
                # Not favorable, so don't update. Keep the old stop.
                return

        elif trade["type"] == "sell":
            # For short positions, trail the stop down when price moves favorably
            potential_new_stop = current_close * (1 + self.trailing_stop_pct)
            
            # Check if this potential new stop is more favorable than the current stop
            if potential_new_stop < current_stop:
                # Now, check if setting this potential_new_stop would cause immediate liquidation
                # For a sell, immediate liquidation means potential_new_stop <= current_close
                if potential_new_stop <= current_close:
                    # If it would liquidate immediately, do NOT update the stop. Keep the old one.
                    if self.logger:
                        self.logger.info(f"Trailing stop (Sell) not updated: Potential {potential_new_stop:.4f} would liquidate immediately (Close: {current_close:.4f}). Keeping old stop {current_stop:.4f}.")
                    return # Keep the old stop
                else:
                    # It's favorable and won't liquidate immediately, so update.
                    new_stop = potential_new_stop
            else:
                # Not favorable, so don't update. Keep the old stop.
                return
        
        # If we reached here, it means new_stop was assigned a value and should be updated
        if new_stop is not None: # This check is technically redundant now but harmless
            if self.debug_trailing_stops and self.logger:
                self.logger.info(f"📈 Trailing stop updated: {current_stop:.4f} -> {new_stop:.4f} ({trade['type']} position)")
            self.portfolio.update_stop_loss(new_stop)

    def _check_stop_loss(self, trade):
        today = self.data_storage.current_candle()
        stop_loss_hit = False
        
        if trade["type"] == "buy":
            # Condition 1: Price gaps below the stop loss
            if today["open"] <= trade["stop_loss"]:
                if self.logger:
                    self.logger.info(f"Stop loss hit for buy trade at {today['open']} (gap down)")
                self._liquidate(today["open"], "stop_loss")
                stop_loss_hit = True
            # Condition 2: Price hits the stop loss during the day
            elif today["low"] <= trade["stop_loss"]:
                if self.logger:
                    self.logger.info(f"Stop loss hit for buy trade at {trade['stop_loss']}")
                self._liquidate(trade["stop_loss"], "stop_loss")
                stop_loss_hit = True
        elif trade["type"] == "sell":
            # Condition 1: Price gaps above the stop loss
            if today["open"] >= trade["stop_loss"]:
                if self.logger:
                    self.logger.info(f"Stop loss hit for sell trade at {today['open']} (gap up)")
                self._liquidate(today["open"], "stop_loss")
                stop_loss_hit = True
            # Condition 2: Price hits the stop loss during the day
            elif today["high"] >= trade["stop_loss"]:
                if self.logger:
                    self.logger.info(f"Stop loss hit for sell trade at {trade['stop_loss']}")
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

    def _on_tick(self):
        trade = self.portfolio.current_trade
        if trade:
            if not self._check_stop_loss(trade):
                self._check_exit_signals(trade)
        else:
            self._check_entry_signals()


    async def run_backtest(self):
        while self.data_storage.has_more_data:
            # Get the next processed data (current candle and historical data)
            current_candle, historical_data = await self.data_storage.get_next_processed_data()
            
            # If there's no more data, break the loop
            if current_candle is None:
                break

            # Process the tick with the newly received data
            self._on_tick()
            
        if self.portfolio.current_trade:
            self._liquidate(reason="end_of_data")

        return self.portfolio.summary()
    
    async def run_live(self):
        # Subscribe to new_candle events from LiveDataStorage
        if isinstance(self.data_storage, LiveDataStorage):
            self.data_storage.on("new_candle", self._on_live_candle_received)
            await self.data_storage.start_live_data() # Start the data stream
        else:
            raise TypeError("run_live can only be called with LiveDataStorage.")

    async def _on_live_candle_received(self, current_candle, historical_data):
        # This method is called when LiveDataStorage emits a new_candle event
        # The data_storage's internal state (current_candle, historical_data) is already updated
        self._on_tick()

    async def run_simulation(self):
        if isinstance(self.data_storage, HistoricalDataStorage):
            return await self.run_backtest() # HistoricalDataStorage is synchronous
        elif isinstance(self.data_storage, LiveDataStorage):
            # For simulation with LiveDataStorage, we still want to iterate through it
            # but without the infinite loop of run_live. This needs careful handling.
            # We'll iterate by calling get_next_processed_data until no more data.
            while True:
                current_candle, historical_data = await self.data_storage.get_next_processed_data()
                if current_candle is not None:
                    self._on_tick()
                else:
                    break # No more data from dummy source
            return self.portfolio.summary()
        else:
            raise NotImplementedError("Unsupported DataStorage type for run_simulation.")
