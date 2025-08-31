import yaml
import asyncio
from module.engine.backtest_engine import BacktestEngine

from utils.helpers import load_config

async def main():
    config = load_config('backtest')
    engine = BacktestEngine(config)
    await engine.run()

if __name__ == "__main__":
    asyncio.run(main())