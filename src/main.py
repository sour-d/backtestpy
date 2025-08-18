import yaml
import asyncio
from module.engine.backtest_engine import BacktestEngine

async def main():
    with open("config/backtest_config.yaml", "r") as f:
        config = yaml.safe_load(f)

    engine = BacktestEngine(config)
    await engine.run()

if __name__ == "__main__":
    asyncio.run(main())