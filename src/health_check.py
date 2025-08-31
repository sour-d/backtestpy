import asyncio
import yaml
from module.exchange.exchange import Exchange
from utils.logger import app_logger

from utils.helpers import load_config

async def main():
    """Main function to run the health check."""
    app_logger.info("Running health check...")
    
    config = load_config('live')
    if not config:
        return

    exchange = None
    try:
        exchange = await Exchange.create()
        symbol = config.get("live_trading", {}).get("symbol", "BTC/USDT")
        ticker = await exchange.client.fetch_ticker(symbol)
        app_logger.info(f"Successfully fetched ticker for {symbol}.")
        app_logger.info(f"Current price: {ticker['last']}")
    except Exception as e:
        app_logger.error(f"Health check failed: {e}", exc_info=True)
    finally:
        if exchange:
            await exchange.client.close()

if __name__ == "__main__":
    asyncio.run(main())
