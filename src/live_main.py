import yaml
import asyncio
from module.engine.live_engine import LiveTradingEngine
from utils.logger import app_logger

def load_config(config_path):
    """Load configuration from a YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        app_logger.error(f"Configuration file not found at: {config_path}")
        return None
    except Exception as e:
        app_logger.error(f"Error loading configuration: {e}")
        return None

async def main():
    """Main function to run the live trading engine."""
    app_logger.info("Starting live trading application...")
    
    # Load configuration
    config = load_config('config/live_config.yaml')
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
