import os
import pandas as pd
from env.trading_env import TradingEnvironment
from utils.data_loader import load_data
from strategies import LongShortSMAStrategy

# Load historical data
data = load_data("data/raw/btcusdt_1h.csv")

# Initialize environment
env = TradingEnvironment(data)

# Initialize Long/Short strategy (fast=20, slow=50)
strategy = LongShortSMAStrategy(env, fast_period=20, slow_period=50, risk_pct=0.02)

# Run backtest
summary = strategy.run_backtest()

# Print summary
strategy.print_summary(summary)

# Save results
os.makedirs("data/result", exist_ok=True)
pd.DataFrame(summary["trades"]).to_csv("data/result/long_short_backtest_output.csv", index=False)

print(f"\nStrategy can take both long and short positions:")
print(f"- Long positions when fast SMA > slow SMA")
print(f"- Short positions when fast SMA < slow SMA")
print(f"- Liquidates on stop loss or signal change")
