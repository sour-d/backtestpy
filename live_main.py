import asyncio
import yaml
import os
from dotenv import load_dotenv
import pandas as pd
import ccxt.pro as ccxtpro
from datetime import datetime

from data_manager.live_data_manager import LiveDataStorage
from portfolio.portfolio import Portfolio
from strategies.moving_average_strategy import MovingAverageStrategy
from storage_manager.file_store_manager import FileStoreManager
from storage_manager.storage_manager_base import LIVE_DATA_TYPE
from utils.logger import app_logger

async def main():
    app_logger.info("Starting live trading application")
    load_dotenv()
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    live_config = config["live_trading"]
    portfolio_config = config["portfolio"]
    indicator_configs = config["indicators"]
    strategy_config = config["strategy"]
    strategy_params = strategy_config["parameters"]

    symbol = live_config['symbol']
    timeframe = live_config['timeframe']
    is_testnet = live_config.get('testnet', False)
    is_test_mode = live_config.get('test', False)

    # Initialize FileStoreManager for live data
    symbol_info = {'symbol': symbol, 'timeframe': timeframe, 'start': datetime.now().strftime('%Y-%m-%d')}
    file_store_manager = FileStoreManager(symbol_info, data_type=LIVE_DATA_TYPE)

    if is_test_mode:
        app_logger.info("Running in Live Simulation Mode")
        # Load historical data for simulation
        try:
            initial_candles_df = pd.read_csv('data/test/raw/btcusdt_4h_all_2025.csv')
            initial_candles_df['datetime'] = pd.to_datetime(initial_candles_df['timestamp'], unit='ms')
            initial_candles = initial_candles_df.values.tolist()
            simulation_data = initial_candles_df
            app_logger.info(f"Loaded {len(initial_candles)} candles from test data")
        except FileNotFoundError:
            app_logger.error("Test data file not found at 'data/test/raw/btcusdt_4h_all_2025.csv'. Exiting.")
            return
    else:
        app_logger.info("Running in Live Mode")
        # Initialize a temporary exchange instance to fetch initial historical data
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
            return

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

    strategy = MovingAverageStrategy(
        data_storage=data_storage,
        portfolio=portfolio,
        logger=app_logger,
        **strategy_params
    )

    app_logger.info(f"Starting live trading for {symbol} ({timeframe})...")
    
    await strategy.run_simulation()
    portfolio.print_summary()
    app_logger.info("Live trading application finished")

if __name__ == "__main__":
    asyncio.run(main())
