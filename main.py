import sys
import yaml
import pandas as pd
import importlib
import re
from pathlib import Path
import copy
from calendar import month_name
import json

# Removed: from env.trading_env import TradingEnvironment
from data_storage.historical_data_storage import HistoricalDataStorage # New import
from portfolio.portfolio import Portfolio
from utils.data_manager import prepare_data_for_backtest


def to_snake_case(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def initialize_components(config, enriched_data, timeframe):
    strategy_config = config["strategy"]
    # Get the timeframe specifically for the strategy from config
    
    # Extract the DataFrame for the strategy's primary timeframe
    if timeframe not in enriched_data:
        raise ValueError(f"Data for strategy timeframe {timeframe} not found in enriched_data.")
    
    data_for_strategy = enriched_data[timeframe]

    # Use HistoricalDataStorage instead of TradingEnvironment
    data_storage = HistoricalDataStorage(data_for_strategy)

    portfolio = Portfolio(
        capital=config["portfolio"]["initial_capital"],
        fee_pct=config["portfolio"]["fee_pct"],
        risk_pct=config["portfolio"]["risk_pct"],
    )

    strategy_class_name = strategy_config["class_name"]
    strategy_params = strategy_config["parameters"]
    strategy_module_name = to_snake_case(strategy_class_name)

    strategy_module = importlib.import_module(f"strategies.{strategy_module_name}")
    StrategyClass = getattr(strategy_module, strategy_class_name)
    
    # Pass data_storage to the strategy
    return StrategyClass(data_storage, portfolio, **strategy_params)


def run_and_save_results(strategy, symbol, timeframe, date_range, config):
    print(f"\n--- Running Backtest: {strategy.__class__.__name__} on {symbol} ({timeframe}) ---")
    summary = strategy.run_backtest()

    if date_range["months"]:
        filename_base = f"{symbol.replace('/', '-')}_{timeframe}_{date_range['months'][0].lower()}_{date_range['year']}"
    else:
        filename_base = f"{symbol.replace('/', '-')}_{timeframe}_{date_range['year']}"

    result_filepath = Path("data/result") / f"{filename_base}.csv"
    summary_filepath = Path("data/summary") / f"{filename_base}.json"
    result_filepath.parent.mkdir(parents=True, exist_ok=True)
    summary_filepath.parent.mkdir(parents=True, exist_ok=True)
    
    pd.DataFrame(summary["trades"]).to_csv(result_filepath, index=False)
    with open(summary_filepath, 'w') as f:
        json.dump(summary, f, indent=4, default=str)
    
    print(f"\n--- Results for {symbol} ({timeframe}) ---")
    strategy.portfolio.print_summary()
    print(f"Results saved to {result_filepath}")
    print(f"Summary saved to {summary_filepath}")
    print("--------------------------------------")


def main():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    backtest_settings = config["backtest_settings"]
    symbols = backtest_settings["symbols"]
    timeframes = backtest_settings["timeframes"] # Keep iterating over backtest_settings timeframes
    periods = backtest_settings["periods"]


    for symbol in symbols:
        for timeframe in timeframes: # Loop over backtest_settings timeframes
            for year, months in periods.items():
                if not months:
                    date_range = {"year": year, "months": [], "start": f"{year}-01-01", "end": f"{year}-12-31"}
                    # Ensure both backtest_settings timeframe and strategy timeframe are processed
                    pair_config = {"symbol": symbol, "timeframes": [timeframe], "start": date_range["start"], "end": date_range["end"]}
                    print(f"DEBUG: Calling prepare_data_for_backtest with timeframes: {pair_config["timeframes"]}")
                    enriched_data = prepare_data_for_backtest(pair_config, copy.deepcopy(config["indicators"]), force_reprocess=False)
                    if enriched_data:
                        strategy = initialize_components(config, enriched_data, timeframe) # Pass enriched_data dict
                        run_and_save_results(strategy, symbol, timeframe, date_range, config) # Use backtest_settings timeframe for naming
                else:
                    for month in months:
                        month_num = list(month_name).index(month.capitalize())
                        start_date = f"{year}-{month_num:02d}-01"
                        end_date = pd.to_datetime(start_date).to_period('M').end_time.strftime('%Y-%m-%d')
                        date_range = {"year": year, "months": [month], "start": start_date, "end": end_date}
                        # Ensure both backtest_settings timeframe and strategy timeframe are processed
                        pair_config = {"symbol": symbol, "timeframes": [timeframe], "start": date_range["start"], "end": date_range["end"]}
                        print(f"DEBUG: Calling prepare_data_for_backtest with timeframes: {pair_config["timeframes"]}")
                        enriched_data = prepare_data_for_backtest(pair_config, copy.deepcopy(config["indicators"]), force_reprocess=False)
                        if enriched_data:
                            strategy = initialize_components(config, enriched_data, timeframe) # Pass enriched_data dict
                            run_and_save_results(strategy, symbol, timeframe, date_range, config)

if __name__ == "__main__":
    main()
