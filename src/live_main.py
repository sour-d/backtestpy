import yaml
import asyncio
from module.engine.live_engine import LiveTradingEngine
from utils.logger import app_logger

from utils.helpers import load_config

async def main():
    """Main function to run the live trading engine."""
    app_logger.info("Starting live trading application...")
    
    # Load configuration
    config = load_config('live')
    if not config:
        return

    try:
        # Initialize and run the live trading engine
        from module.exchange.exchange import Exchange
        exchange = await Exchange.create()
        live_engine = await LiveTradingEngine.create(config=config, exchange=exchange)
        await live_engine.run()
    except ValueError as e:
        app_logger.error(f"Execution failed: {e}")
    except Exception as e:
        app_logger.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
