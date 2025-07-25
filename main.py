import os
import re
import sys
import yaml
import pandas as pd
import importlib
from pathlib import Path

from env.trading_env import TradingEnvironment
from utils.data_loader import load_data
from utils.indicator_processor import IndicatorProcessor
from portfolio.portfolio import Portfolio


def to_snake_case(name):
    """Converts a CamelCase name to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def get_pair_filename(pair_config):
    """Generates a standard filename from a trading pair config."""
    symbol = pair_config["symbol"].replace("/", "").lower()
    timeframe = pair_config["timeframe"]
    return f"{symbol}_{timeframe}.csv"


def run_backtest_for_pair(pair_config, config):
    """Runs the full backtest process for a single trading pair."""
    
    # 1. Define dynamic file paths
    filename_base = get_pair_filename(pair_config)
    raw_filepath = Path("data/raw") / filename_base
    enriched_filepath = Path("data/processed") / filename_base
    result_filepath = Path("data/result") / filename_base

    print(f"\n--- Starting Backtest for {pair_config['symbol']} ---")
    
    if not raw_filepath.exists():
        print(f"[ERROR] Raw data file not found: {raw_filepath}")
        print("Please run 'make download' first.")
        return

    # 2. Load Raw Data
    raw_data = load_data(raw_filepath)

    # 3. Pre-process Data to Add Indicators
    indicator_processor = IndicatorProcessor(raw_data)
    enriched_data = indicator_processor.process(config["indicators"])
    enriched_filepath.parent.mkdir(parents=True, exist_ok=True)
    indicator_processor.save_to_csv(enriched_filepath)

    # 4. Initialize Environment and Portfolio
    env = TradingEnvironment(enriched_data)
    portfolio = Portfolio(
        capital=config["portfolio"]["initial_capital"],
        fee_pct=config["portfolio"]["fee_pct"],
    )

    # 5. Dynamically Load and Initialize Strategy
    strategy_config = config["strategy"]
    strategy_class_name = strategy_config["class_name"]
    strategy_params = strategy_config["parameters"]
    strategy_module_name = to_snake_case(strategy_class_name)
    
    strategy_module = importlib.import_module(f"strategies.{strategy_module_name}")
    StrategyClass = getattr(strategy_module, strategy_class_name)
    strategy = StrategyClass(env, portfolio, **strategy_params)

    # 6. Run Backtest
    summary = strategy.run_backtest()

    # 7. Print Summary and Save Results
    print(f"\n--- Results for {pair_config['symbol']} ---")
    portfolio.print_summary()
    result_filepath.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summary["trades"]).to_csv(result_filepath, index=False)
    print(f"Results saved to {result_filepath}")
    print("--------------------------------------")


def main():
    # 1. Load Configuration
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # 2. Determine which pairs to run
    try:
        run_arg = sys.argv[1]
    except IndexError:
        print("[ERROR] Please specify which index to run (e.g., 'python main.py all' or 'python main.py 0').")
        return

    trading_pairs = config["trading_pairs"]

    if run_arg.lower() == "all":
        for pair_config in trading_pairs:
            run_backtest_for_pair(pair_config, config)
    else:
        try:
            pair_index = int(run_arg)
            if 0 <= pair_index < len(trading_pairs):
                run_backtest_for_pair(trading_pairs[pair_index], config)
            else:
                print(f"[ERROR] Index {pair_index} is out of bounds.")
        except ValueError:
            print(f"[ERROR] Invalid argument '{run_arg}'. Please use 'all' or a valid number.")


if __name__ == "__main__":
    main()