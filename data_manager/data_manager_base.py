from abc import ABC, abstractmethod
import pandas as pd

class DataStorageBase(ABC):
    """
    Abstract base class for all data storage implementations.
    Defines the interface for strategies to retrieve market data.
    """
    def __init__(self, data_df: pd.DataFrame):
        self.data_df = data_df

    @abstractmethod
    async def get_next_processed_data(self):
        """
        Advances to the next data point and returns the current candle
        and the historical data needed by the strategy.
        Returns (current_candle: pd.Series, historical_data: pd.DataFrame) or (None, None)
        if no more data.
        """
        pass

    @abstractmethod
    def current_candle(self) -> pd.Series:
        """
        Returns the current day's data (the latest candle).
        """
        pass

    @abstractmethod
    def previous_candle_of(self, day_count: int) -> pd.Series:
        """
        Returns the data for a candle N days (or periods) before the current one.
        day_count=1 for yesterday, day_count=2 for day before yesterday, etc.
        """
        pass

    @property
    @abstractmethod
    def has_more_data(self) -> bool:
        """
        Returns True if there is more data to process, False otherwise.
        """
        pass

    @property
    @abstractmethod
    def current_date(self):
        """
        Returns the datetime of the current data point.
        """
        pass

    @property
    @abstractmethod
    def current_step(self) -> int:
        """
        Returns the current step/index in the data stream.
        """
        pass

    async def connect(self):
        """
        Establishes connection to the data source (e.g., WebSocket).
        Implemented by subclasses if needed.
        """
        pass

    async def close(self):
        """
        Closes connection to the data source.
        Implemented by subclasses if needed.
        """
        pass