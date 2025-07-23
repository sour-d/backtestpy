import os
import pandas as pd
from env.trading_env import TradingEnvironment
from utils.data_loader import load_data

# Load historical data
data = load_data("data/raw/ethusdt_1h.csv")

# Initialize environment
env = TradingEnvironment(data)

# Simple strategy: SMA Crossover (fast=5, slow=10)
while env.has_data():
    now = env.now()
    fast_sma = env.simple_moving_average(5)
    slow_sma = env.simple_moving_average(10)

    if not env.current_trade:
        if fast_sma > slow_sma:
            env.take_position(risk=now["close"] * 0.02, price=now["close"])
    else:
        if now["close"] < env.current_trade["stop_loss"]:
            env.exit_position(price=now["close"], action="stop_loss")
        elif fast_sma < slow_sma:
            env.exit_position(price=now["close"], action="sma_exit")

    env.move()

# Print summary
summary = env.summary()
print(f"Final Capital: {summary['final_capital']}")
print(f"Profit: {summary['profit']}")
print(f"Total Trades: {summary['total_trades']}")

# Save results
os.makedirs("data/result", exist_ok=True)
pd.DataFrame(summary["trades"]).to_csv("data/result/backtest_output.csv", index=False)
