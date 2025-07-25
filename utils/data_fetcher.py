import os
import ccxt
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
from utils.file_utils import get_pair_filename

SAVE_PATH = "./data/raw"

Path(SAVE_PATH).mkdir(parents=True, exist_ok=True)


def parse_date(date_str):
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)


def _fetch_ohlcv(exchange, symbol, timeframe, since_ms, until_ms):
    """Internal function to fetch data from the exchange."""
    all_data = []
    limit = 1000
    while since_ms < until_ms:
        try:
            data = exchange.fetch_ohlcv(
                symbol, timeframe=timeframe, since=since_ms, limit=limit
            )
            if not data:
                break
            last_timestamp = data[-1][0]
            if last_timestamp == since_ms:
                break
            all_data.extend(data)
            since_ms = last_timestamp + 1
            time.sleep(exchange.rateLimit / 1000)
        except Exception as e:
            print(f"[ERROR] Failed for {symbol} @ {since_ms}: {e}")
            time.sleep(5)
    return all_data


def _save_to_csv(symbol, timeframe, data):
    """Internal function to save DataFrame to CSV."""
    df = pd.DataFrame(
        data, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
    filename = get_pair_filename({"symbol": symbol, "timeframe": timeframe})
    df.to_csv(os.path.join(SAVE_PATH, filename), index=False)
    print(f"[SAVED] {filename}")


def download_data_for_pair(pair_config):
    """
    Fetches and saves data for a single trading pair configuration.
    """
    exchange = ccxt.bybit({"enableRateLimit": True, "options": {"defaultType": "spot"}})
    symbol = pair_config["symbol"]
    timeframe = pair_config["timeframe"]
    since_ms = parse_date(pair_config["start"])
    until_ms = parse_date(pair_config["end"])

    print(f"[FETCHING] {symbol} {timeframe} from {pair_config['start']} to {pair_config['end']}")
    data = _fetch_ohlcv(exchange, symbol, timeframe, since_ms, until_ms)
    if data:
        _save_to_csv(symbol, timeframe, data)
    else:
        print(f"[INFO] No data returned for {symbol}.")