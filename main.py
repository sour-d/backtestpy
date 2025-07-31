import sys
import yaml
import pandas as pd
import importlib
import re
from pathlib import Path
import copy

from env.trading_env import TradingEnvironment
from portfolio.portfolio import Portfolio
from utils.data_manager import prepare_data_for_backtest


def to_snake_case(name):
    """Converts a CamelCase name to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def initialize_components(config, pair_config, enriched_data):
    """Initializes the environment, portfolio, and strategy."""
    strategy_config = config["strategy"]
    # Use the strategy's configured timeframe as primary, fallback to first timeframe
    primary_timeframe = strategy_config.get("timeframe", pair_config["timeframes"][0])
    print(f"\n📊 Using primary timeframe: {primary_timeframe}")
    
    env = TradingEnvironment(enriched_data, primary_timeframe)
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
    
    return StrategyClass(env, portfolio, **strategy_params)


def run_and_save_results(strategy, pair_config, config):
    """Runs the backtest and saves the results."""
    print(f"\n--- Running Backtest: {strategy.__class__.__name__} on {pair_config['symbol']} ---")
    summary = strategy.run_backtest()

    # Save results - use prefix and primary timeframe for filename
    primary_timeframe = config["strategy"].get("timeframe", pair_config["timeframes"][0])
    
    # Use prefix if available, otherwise fall back to symbol
    if "prefix" in pair_config and pair_config["prefix"]:
        filename_base = f"{pair_config['prefix']}_{primary_timeframe}.csv"
    else:
        filename_base = f"{pair_config['symbol'].replace('/', '').lower()}_{primary_timeframe}.csv"
    
    result_filepath = Path("data/result") / filename_base
    result_filepath.parent.mkdir(parents=True, exist_ok=True)
    
    pd.DataFrame(summary["trades"]).to_csv(result_filepath, index=False)
    
    print(f"\n--- Results for {pair_config['symbol']} ---")
    strategy.portfolio.print_summary()
    print(f"Results saved to {result_filepath}")
    print("--------------------------------------")


def run_backtest_for_pair(pair_config, config):
    """Runs the full backtest process for a single trading pair."""
    print(f"\n--- Preparing Data for {pair_config['symbol']} ---")
    print(f"📈 Available timeframes: {pair_config['timeframes']}")
    
    # Pass a deep copy of the indicators config to prevent in-place modification issues
    enriched_data = prepare_data_for_backtest(pair_config, copy.deepcopy(config["indicators"]), force_reprocess=False)
    
    if enriched_data is None or not enriched_data: # Check if dictionary is empty
        print(f"[ERROR] Could not prepare data for {pair_config['symbol']}. Skipping backtest.")
        return
        
    strategy = initialize_components(config, pair_config, enriched_data)
    run_and_save_results(strategy, pair_config, config)


def main():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    try:
        run_arg = sys.argv[1]
    except IndexError:
        print("[ERROR] Please specify an index (e.g., 'python main.py all' or 'python main.py 0').")
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