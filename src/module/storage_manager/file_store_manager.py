import pandas as pd
from pathlib import Path
import json

from .storage_manager_base import DataStoreManagerBase

class FileStoreManager(DataStoreManagerBase):
    """
    Implements DataStoreManagerBase for file-based storage.
    Stores data in CSV and JSON files within a specified base directory.
    """
    def __init__(self, symbol_info, data_type: str = "backtest"):
        super().__init__(symbol_info, data_type)
        self.raw_data_dir = self.base_path / "raw"
        self.processed_data_dir = self.base_path / "processed"
        self.result_dir = self.base_path / "result"
        self.summary_dir = self.base_path / "summary"

        # Ensure directories exist
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        self.result_dir.mkdir(parents=True, exist_ok=True)
        self.summary_dir.mkdir(parents=True, exist_ok=True)

    def get_raw_filepath(self, file_extension) -> Path:
        return self.raw_data_dir / f"{self.filename}.{file_extension}"

    def get_processed_filepath(self, file_extension) -> Path:
        return self.processed_data_dir / f"{self.filename}.{file_extension}"

    def get_result_filepath(self, file_extension) -> Path:
        return self.result_dir / f"{self.filename}.{file_extension}"

    def get_summary_filepath(self, file_extension) -> Path:
        return self.summary_dir / f"{self.filename}.{file_extension}"

    def _get_filepath(self, type: str) -> Path:
        """
        Helper method to get the file path based on type.
        """
        if type == "raw":
            return self.get_raw_filepath("csv")
        elif type == "processed":
            return self.get_processed_filepath("csv")
        elif type == "result":
            return self.get_result_filepath("csv")
        elif type == "summary":
            return self.get_summary_filepath("json")
        else:
            raise ValueError(f"Unknown data type: {type}")

    def save_dataframe(self, df: pd.DataFrame, type: str, append: bool = False):
        self._get_filepath(type).parent.mkdir(parents=True, exist_ok=True)
        if append and self._get_filepath(type).exists():
            df.to_csv(self._get_filepath(type), mode='a', header=False, index=False)
        else:
            df.to_csv(self._get_filepath(type), index=False)

    def load_dataframe(self, type: str) -> pd.DataFrame:
        if self._get_filepath(type).exists():
            return pd.read_csv(self._get_filepath(type))
        return pd.DataFrame() # Return empty DataFrame if file not found

    def save_json(self, data: dict, type: str):
        self._get_filepath(type).parent.mkdir(parents=True, exist_ok=True)
        with open(self._get_filepath(type), 'w') as f:
            json.dump(data, f, indent=4, default=str)

    def load_json(self, type: str) -> dict:
        if self._get_filepath(type).exists():
            with open(self._get_filepath(type), 'r') as f:
                return json.load(f)
        return {} # Return empty dict if file not found
