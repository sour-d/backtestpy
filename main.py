import sys
import yaml
import pandas as pd
import importlib
import re
from pathlib import Path
import copy
from calendar import month_name
import json
import asyncio

from data_storage.historical_data_storage import HistoricalDataStorage
from data_store_manager.data_store_manager_base import BACKTEST_DATA_TYPE, RESULT_DATA_TYPE, SUMMARY_DATA_TYPE
from portfolio.portfolio import Portfolio
from utils.backtestHelpers import prepare_data_for_backtest
from data_store_manager.file_store_manager import FileStoreManager # New import


def to_snake_case(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def initialize_components(config, enriched_data, timeframe):
    strategy_config = config["strategy"]
    
    # enriched_data is now a DataFrame directly, not a dictionary
    data_for_strategy = enriched_data

    data_storage = HistoricalDataStorage(data_for_strategy, window_size=500)

    portfolio = Portfolio(
        capital=config["portfolio"]["initial_capital"],
        fee_pct=config["portfolio"]["fee_pct"],
        risk_pct=config["portfolio"]["risk_pct"],
    )

    strategy_class_name = strategy_config["class_name"]
    strategy_params = config["strategy"]["parameters"]
    strategy_module_name = to_snake_case(strategy_class_name)

    strategy_module = importlib.import_module(f"strategies.{strategy_module_name}")
    StrategyClass = getattr(strategy_module, strategy_class_name)
    
    return StrategyClass(data_storage, portfolio, **strategy_params)


async def run_and_save_results(strategy, pair_config):
    print(f"\n--- Running Backtest: {strategy.__class__.__name__} on {pair_config['symbol']} ({pair_config['timeframe']}) ---")
    data_store_manager = FileStoreManager(pair_config, BACKTEST_DATA_TYPE)
    symbol = pair_config['symbol']
    timeframe = pair_config['timeframe']
    summary = await strategy.run_backtest()

    data_store_manager.save_dataframe(pd.DataFrame(summary["trades"]), RESULT_DATA_TYPE)
    data_store_manager.save_json(summary, SUMMARY_DATA_TYPE)
    
    print(f"\n--- Results for {symbol} ({timeframe}) ---")
    strategy.portfolio.print_summary()
    print("--------------------------------------")


async def main():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    backtest_settings = config["backtest_settings"]
    symbols = backtest_settings["symbols"]
    timeframes = backtest_settings["timeframes"]
    periods = backtest_settings["periods"]

    # Initialize the FileStoreManager once for the main loop
    # data_store_manager = FileStoreManager() # No symbol_info needed at init

    for symbol in symbols:
        for timeframe in timeframes:
            for year, months in periods.items():
                if not months:
                    date_range = {"year": year, "months": [], "start": f"{year}-01-01", "end": f"{year}-12-31"}
                    pair_config = {"symbol": symbol, "timeframe": timeframe, "start": date_range["start"], "end": date_range["end"]}
                    enriched_data = prepare_data_for_backtest(pair_config, copy.deepcopy(config["indicators"]))
                    if enriched_data is not None and not enriched_data.empty:
                        strategy = initialize_components(config, enriched_data, timeframe)
                        await run_and_save_results(strategy, pair_config)
                else:
                    for month in months:
                        month_num = list(month_name).index(month.capitalize())
                        start_date = f"{year}-{month_num:02d}-01"
                        end_date = pd.to_datetime(start_date).to_period('M').end_time.strftime('%Y-%m-%d')
                        date_range = {"year": year, "months": [month], "start": start_date, "end": end_date}
                        pair_config = {"symbol": symbol, "timeframe": timeframe, "start": date_range["start"], "end": date_range["end"]}
                        enriched_data = prepare_data_for_backtest(pair_config, copy.deepcopy(config["indicators"]))
                        if enriched_data is not None and not enriched_data.empty:
                            strategy = initialize_components(config, enriched_data, timeframe)
                            await run_and_save_results(strategy, pair_config)

if __name__ == "__main__":
    asyncio.run(main())
