import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime

from data_store_manager.data_store_manager_base import BACKTEST_DATA_TYPE, PROCESSED_DATA_TYPE, RAW_DATA_TYPE

from .historical_data_fetcher import download_data_for_pair

from data_store_manager.file_store_manager import FileStoreManager # New import
from utils.indicator_processor import IndicatorProcessor # Keep IndicatorProcessor


def _check_file_date_range(data_store_manager: FileStoreManager, required_start, required_end):
    """Checks if a CSV file's date range exactly matches the required dates."""
    try:
        df = data_store_manager.load_dataframe(BACKTEST_DATA_TYPE)
        if df.empty:
            return False
        df["datetime"] = pd.to_datetime(df["datetime"])
        
        # Get the actual date range in the file
        start_in_file = df["datetime"].iloc[0].date()
        end_in_file = df["datetime"].iloc[-1].date()
        
        # Check if file dates exactly match the required dates
        start_matches = start_in_file == required_start
        end_matches = end_in_file == required_end
        
        return start_matches and end_matches
    except Exception:
        return False


def prepare_data_for_backtest(pair_config, indicator_configs):
    """
    Ensures both raw and enriched data are ready for a backtest for all specified timeframes.
    Returns a dictionary of DataFrames, keyed by timeframe.
    """
    
    data_store_manager = FileStoreManager(pair_config, BACKTEST_DATA_TYPE)
    symbol = pair_config["symbol"]
    timeframe = pair_config["timeframe"]
    start = pair_config["start"]
    end = pair_config["end"]

    # raw_filepath = data_store_manager.get_raw_filepath(symbol, timeframe, start_date_str, end_date_str)
    # enriched_filepath = data_store_manager.get_processed_filepath(symbol, timeframe)

    req_start = datetime.strptime(start, "%Y-%m-%d").date()
    req_end = datetime.strptime(end, "%Y-%m-%d").date()

    if not _check_file_date_range(data_store_manager, req_start, req_end):
        print(f"⚠️  Raw data missing for {symbol} ({timeframe})")
        # Pass the current_tf_pair_config to download_data_for_pair
        download_data_for_pair(pair_config)

    print(f"🔄 Processing indicators for {symbol} ({timeframe})...")
    raw_data = data_store_manager.load_dataframe(RAW_DATA_TYPE)
    if raw_data.empty:
        return print(f"❌ Raw data for {symbol} ({timeframe}) is empty. Skipping.")
    
    indicator_processor = IndicatorProcessor(indicator_configs)
    enriched_data = indicator_processor.process(raw_data)
    data_store_manager.save_dataframe(enriched_data, PROCESSED_DATA_TYPE)

    # final_data = data_store_manager.load_dataframe(enriched_filepath)
    # all_timeframe_data[timeframe] = final_data
    
    return enriched_data


def run_download_process(force_download=False):
    """
    Orchestrates the download process for all symbols in the config file.
    Downloads data for all timeframes specified in each trading pair.
    """
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    symbols_to_download = config.get("trading_pairs", [])
    if not symbols_to_download:
        print("[WARNING] No symbols found in config.yaml under 'trading_pairs'.")
        return

    data_store_manager = FileStoreManager() # Initialize FileStoreManager once

    for item in symbols_to_download:
        timeframes = item.get("timeframes", [item.get("timeframe", "1h")])
        
        for tf in timeframes:
            symbol = item["symbol"]
            start_date_str = item["start"]
            end_date_str = item["end"]

            raw_filepath = data_store_manager.get_raw_filepath(symbol, tf, start_date_str, end_date_str)

            if not force_download and raw_filepath.exists():
                print(f"⏭️  {item.get('prefix', item['symbol'])} ({tf}) - already exists")
                continue
            
            print(f"📥 {item.get('prefix', item['symbol'])} ({tf}) {item['start']} → {item['end']}", end=" ... ")
            download_data_for_pair({"symbol": symbol, "timeframe": tf, "start": start_date_str, "end": end_date_str})
            print("✅")