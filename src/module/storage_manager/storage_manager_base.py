from abc import ABC, abstractmethod
import pandas as pd
from pathlib import Path

# create enums for data types
RAW_DATA_TYPE = "raw"
PROCESSED_DATA_TYPE = "processed"
RESULT_DATA_TYPE = "result"
SUMMARY_DATA_TYPE = "summary"


BACKTEST_DATA_TYPE = "backtest"
LIVE_DATA_TYPE = "live"
PAPER_DATA_TYPE = "paper"
TEST_DATA_TYPE = "test"

BASE_PATH = "./data"

class DataStoreManagerBase(ABC):
    """
    Abstract base class for managing data storage and retrieval.
    Designed to be agnostic to the underlying storage mechanism (file, database, etc.).
    """
    def __init__(self, pair_config, data_type: str = BACKTEST_DATA_TYPE):
        self.base_path = Path(BASE_PATH) / data_type
        self.pair_config = pair_config
        symbol, timeframe = pair_config['symbol'], pair_config['timeframe']
        month = pair_config.get('month', 'all')
        year = pair_config['start'].split('-')[0]
        self.filename = f"{symbol.replace('/', '').lower()}_{timeframe}_{month}_{year}"

    @abstractmethod
    def get_raw_filepath(self, symbol: str, timeframe: str, start_date: str, end_date: str, prefix: str = None) -> Path:
        """
        Generates the file path for raw data.
        start_date and end_date are in YYYY-MM-DD format.
        """
        pass

    @abstractmethod
    def get_processed_filepath(self, symbol: str, timeframe: str, year: int, prefix: str = None) -> Path:
        """
        Generates the file path for processed data.
        """
        pass

    @abstractmethod
    def get_result_filepath(self, symbol: str, timeframe: str, year: int, month: str = None, prefix: str = None) -> Path:
        """
        Generates the file path for backtest results (trades).
        """
        pass

    @abstractmethod
    def get_summary_filepath(self, symbol: str, timeframe: str, year: int, month: str = None, prefix: str = None) -> Path:
        """
        Generates the file path for backtest summary.
        """
        pass

    @abstractmethod
    def save_dataframe(self, df: pd.DataFrame, filepath: Path):
        """
        Saves a pandas DataFrame to the specified location.
        """
        pass

    @abstractmethod
    def load_dataframe(self, filepath: Path) -> pd.DataFrame:
        """
        Loads a pandas DataFrame from the specified location.
        """
        pass

    @abstractmethod
    def save_json(self, data: dict, filepath: Path):
        """
        Saves a dictionary to the specified location as JSON.
        """
        pass

    @abstractmethod
    def load_json(self, filepath: Path) -> dict:
        """
        Loads data from the specified location as JSON.
        """
        pass
