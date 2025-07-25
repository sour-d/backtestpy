import os
import ccxt
import pandas as pd
import time
import yaml
from datetime import datetime
from pathlib import Path

CONFIG_PATH = "./config.yaml"
SAVE_PATH = "./data/raw"

Path(SAVE_PATH).mkdir(parents=True, exist_ok=True)


def parse_date(date_str):
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)


def fetch_ohlcv(exchange, symbol, timeframe, since_ms, until_ms):
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
            time.sleep(exchange.rateLimit / 1000)  # respect rate limit
        except Exception as e:
            print(f"[ERROR] Failed for {symbol} @ {since_ms}: {e}")
            time.sleep(5)
    return all_data


def save_to_csv(symbol, timeframe, data):
    df = pd.DataFrame(
        data, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
    symbol_clean = symbol.replace("/", "").lower()
    filename = f"{symbol_clean}_{timeframe}.csv"
    df.to_csv(os.path.join(SAVE_PATH, filename), index=False)
    print(f"[SAVED] {filename}")


def main():
    exchange = ccxt.bybit({"enableRateLimit": True, "options": {"defaultType": "spot"}})

    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    # Use the new 'trading_pairs' key
    symbols_to_download = config.get("trading_pairs", [])

    if not symbols_to_download:
        print("[WARNING] No symbols found in config.yaml under 'trading_pairs'.")
        return

    for item in symbols_to_download:
        symbol = item["symbol"]
        timeframe = item["timeframe"]
        since_ms = parse_date(item["start"])
        until_ms = parse_date(item["end"])
        print(f"[FETCHING] {symbol} {timeframe} from {item['start']} to {item['end']}")
        data = fetch_ohlcv(exchange, symbol, timeframe, since_ms, until_ms)
        if data:
            save_to_csv(symbol, timeframe, data)
        else:
            print(f"[INFO] No data returned for {symbol}.")


if __name__ == "__main__":
    main()
