import os
import pandas as pd
from env.trading_env import TradingEnvironment
from utils.data_loader import load_data

# Load historical data
data = load_data("data/raw/btcusdt_1h.csv")

# Initialize environment
env = TradingEnvironment(data)

# Simple strategy: SMA Crossover (fast=5, slow=10)
while env.has_data():
    now = env.now()
    fast_sma = env.simple_moving_average(5)
    slow_sma = env.simple_moving_average(10)

    # Skip if we don't have enough data for moving averages
    if fast_sma is None or slow_sma is None:
        env.move()
        continue

    if not env.current_trade:
        if fast_sma > slow_sma:
            # Use a fixed risk amount instead of percentage of price
            risk_amount = now["close"] * 0.02  # 2% of current price as risk per share
            env.take_position(risk=risk_amount, price=now["close"])
    else:
        if now["close"] < env.current_trade["stop_loss"]:
            env.exit_position(price=now["close"], action="stop_loss")
        elif fast_sma < slow_sma:
            env.exit_position(price=now["close"], action="sma")

    env.move()

# Print summary
summary = env.summary()
print(f"Final Capital: {summary['final_capital']}")
print(f"Profit: {summary['profit']}")
print(f"Total Trades: {summary['total_trades']}")

# Save results
os.makedirs("data/result", exist_ok=True)
pd.DataFrame(summary["trades"]).to_csv("data/result/backtest_output.csv", index=False)
