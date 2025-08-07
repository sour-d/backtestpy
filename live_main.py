import asyncio
import yaml
import os
from dotenv import load_dotenv
import pandas as pd
import ccxt.pro as ccxtpro # Import ccxt.pro for fetching initial data

from data_storage.live_data_storage import LiveDataStorage

async def main():
    load_dotenv()
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    live_config = config["live_trading"]
    indicator_configs = config["indicators"]

    symbol = live_config['symbol']
    timeframe = live_config['timeframe']
    is_testnet = live_config.get('testnet', False)

    # Initialize a temporary exchange instance to fetch initial historical data
    temp_exchange = ccxtpro.bybit({
        'apiKey': os.getenv("BYBIT_API_KEY"),
        'secret': os.getenv("BYBIT_API_SECRET"),
        'options': {'defaultType': 'swap'},
    })
    if is_testnet:
        temp_exchange.set_sandbox_mode(True)

    print(f"Fetching initial historical data for {symbol} ({timeframe})...")
    # Fetch enough historical data for indicator calculation (e.g., 200 candles)
    initial_candles_raw = await temp_exchange.fetch_ohlcv(symbol, timeframe, limit=500)
    await temp_exchange.close() # Close the temporary exchange
    await asyncio.sleep(1) # Add a small delay to respect rate limits

    if not initial_candles_raw:
        print("Error: Could not fetch initial historical data. Exiting.")
        return

    # Convert raw initial candles to the format expected by LiveDataStorage (with datetime)
    initial_candles_df = pd.DataFrame(initial_candles_raw, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    initial_candles_df['datetime'] = pd.to_datetime(initial_candles_df['timestamp'], unit='ms')
    initial_candles = initial_candles_df.values.tolist()

    data_storage = LiveDataStorage(
        symbol=symbol,
        timeframe=timeframe,
        initial_candles=initial_candles,
        indicator_configs=indicator_configs,
        is_testnet=is_testnet
    )

    def on_new_candle_received(current_candle, historical_data):
        print("\n--- New Live Candle Received ---")
        print(current_candle.to_string())
        # You can also inspect historical_data here if needed
        # print("Historical Data Tail:")
        # print(historical_data.tail())
        print("total historical candles:", len(historical_data), "and all is", len(data_storage.all_candles))
        print("--------------------------------")

    data_storage.on("new_candle", on_new_candle_received)

    print(f"Starting live data stream for {symbol} ({timeframe})...")
    print("Press Ctrl+C to stop.")

    try:
        await data_storage.start_live_data()
    except asyncio.CancelledError:
        print("Live data stream stopped.")
    except KeyboardInterrupt:
        print("Live data stream interrupted by user.")
    finally:
        await data_storage.close()
        print("Exchange connection closed.")

if __name__ == "__main__":
    asyncio.run(main())