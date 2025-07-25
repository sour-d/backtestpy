import os
import pandas as pd
from env.trading_env import TradingEnvironment
from utils.data_loader import load_data
from strategies.sma_crossover_strategy import SMACrossoverStrategy
from portfolio.portfolio import Portfolio

# 1. Load historical data
data = load_data("data/raw/btcusdt_1h.csv")

# 2. Initialize Environment, Portfolio, and Strategy
env = TradingEnvironment(data)
portfolio = Portfolio(capital=100000, risk_pct=5, fee_pct=0.1)
strategy = SMACrossoverStrategy(
    env, portfolio, fast_period=50, slow_period=200, risk_pct=0.01
)

# 3. Run backtest
summary = strategy.run_backtest()

# 4. Print summary
portfolio.print_summary()

# 5. Save results
os.makedirs("data/result", exist_ok=True)
pd.DataFrame(summary["trades"]).to_csv(
    "data/result/refactored_backtest_output.csv", index=False
)

print("\nRefactored backtest complete. Results saved.")