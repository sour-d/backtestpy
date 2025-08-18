import asyncio
import yaml
import os
from dotenv import load_dotenv
import pandas as pd
import ccxt.pro as ccxtpro
from datetime import datetime

from module.data_manager.live_data_manager import LiveDataStorage
from module.portfolio.portfolio import Portfolio
from module.storage_manager.file_store_manager import FileStoreManager
from module.storage_manager.storage_manager_base import PAPER_DATA_TYPE
from utils.logger import app_logger
from utils.helpers import initialize_strategy

class PaperEngine:
    def __init__(self, config):
        self.config = config
        load_dotenv()

    async def _initialize_components(self):
        paper_config = self.config["paper_trading"]
        portfolio_config = self.config["portfolio"]
        indicator_configs = self.config["indicators"]
        strategy_config = self.config["strategy"]

        symbol = paper_config['symbol']
        timeframe = paper_config['timeframe']
        is_testnet = paper_config.get('testnet', False)
        is_test_mode = paper_config.get('test', False)

        symbol_info = {'symbol': symbol, 'timeframe': timeframe, 'start': datetime.now().strftime('%Y-%m-%d')}
        file_store_manager = FileStoreManager(symbol_info, data_type=PAPER_DATA_TYPE)

        if is_test_mode:
            app_logger.info("Running in Live Simulation Mode")
            try:
                initial_candles_df = pd.read_csv('data/test/raw/btcusdt_4h_all_2025.csv')
                initial_candles_df['datetime'] = pd.to_datetime(initial_candles_df['timestamp'], unit='ms')
                initial_candles = initial_candles_df.values.tolist()
                simulation_data = initial_candles_df
                app_logger.info(f"Loaded {len(initial_candles)} candles from test data")
            except FileNotFoundError:
                app_logger.error("Test data file not found at 'data/test/raw/btcusdt_4h_all_2025.csv'. Exiting.")
                return None, None, None
        else:
            app_logger.info("Running in Live Mode")
            temp_exchange = ccxtpro.bybit({
                'apiKey': os.getenv("BYBIT_API_KEY"),
                'secret': os.getenv("BYBIT_API_SECRET"),
                'options': {'defaultType': 'swap'},
            })
            if is_testnet:
                temp_exchange.set_sandbox_mode(True)

            app_logger.info(f"Fetching initial historical data for {symbol} ({timeframe})...")
            initial_candles_raw = await temp_exchange.fetch_ohlcv(symbol, timeframe, limit=500)
            await temp_exchange.close()
            await asyncio.sleep(1)

            if not initial_candles_raw:
                app_logger.error("Could not fetch initial historical data. Exiting.")
                return None, None, None

            initial_candles_df = pd.DataFrame(initial_candles_raw, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            initial_candles_df['datetime'] = pd.to_datetime(initial_candles_df['timestamp'], unit='ms')
            initial_candles = initial_candles_df.values.tolist()
            simulation_data = None
            app_logger.info(f"Fetched {len(initial_candles)} initial candles")

        data_storage = LiveDataStorage(
            symbol=symbol,
            timeframe=timeframe,
            initial_candles=initial_candles,
            indicator_configs=indicator_configs,
            is_testnet=is_testnet,
            simulation_data=simulation_data,
            logger=app_logger
        )

        portfolio = Portfolio(
            capital=portfolio_config['initial_capital'],
            risk_pct=portfolio_config['risk_pct'],
            fee_pct=portfolio_config['fee_pct'],
            file_store_manager=file_store_manager,
            logger=app_logger
        )

        strategy = initialize_strategy(strategy_config, data_storage, portfolio, app_logger)
        
        return data_storage, portfolio, strategy

    async def run(self):
        app_logger.info("Starting live trading application")
        data_storage, portfolio, strategy = await self._initialize_components()

        if not strategy:
            app_logger.error("Strategy could not be initialized. Exiting.")
            return

        app_logger.info(f"Starting paper trading for {strategy.data_storage.symbol} ({strategy.data_storage.timeframe})...")
        
        if isinstance(data_storage, LiveDataStorage):
            if data_storage.simulation_data is not None:
                # Simulation mode
                while True:
                    current_candle, historical_data = await data_storage.get_next_processed_data()
                    if current_candle is not None:
                        strategy.on_tick()
                    else:
                        break
                portfolio.print_summary()
            else:
                # Live mode
                data_storage.on("new_candle", strategy.on_tick)
                await data_storage.start_live_data()
        
        app_logger.info("Paper trading application finished")
