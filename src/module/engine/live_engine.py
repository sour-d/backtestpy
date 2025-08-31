import asyncio
from module.exchange.exchange import Exchange
from module.portfolio.portfolio import Portfolio
from utils.logger import app_logger
from utils.helpers import initialize_strategy
from module.data_manager.live_data_manager import LiveDataManager
from module.storage_manager.storage_manager_base import LIVE_DATA_TYPE

import pandas as pd
import os


class LiveTradingEngine:
    def __init__(self, config, exchange: Exchange, portfolio: Portfolio):
        self.logger = app_logger
        self.config = config
        self.exchange = exchange
        self.portfolio = portfolio
        self.data_manager = None
        self.strategy = None

    @classmethod
    async def create(cls, config, exchange: Exchange):
        portfolio = await cls._initialize_portfolio(config, exchange)
        return cls(config, exchange, portfolio)

    @staticmethod
    async def _initialize_portfolio(config, exchange):
        """
        Fetches the account balance from the exchange and initializes the portfolio.
        """
        try:
            balance_info = await exchange.fetch_balance(
                asset=config.get("capital_asset", "USDT")
            )
            capital = balance_info.get("free", 0)

            if capital <= 0:
                app_logger.error("Insufficient capital to start trading.")
                raise ValueError("Insufficient capital.")

            app_logger.info(f"Initializing portfolio with capital: {capital}")

            return Portfolio(
                capital=capital,
                risk_pct=config.get("risk_pct", 5),
                fee_pct=config.get("fee_pct", 0.1),
                logger=app_logger,
            )
        except Exception as e:
            app_logger.error(f"Failed to initialize portfolio: {e}")
            raise

    async def _initialize_components(self):
        live_config = self.config["live_trading"]
        indicator_configs = self.config["indicators"]
        strategy_config = self.config["strategy"]

        symbol, timeframe = (
            live_config["symbol"],
            live_config["timeframe"],
        )

        self.logger.info(
            f"Fetching initial historical data for {symbol} ({timeframe})..."
        )
        initial_candles_raw = await self.exchange.client.fetch_ohlcv(
            symbol, timeframe, limit=500
        )

        if not initial_candles_raw:
            self.logger.error("Could not fetch initial historical data. Exiting.")
            return

        initial_candles_df = pd.DataFrame(
            initial_candles_raw,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        initial_candles_df["datetime"] = pd.to_datetime(
            initial_candles_df["timestamp"], unit="ms"
        )
        initial_candles = initial_candles_df.values.tolist()
        self.logger.info(f"Fetched {len(initial_candles)} initial candles")

        self.data_manager = LiveDataManager(
            symbol=symbol,
            timeframe=timeframe,
            initial_candles=initial_candles,
            indicator_configs=indicator_configs,
            logger=self.logger,
            
            exchange=self.exchange,
        )

        self.strategy = initialize_strategy(
            strategy_config, self.data_manager, self.portfolio, self.logger
        )
        # Set the engine to live mode
        self.strategy.is_live = True
        self.strategy.exchange = self.exchange

    async def run(self):
        self.logger.info("Initializing components for Live Trading Engine...")
        await self._initialize_components()

        if not self.strategy:
            self.logger.error("Strategy could not be initialized. Exiting.")
            return

        self.logger.info(
            f"Starting live trading for {self.data_manager.symbol} ({self.data_manager.timeframe})..."
        )

        while True:
            try:
                current_candle, _ = await self.data_manager.get_next_processed_data()
                if current_candle is not None:
                    self.logger.info(
                        f"New candle received: {current_candle['datetime']}"
                    )
                    self.strategy.on_tick()
                else:
                    await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"An error occurred in the trading loop: {e}")
                self.logger.info("Retrying in 10 seconds...")
                await asyncio.sleep(10)