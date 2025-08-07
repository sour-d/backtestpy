import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime

from .data_fetcher import download_data_for_pair
from .indicator_processor import IndicatorProcessor
from .data_loader import load_data
from .file_utils import get_pair_filename  # Updated import


def _check_file_date_range(filepath, required_start, required_end):
    """Checks if a CSV file's date range exactly matches the required dates."""
    if not filepath.exists():
        return False
    try:
        df = pd.read_csv(filepath)
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


def prepare_data_for_backtest(pair_config, indicator_configs, force_reprocess=False):
    """
    Ensures both raw and enriched data are ready for a backtest for all specified timeframes.
    Returns a dictionary of DataFrames, keyed by timeframe.
    """
    all_timeframe_data = {}
    timeframes = pair_config.get("timeframes", [pair_config.get("timeframe", "1h")]) # Get all timeframes or default to single

    for tf in timeframes:
        # Create a temporary pair_config for the current timeframe
        current_tf_pair_config = pair_config.copy()
        current_tf_pair_config["timeframe"] = tf

        filename_base = get_pair_filename(current_tf_pair_config)
        raw_filepath = Path("data/raw") / filename_base
        enriched_filepath = Path("data/processed") / filename_base

        # Ensure the processed data directory exists before any writes
        enriched_filepath.parent.mkdir(parents=True, exist_ok=True)

        req_start = datetime.strptime(pair_config["start"], "%Y-%m-%d").date()
        req_end = datetime.strptime(pair_config["end"], "%Y-%m-%d").date()

        if force_reprocess or not _check_file_date_range(enriched_filepath, req_start, req_end):
            if not _check_file_date_range(raw_filepath, req_start, req_end):
                print(f"⚠️  Raw data missing for {current_tf_pair_config['symbol']} ({tf})")
                download_data_for_pair(current_tf_pair_config)
            
            print(f"🔄 Processing indicators for {current_tf_pair_config['symbol']} ({tf})...")
            raw_data = load_data(raw_filepath)
            if raw_data.empty:
                print(f"❌ Raw data for {current_tf_pair_config['symbol']} ({tf}) is empty. Skipping.")
                continue # Skip this timeframe if data is empty
            
            # Use the refactored IndicatorProcessor
            indicator_processor = IndicatorProcessor(indicator_configs)
            enriched_data = indicator_processor.process(raw_data)
            indicator_processor.save_to_csv(enriched_data, enriched_filepath) # Pass data to save_to_csv
        
        final_data = load_data(enriched_filepath)
        all_timeframe_data[tf] = final_data
    
    if not all_timeframe_data: # If no data was loaded for any timeframe
        return None
    
    return all_timeframe_data


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

    for item in symbols_to_download:
        # Handle both single timeframe (legacy) and multiple timeframes
        timeframes = item.get("timeframes", [item.get("timeframe", "1h")])
        
        for tf in timeframes:
            # Create a config for this specific timeframe
            tf_config = item.copy()
            tf_config["timeframe"] = tf
            
            raw_filepath = Path("data/raw") / get_pair_filename(tf_config)
            req_start = datetime.strptime(item["start"], "%Y-%m-%d").date()
            req_end = datetime.strptime(item["end"], "%Y-%m-%d").date()

            if not force_download and _check_file_date_range(raw_filepath, req_start, req_end):
                print(f"⏭️  {item.get('prefix', item['symbol'])} ({tf}) - already exists")
                continue
            
            print(f"📥 {item.get('prefix', item['symbol'])} ({tf}) {item['start']} → {item['end']}", end=" ... ")
            download_data_for_pair(tf_config)
            print("✅")