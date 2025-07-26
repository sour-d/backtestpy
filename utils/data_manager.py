import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime

from .data_fetcher import download_data_for_pair
from .indicator_processor import IndicatorProcessor
from .data_loader import load_data
from .file_utils import get_pair_filename  # Updated import


def _check_file_date_range(filepath, required_start, required_end):
    """Checks if a CSV file's date range is sufficient."""
    if not filepath.exists():
        return False
    try:
        df = pd.read_csv(filepath)
        if df.empty:
            return False
        df["datetime"] = pd.to_datetime(df["datetime"])
        start_in_file = df["datetime"].iloc[0].date()
        end_in_file = df["datetime"].iloc[-1].date()
        return start_in_file <= required_start and end_in_file >= required_end
    except Exception:
        return False


def prepare_data_for_backtest(pair_config, indicator_configs, force_reprocess=False):
    """
    Ensures both raw and enriched data are ready for a backtest.
    """
    filename_base = get_pair_filename(pair_config)
    raw_filepath = Path("data/raw") / filename_base
    enriched_filepath = Path("data/processed") / filename_base

    # Ensure the processed data directory exists before any writes
    enriched_filepath.parent.mkdir(parents=True, exist_ok=True)

    req_start = datetime.strptime(pair_config["start"], "%Y-%m-%d").date()
    req_end = datetime.strptime(pair_config["end"], "%Y-%m-%d").date()

    if force_reprocess or not _check_file_date_range(enriched_filepath, req_start, req_end):
        if not _check_file_date_range(raw_filepath, req_start, req_end):
            print(f"[INFO] Raw data for {pair_config['symbol']} is missing or outdated.")
            download_data_for_pair(pair_config)
        
        print(f"[INFO] Processing indicators for {pair_config['symbol']}...")
        raw_data = load_data(raw_filepath)
        if raw_data.empty:
            print(f"[ERROR] Raw data for {pair_config['symbol']} is empty. Skipping indicator processing.")
            return None
        indicator_processor = IndicatorProcessor(raw_data)
        enriched_data = indicator_processor.process(indicator_configs)
        indicator_processor.save_to_csv(enriched_filepath)
    
    print(f"[INFO] Valid enriched data found for {pair_config['symbol']}.")
    final_data = load_data(enriched_filepath)
    return final_data


def run_download_process(force_download=False):
    """
    Orchestrates the download process for all symbols in the config file.
    """
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    symbols_to_download = config.get("trading_pairs", [])
    if not symbols_to_download:
        print("[WARNING] No symbols found in config.yaml under 'trading_pairs'.")
        return

    for item in symbols_to_download:
        raw_filepath = Path("data/raw") / get_pair_filename(item)
        req_start = datetime.strptime(item["start"], "%Y-%m-%d").date()
        req_end = datetime.strptime(item["end"], "%Y-%m-%d").date()

        if not force_download and _check_file_date_range(raw_filepath, req_start, req_end):
            print(f"[SKIPPED] Data for {item['symbol']} already exists and is up-to-date.")
            continue
        download_data_for_pair(item)