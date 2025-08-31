from abc import ABC, abstractmethod
import datetime
from module.data_manager.data_manager_base import DataStorageBase
from module.data_manager.historical_data_manager import HistoricalDataStorage
from module.data_manager.live_data_manager import LiveDataManager


class BaseStrategy(ABC):
    def __init__(self, data_storage: DataStorageBase, portfolio, logger=None, **params):
        self.data_storage = data_storage
        self.portfolio = portfolio
        self.params = params
        self.risk_pct = self.params.get("risk_pct", 0.01)
        self.trailing_stop_enabled = self.params.get("trailing_stop_enabled", False)
        self.trailing_stop_pct = self.params.get(
            "trailing_stop_pct", 0.02
        )  # 2% trailing stop
        self.debug_trailing_stops = self.params.get("debug_trailing_stops", False)
        self.logger = logger
        self.is_live = False
        self.exchange = None

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

    def _calculate_position_size(self, risk_per_share, price):
        """Calculate position size based on fixed risk amount."""
        # Fixed risk amount based on initial capital
        max_risk_amount = self.portfolio.risk_per_trade

        # Calculate max position size based on risk management
        if risk_per_share <= 0:
            return 0

        max_by_risk = max_risk_amount / risk_per_share

        # Calculate max position size based on available capital
        max_by_capital = self.portfolio.capital / price

        # Take the minimum to ensure we don't exceed either constraint
        position_size = min(max_by_risk, max_by_capital)

        return max(0, round(position_size, 2))

    def _take_position(self, trade_type, price, stop_loss=None):
        if stop_loss is None:
            risk_per_share = price * self.risk_pct
            if trade_type == "buy":
                stop_loss = price - risk_per_share
            else:
                stop_loss = price + risk_per_share
        else:
            risk_per_share = abs(price - stop_loss)

        if self.is_live:
            amount = self._calculate_position_size(risk_per_share, price)
            if amount > 0:
                self.logger.info(
                    f"Placing live {trade_type} order for {amount} of {self.data_storage.symbol} at {price}"
                )
                try:
                    self.exchange.create_market_order(
                        symbol=self.data_storage.symbol,
                        side=trade_type,
                        amount=amount,
                        stop_loss=stop_loss,
                    )
                    # In a live scenario, you would ideally wait for the order fill confirmation
                    # and then update the portfolio. For simplicity here, we open the position directly.
                    self.portfolio.open_position(
                        trade_type=trade_type,
                        price=price,
                        stop_loss=stop_loss,
                        risk_per_share=risk_per_share,
                        entry_date=self.data_storage.current_date,
                        entry_step=self.data_storage.current_step,
                    )
                except Exception as e:
                    self.logger.error(f"Failed to place live order: {e}")
            else:
                self.logger.warning("Could not open position, quantity is 0")

        else:
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

        if self.is_live:
            trade = self.portfolio.current_trade
            if trade:
                self.logger.info(
                    f"Placing live order to close {trade['type']} position for {self.data_storage.symbol}"
                )
                try:
                    side = "sell" if trade["type"] == "buy" else "buy"
                    self.exchange.create_market_order(
                        symbol=self.data_storage.symbol,
                        side=side,
                        amount=trade["quantity"],
                        reduce_only=True,
                    )
                    self.portfolio.close_position(
                        price=price,
                        exit_date=self.data_storage.current_date,
                        exit_step=self.data_storage.current_step,
                        action=reason,
                    )
                except Exception as e:
                    self.logger.error(f"Failed to close live position: {e}")

        # For end_of_data, use the last available candle's close price and datetime
        elif reason == "end_of_data":
            last_candle = self.data_storage.previous_candle_of(
                0
            )  # Get the very last candle processed
            if last_candle is not None:
                price = last_candle["close"]
                exit_date = last_candle["datetime"]
                exit_step = self.data_storage.current_step - 1  # Last completed step
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
        previous_candle = self.data_storage.previous_candle_of(
            0
        )  # Get the last processed candle
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
                        self.logger.info(
                            f"Trailing stop (Buy) not updated: Potential {potential_new_stop:.4f} would liquidate immediately (Close: {current_close:.4f}). Keeping old stop {current_stop:.4f}."
                        )
                    return  # Keep the old stop
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
                        self.logger.info(
                            f"Trailing stop (Sell) not updated: Potential {potential_new_stop:.4f} would liquidate immediately (Close: {current_close:.4f}). Keeping old stop {current_stop:.4f}."
                        )
                    return  # Keep the old stop
                else:
                    # It's favorable and won't liquidate immediately, so update.
                    new_stop = potential_new_stop
            else:
                # Not favorable, so don't update. Keep the old stop.
                return

        # If we reached here, it means new_stop was assigned a value and should be updated
        if new_stop is not None:  # This check is technically redundant now but harmless
            if self.debug_trailing_stops and self.logger:
                self.logger.info(
                    f"📈 Trailing stop updated: {current_stop:.4f} -> {new_stop:.4f} ({trade['type']} position)"
                )
            self.portfolio.update_stop_loss(new_stop)

    def _check_stop_loss(self, trade):
        today = self.data_storage.current_candle()
        stop_loss_hit = False

        if trade["type"] == "buy":
            # Condition 1: Price gaps below the stop loss
            if today["open"] <= trade["stop_loss"]:
                if self.logger:
                    self.logger.info(
                        f"Stop loss hit for buy trade at {today['open']} (gap down)"
                    )
                self._liquidate(today["open"], "stop_loss")
                stop_loss_hit = True
            # Condition 2: Price hits the stop loss during the day
            elif today["low"] <= trade["stop_loss"]:
                if self.logger:
                    self.logger.info(
                        f"Stop loss hit for buy trade at {trade['stop_loss']}"
                    )
                self._liquidate(trade["stop_loss"], "stop_loss")
                stop_loss_hit = True
        elif trade["type"] == "sell":
            # Condition 1: Price gaps above the stop loss
            if today["open"] >= trade["stop_loss"]:
                if self.logger:
                    self.logger.info(
                        f"Stop loss hit for sell trade at {today['open']} (gap up)"
                    )
                self._liquidate(today["open"], "stop_loss")
                stop_loss_hit = True
            # Condition 2: Price hits the stop loss during the day
            elif today["high"] >= trade["stop_loss"]:
                if self.logger:
                    self.logger.info(
                        f"Stop loss hit for sell trade at {trade['stop_loss']}"
                    )
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

    def on_tick(self):
        trade = self.portfolio.current_trade
        if trade:
            if not self._check_stop_loss(trade):
                self._check_exit_signals(trade)
        else:
            self._check_entry_signals()

    async def run_backtest(self):
        while self.data_storage.has_more_data:
            # Get the next processed data (current candle and historical data)
            current_candle, historical_data = (
                await self.data_storage.get_next_processed_data()
            )

            # If there's no more data, break the loop
            if current_candle is None:
                break

            # Process the tick with the newly received data
            self.on_tick()

        if self.portfolio.current_trade:
            self._liquidate(reason="end_of_data")

        return self.portfolio.summary()
