from __future__ import annotations

import os
from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum

from dotenv import load_dotenv
import ccxt
from src.utils.logger import app_logger


class OrderType(Enum):
    """Supported order types."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_MARKET = "STOP_MARKET"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"


class Side(Enum):
    """Order sides."""

    BUY = "BUY"
    SELL = "SELL"


class TimeInForce(Enum):
    """Time in force options."""

    GTC = "GTC"  # Good Till Cancel
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill


class WorkingType(Enum):
    """Working type for stop orders."""

    MARK_PRICE = "MARK_PRICE"
    CONTRACT_PRICE = "CONTRACT_PRICE"


@dataclass
class OrderConfig:
    """Configuration for order placement with sensible defaults."""

    time_in_force: str = "GTC"  # CCXT uses strings
    reduce_only: bool = False
    position_side: Optional[str] = None
    client_order_id: Optional[str] = None
    stop_loss: Optional[float] = None  # Add stop-loss to config
    take_profit: Optional[float] = None  # Add take-profit to config
    params: Dict[str, Any] = field(default_factory=dict)


def _to_ccxt_symbol(symbol: str) -> str:
    """Convert "BTC/USDT" format for CCXT (already correct format)."""
    return symbol.upper()


def build_params(
    symbol: str,
    config: OrderConfig,
    stop_price: Optional[float] = None,
) -> Dict[str, Any]:
    # The above code is a Python docstring that describes the purpose of a function. It states that
    # the function is used to build a CCXT order params dictionary with sensible defaults. This
    # suggests that the function is designed to create a dictionary containing default parameters for
    # placing orders using the CCXT library in Python.
    """Build a CCXT order params dict with sensible defaults."""
    ccxt_symbol = _to_ccxt_symbol(symbol)

    # Build CCXT params
    params = {
        "timeInForce": config.time_in_force,
    }

    if config.reduce_only:
        params["reduceOnly"] = True
    if config.position_side:
        params["positionSide"] = config.position_side
    if config.client_order_id:
        params["clientOrderId"] = config.client_order_id
    if stop_price is not None:
        params["stopPrice"] = stop_price

    # Add any additional params
    params.update(config.params)
    return params


class Exchange:
    """CCXT-based exchange wrapper with unified API.

    Env configuration (via .env):
    - BINANCE_API_KEY
    - BINANCE_API_SECRET
    - BINANCE_TESTNET=true|false

    Supports futures trading with unified order placement including stop-loss.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, logger=None):
        load_dotenv()
        self.logger = logger or app_logger
        self.default_config = {}

        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        testnet = os.getenv("BINANCE_TESTNET", "false").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        # Initialize CCXT Binance client
        self.client = ccxt.binance(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "sandbox": testnet,  # Use testnet if specified
                "options": {
                    "defaultType": "future",  # Use futures by default
                },
            }
        )

        # Enable features
        self.client.load_markets()

    def _get_order_config(self, config: Optional[OrderConfig] = None) -> OrderConfig:
        """Get order configuration with defaults."""
        return config or self.default_config

    def _validate_side(self, side: Union[str, Side]) -> Side:
        """Validate and convert side."""
        if isinstance(side, str):
            try:
                return Side(side.upper())
            except ValueError:
                raise ValueError(f"Invalid side: {side}")
        return side

    def fetch_order_book(
        self, symbol: str, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Fetch futures order book (depth)."""
        try:
            return self.client.fetch_order_book(symbol, limit)
        except Exception as e:
            self.logger.error(f"fetch_order_book error: {e}")
            raise

    def fetch_trades(
        self, symbol: str, since: Optional[int] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch recent public trades for the symbol."""
        try:
            return self.client.fetch_trades(symbol, since, limit)
        except Exception as e:
            self.logger.error(f"fetch_trades error: {e}")
            raise

    def fetch_balance(self, asset: str = "USDT") -> Dict[str, Any]:
        """Fetch a single futures asset balance (default: USDT)."""
        try:
            balance = self.client.fetch_balance()
            return balance.get(asset, {})
        except Exception as e:
            self.logger.error(f"fetch_balance error: {e}")
            raise

    def create_market_order(
        self,
        symbol: str,
        side: Union[str, Side],
        amount: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        reduce_only: bool = False,
        position_side: Optional[str] = None,
        client_order_id: Optional[str] = None,
    ) -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Create a market order with optional stop-loss and take-profit.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'buy' or 'sell'
            amount: Order quantity
            stop_loss: Optional stop-loss price
            take_profit: Optional take-profit price
            reduce_only: Whether this is a reduce-only order
            position_side: Position side for hedge mode (omit for one-way mode)
            client_order_id: Custom order ID

        Returns:
            Single order dict or dict with multiple orders if SL/TP specified
        """
        validated_side = self._validate_side(side)

        try:
            # Build params for market order
            params = {}
            if reduce_only:
                params["reduceOnly"] = True
            if position_side:
                params["positionSide"] = position_side
            if client_order_id:
                params["clientOrderId"] = client_order_id

            self.logger.info(
                f"Creating market order: {symbol} {validated_side.value} {amount}"
            )

            # Place main market order
            main_order = self.client.create_order(
                symbol=symbol,
                type="market",
                side=validated_side.value.lower(),
                amount=amount,
                price=None,
                params=params,
            )

            result = {"main_order": main_order}

            # Add stop-loss if specified
            if stop_loss:
                sl_order = self._create_stop_loss_order(
                    symbol, validated_side, amount, stop_loss, position_side
                )
                result["stop_loss"] = sl_order

            # Add take-profit if specified
            if take_profit:
                tp_order = self._create_take_profit_order(
                    symbol, validated_side, amount, take_profit, position_side
                )
                result["take_profit"] = tp_order

            # Return single order or multiple orders
            return main_order if len(result) == 1 else result

        except Exception as e:
            self.logger.error(f"create_market_order error: {e}")
            raise

    def create_limit_order(
        self,
        symbol: str,
        side: Union[str, Side],
        amount: float,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        reduce_only: bool = False,
        position_side: Optional[str] = None,
        client_order_id: Optional[str] = None,
        time_in_force: str = "GTC",
    ) -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Create a limit order with optional stop-loss and take-profit.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'buy' or 'sell'
            amount: Order quantity
            price: Limit price
            stop_loss: Optional stop-loss price
            take_profit: Optional take-profit price
            reduce_only: Whether this is a reduce-only order
            position_side: Position side for hedge mode (omit for one-way mode)
            client_order_id: Custom order ID
            time_in_force: Time in force (GTC, IOC, FOK)

        Returns:
            Single order dict or dict with multiple orders if SL/TP specified
        """
        validated_side = self._validate_side(side)

        try:
            # Build params for limit order
            params = {"timeInForce": time_in_force}
            if reduce_only:
                params["reduceOnly"] = True
            if position_side:
                params["positionSide"] = position_side
            if client_order_id:
                params["clientOrderId"] = client_order_id

            self.logger.info(
                f"Creating limit order: {symbol} {validated_side.value} {amount} @ {price}"
            )

            # Place main limit order
            main_order = self.client.create_order(
                symbol=symbol,
                type="limit",
                side=validated_side.value.lower(),
                amount=amount,
                price=price,
                params=params,
            )

            result = {"main_order": main_order}

            # Add stop-loss if specified
            if stop_loss:
                sl_order = self._create_stop_loss_order(
                    symbol, validated_side, amount, stop_loss, position_side
                )
                result["stop_loss"] = sl_order

            # Add take-profit if specified
            if take_profit:
                tp_order = self._create_take_profit_order(
                    symbol, validated_side, amount, take_profit, position_side
                )
                result["take_profit"] = tp_order

            # Return single order or multiple orders
            return main_order if len(result) == 1 else result

        except Exception as e:
            self.logger.error(f"create_limit_order error: {e}")
            raise

    def _create_stop_loss_order(
        self,
        symbol: str,
        original_side: Side,
        amount: float,
        stop_price: float,
        position_side: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a stop-loss market order (internal helper)."""
        # Stop-loss is always on the opposite side
        opposite_side = "sell" if original_side == Side.BUY else "buy"

        params = {"reduceOnly": True, "stopPrice": stop_price}
        if position_side:
            params["positionSide"] = position_side

        self.logger.info(f"Creating stop-loss order at {stop_price}")

        return self.client.create_order(
            symbol=symbol,
            type="stop_market",
            side=opposite_side,
            amount=amount,
            price=None,
            params=params,
        )

    def _create_take_profit_order(
        self,
        symbol: str,
        original_side: Side,
        amount: float,
        tp_price: float,
        position_side: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a take-profit limit order (internal helper)."""
        # Take-profit is always on the opposite side
        opposite_side = "sell" if original_side == Side.BUY else "buy"

        params = {"reduceOnly": True, "timeInForce": "GTC"}
        if position_side:
            params["positionSide"] = position_side

        self.logger.info(f"Creating take-profit order at {tp_price}")

        return self.client.create_order(
            symbol=symbol,
            type="limit",
            side=opposite_side,
            amount=amount,
            price=tp_price,
            params=params,
        )

    def update_order(
        self,
        order_id: Union[int, str],
        symbol: str,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Update an order if supported by exchange."""
        try:
            params = {}
            if stop_price is not None:
                params["stopPrice"] = stop_price
            return self.client.edit_order(order_id, symbol, price=price, params=params)
        except Exception as e:
            self.logger.error(f"update_order error: {e}")
            raise

    def cancel_order(self, order_id: Union[int, str], symbol: str) -> Dict[str, Any]:
        """Cancel an order."""
        try:
            return self.client.cancel_order(order_id, symbol)
        except Exception as e:
            self.logger.error(f"cancel_order error: {e}")
            raise

    def cancel_all_orders(self, symbol: str) -> List[Dict[str, Any]]:
        """Cancel all open orders for a symbol."""
        try:
            return self.client.cancel_all_orders(symbol)
        except Exception as e:
            self.logger.error(f"cancel_all_orders error: {e}")
            raise

    def fetch_order(self, order_id: Union[int, str], symbol: str) -> Dict[str, Any]:
        """Fetch a single order by id."""
        try:
            return self.client.fetch_order(order_id, symbol)
        except Exception as e:
            self.logger.error(f"fetch_order error: {e}")
            raise

    def fetch_open_orders(
        self, symbol: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch open orders, optionally filtered by symbol."""
        try:
            return self.client.fetch_open_orders(symbol, None, limit)
        except Exception as e:
            self.logger.error(f"fetch_open_orders error: {e}")
            raise

    def fetch_order_history(
        self, symbol: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch order history for a symbol."""
        try:
            return self.client.fetch_orders(symbol, None, limit)
        except Exception as e:
            self.logger.error(f"fetch_order_history error: {e}")
            raise

    def fetch_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch current positions."""
        try:
            return self.client.fetch_positions([symbol] if symbol else None)
        except Exception as e:
            self.logger.error(f"fetch_positions error: {e}")
            raise

    def fetch_account_info(self) -> Dict[str, Any]:
        """Fetch account information."""
        try:
            return self.client.fetch_balance()
        except Exception as e:
            self.logger.error(f"fetch_account_info error: {e}")
            raise
