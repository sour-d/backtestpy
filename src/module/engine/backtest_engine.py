import yaml
import pandas as pd
import importlib
import re
import copy
from calendar import month_name
import asyncio

from module.data_manager.historical_data_manager import HistoricalDataStorage
from module.storage_manager.storage_manager_base import BACKTEST_DATA_TYPE, RESULT_DATA_TYPE, SUMMARY_DATA_TYPE
from module.portfolio.portfolio import Portfolio
from utils.backtestHelpers import prepare_data_for_backtest
from module.storage_manager.file_store_manager import FileStoreManager

from utils.helpers import initialize_strategy

class BacktestEngine:
    def __init__(self, config):
        self.config = config

    def _initialize_components(self, enriched_data, timeframe):
        strategy_config = self.config["strategy"]
        
        data_for_strategy = enriched_data
        data_storage = HistoricalDataStorage(data_for_strategy, window_size=500)

        portfolio = Portfolio(
            capital=self.config["portfolio"]["initial_capital"],
            fee_pct=self.config["portfolio"]["fee_pct"],
            risk_pct=self.config["portfolio"]["risk_pct"],
        )

        return initialize_strategy(strategy_config, data_storage, portfolio)

    async def _run_and_save_results(self, strategy, pair_config):
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

    async def run(self):
        backtest_settings = self.config["backtest_settings"]
        symbols = backtest_settings["symbols"]
        timeframes = backtest_settings["timeframes"]
        periods = backtest_settings["periods"]

        for symbol in symbols:
            for timeframe in timeframes:
                for year, months in periods.items():
                    if not months:
                        date_range = {"year": year, "months": [], "start": f"{year}-01-01", "end": f"{year}-12-31"}
                        pair_config = {"symbol": symbol, "timeframe": timeframe, "start": date_range["start"], "end": date_range["end"]}
                        enriched_data = prepare_data_for_backtest(pair_config, copy.deepcopy(self.config["indicators"]))
                        if enriched_data is not None and not enriched_data.empty:
                            strategy = self._initialize_components(enriched_data, timeframe)
                            await self._run_and_save_results(strategy, pair_config)
                    else:
                        for month in months:
                            month_num = list(month_name).index(month.capitalize())
                            start_date = f"{year}-{month_num:02d}-01"
                            end_date = pd.to_datetime(start_date).to_period('M').end_time.strftime('%Y-%m-%d')
                            date_range = {"year": year, "months": [month], "start": start_date, "end": end_date}
                            pair_config = {"symbol": symbol, "timeframe": timeframe, "start": date_range["start"], "end": date_range["end"]}
                            enriched_data = prepare_data_for_backtest(pair_config, copy.deepcopy(self.config["indicators"]))
                            if enriched_data is not None and not enriched_data.empty:
                                strategy = self._initialize_components(enriched_data, timeframe)
                                await self._run_and_save_results(strategy, pair_config)
