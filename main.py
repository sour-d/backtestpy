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
    fast_sma = env.simple_moving_average(50)
    slow_sma = env.simple_moving_average(200)

    # Skip if we don't have enough data for moving averages
    if fast_sma is None or slow_sma is None:
        env.move()
        continue

    if not env.current_trade:
        if fast_sma > slow_sma:
            # Use a fixed risk amount instead of percentage of price
            risk_amount = now["close"] * 0.01  # 2% of current price as risk per share
            env.take_position(risk=risk_amount, price=now["close"])
    else:
        if now["low"] < env.current_trade["stop_loss"]:
            env.exit_position(price=env.current_trade["stop_loss"], action="stop_loss")
        elif fast_sma < slow_sma:
            env.exit_position(price=now["close"], action="sma")

    env.move()

# Close any open position at the end
if env.current_trade:
    final_price = env.now()["close"]
    print(f"Closing open position at end of backtest at price: {final_price}")
    env.exit_position(price=final_price, action="end_of_data")

# Print summary
summary = env.summary()
print(f"Final Capital: {summary['final_capital']:.2f}")
print(f"Profit: {summary['profit']:.2f}")
print(f"Total Trades: {summary['total_trades']}")
print(f"Total Fees Paid: {summary['total_fees_paid']:.2f}")
print(f"Net Profit After Fees: {summary['net_profit_after_fees']:.2f}")

# Save results
os.makedirs("data/result", exist_ok=True)
pd.DataFrame(summary["trades"]).to_csv("data/result/backtest_output.csv", index=False)
