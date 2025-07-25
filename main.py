import os
import pandas as pd
from env.trading_env import TradingEnvironment
from utils.data_loader import load_data
from strategies import SMACrossoverStrategy

# Load historical data
data = load_data("data/raw/btcusdt_1h.csv")

# Initialize environment
env = TradingEnvironment(data)

# Initialize strategy (SMA Crossover: fast=50, slow=200)
strategy = SMACrossoverStrategy(env, fast_period=50, slow_period=200, risk_pct=0.01)

# Run backtest
summary = strategy.run_backtest()

# Print summary
strategy.print_summary(summary)

# Save results
os.makedirs("data/result", exist_ok=True)
pd.DataFrame(summary["trades"]).to_csv("data/result/backtest_output.csv", index=False)
