import os
import ccxt
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
from data_store_manager.data_store_manager_base import BACKTEST_DATA_TYPE, RAW_DATA_TYPE
from data_store_manager.file_store_manager import FileStoreManager
from utils.file_utils import get_pair_filename

SAVE_PATH = "./data/raw"

Path(SAVE_PATH).mkdir(parents=True, exist_ok=True)


def parse_date(date_str):
    return int(datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").timestamp() * 1000)


def _fetch_ohlcv(exchange, symbol, timeframe, since_ms, until_ms, pair_config):
    """Internal function to fetch data from the exchange."""
    all_data = []
    limit = 1000  # Standard limit for most exchanges
    earliest_timestamp = None

    while since_ms < until_ms:
        try:
            data = exchange.fetch_ohlcv(
                symbol, timeframe=timeframe, since=since_ms, limit=limit
            )

            if not data:
                break

            # Ensure data is sorted by timestamp (ascending)
            data = sorted(data, key=lambda x: x[0])

            first_timestamp_chunk = data[0][0]
            last_timestamp_chunk = data[-1][0]

            # If this is the first chunk, record the earliest timestamp actually fetched
            if earliest_timestamp is None:
                earliest_timestamp = first_timestamp_chunk

            # Filter out data that is already collected or beyond until_ms
            # Use a set for efficient lookup of existing timestamps if all_data gets large
            existing_timestamps = {d[0] for d in all_data}
            new_data = [d for d in data if d[0] >= since_ms and d[0] <= until_ms and d[0] not in existing_timestamps]

            if not new_data:
                if last_timestamp_chunk >= since_ms: # If the chunk actually contained data beyond current since_ms
                    since_ms = last_timestamp_chunk + 1
                else:
                    # Fallback: if no new data and last_timestamp_chunk is not advancing since_ms,
                    # heuristically advance since_ms to avoid infinite loop. This might skip some data.
                    timeframe_duration_ms = exchange.parse_timeframe(timeframe) * 1000
                    since_ms += limit * timeframe_duration_ms # Advance by expected duration of a full limit chunk
                continue

            all_data.extend(new_data)

            # Advance since_ms to the timestamp of the last fetched candle + 1 millisecond
            since_ms = last_timestamp_chunk + 1

            # Avoid hitting rate limits
            time.sleep(exchange.rateLimit / 1000)

        except ccxt.RateLimitExceeded as e:
            print(f"[ERROR] Rate limit exceeded for {symbol}. Waiting 10 seconds. Error: {e}")
            time.sleep(10)
        except Exception as e:
            print(f"[ERROR] Failed for {symbol} @ {datetime.fromtimestamp(since_ms / 1000)}: {e}")
            time.sleep(5)

    # After fetching, filter all_data to ensure it's within the exact requested range
    # and handle potential duplicates from multiple fetches
    final_data = [d for d in all_data if d[0] >= parse_date(f"{pair_config["start"]} 00:00:00") and d[0] <= parse_date(f"{pair_config["end"]} 23:59:59")]
    final_data = sorted(final_data, key=lambda x: x[0])
    
    # Remove duplicates based on timestamp
    seen_timestamps = set()
    deduplicated_data = []
    for d in final_data:
        if d[0] not in seen_timestamps:
            deduplicated_data.append(d)
            seen_timestamps.add(d[0])

    return deduplicated_data


def _save_to_csv(pair_config, data):
    data_store_manager = FileStoreManager(pair_config, BACKTEST_DATA_TYPE)
    """Internal function to save DataFrame to CSV."""
    df = pd.DataFrame(
        data, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
    data_store_manager.save_dataframe(df, RAW_DATA_TYPE)


def download_data_for_pair(pair_config):
    """
    Fetches and saves data for a single trading pair configuration.
    """
    exchange = ccxt.bybit({"enableRateLimit": True, "options": {"defaultType": "swap"}})
    symbol = pair_config["symbol"]
    timeframe = pair_config["timeframe"]
    since_ms = parse_date(f"{pair_config["start"]} 00:00:00")
    until_ms = parse_date(f"{pair_config["end"]} 23:59:59")

    data = _fetch_ohlcv(exchange, symbol, timeframe, since_ms, until_ms, pair_config)
    if data:
        _save_to_csv(pair_config, data)
    else:
        raise Exception(f"No data returned for {symbol} {timeframe}")