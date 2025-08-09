import pandas as pd
import ccxt.pro as ccxtpro
import asyncio
from collections import deque
from datetime import datetime
import os
from dotenv import load_dotenv
import pytz # New import

from .data_manager_base import DataStorageBase
from utils.indicator_processor import IndicatorProcessor
from event_emitter import EventEmitter # New import

class LiveDataStorage(DataStorageBase, EventEmitter):
    def __init__(self, symbol: str, timeframe: str, initial_candles: list, indicator_configs: list, is_testnet: bool = True):
        DataStorageBase.__init__(self, pd.DataFrame()) # Initialize DataStorageBase part
        EventEmitter.__init__(self) # Initialize EventEmitter part
        
        load_dotenv() # Load .env file
        api_key = os.getenv("BYBIT_API_KEY")
        api_secret = os.getenv("BYBIT_API_SECRET")

        if not api_key or not api_secret:
            raise ValueError("BYBIT_API_KEY and BYBIT_API_SECRET must be set in a .env file for LiveDataStorage.")

        self.symbol = symbol
        self.timeframe = timeframe
        self.is_testnet = is_testnet
        self.indicator_configs = indicator_configs # Store indicator configs

        self.exchange = ccxtpro.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'swap'},
            'enableRateLimit': True,
        })

        if self.is_testnet:
            self.exchange.set_sandbox_mode(True)

        # Initialize all_candles with provided initial_candles
        self.all_candles = deque(maxlen=500) # Keep a rolling window of 500 candles
        for candle in initial_candles:
            self.all_candles.append(candle)
        
        self._current_step = len(self.all_candles) # Set initial step based on provided data

        # Create initial DataFrame for IndicatorProcessor
        initial_df_list = []
        for candle_data in self.all_candles:
            # Ensure candle_data is a list/tuple with 7 elements (OHLCV + timestamp + datetime)
            if len(candle_data) == 7:
                initial_df_list.append(candle_data)
            else: # Handle cases where datetime might not be present yet (e.g., from fetch_ohlcv)
                temp_candle_df = pd.DataFrame([candle_data], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                temp_candle_df['datetime'] = pd.to_datetime(temp_candle_df['timestamp'], unit='ms')
                initial_df_list.append(temp_candle_df.iloc[0].values.tolist())

        initial_df = pd.DataFrame(initial_df_list, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'datetime'])
        initial_df['datetime'] = pd.to_datetime(initial_df['datetime']) # Ensure datetime objects

        # Convert to IST for initial data
        ist_timezone = pytz.timezone('Asia/Kolkata')
        initial_df['datetime_ist'] = initial_df['datetime'].dt.tz_localize(pytz.utc).dt.tz_convert(ist_timezone)

        self.indicator_processor = IndicatorProcessor(self.indicator_configs)
        self.data_df = self.indicator_processor.process(initial_df) # Process initial data

        print(f"LiveDataStorage initialized for {symbol} ({timeframe}).")

    async def connect(self):
        await self.exchange.load_markets()
        print(f"Connected to Bybit for {self.symbol} ({self.timeframe}).")

    async def get_next_processed_data(self):
        """
        Fetches the next completed candle from the WebSocket, processes it,
        updates internal state, and returns the candle and historical data.
        Does NOT loop or emit events directly.
        """
        try:
            ohlcv_cache = await self.exchange.watch_ohlcv(self.symbol, self.timeframe)
            
            # Ensure we have at least 2 candles in the cache to identify a completed one.
            # The one before the last is the most recently completed candle.
            if len(ohlcv_cache) < 2:
                return None, None # No new completed candle yet

            completed_candle_raw = ohlcv_cache[-2]
            completed_candle_timestamp = completed_candle_raw[0]

            # Check if this candle has already been processed
            # This check is crucial when initial_candles are provided
            if self.all_candles and completed_candle_timestamp <= self.all_candles[-1][0]:
                return None, None # Already processed this candle or it's older

            # Convert raw candle to pandas Series with datetime and IST
            candle_df_single = pd.DataFrame([completed_candle_raw], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            candle_df_single['datetime'] = pd.to_datetime(candle_df_single['timestamp'], unit='ms')
            
            ist_timezone = pytz.timezone('Asia/Kolkata')
            candle_df_single['datetime_ist'] = candle_df_single['datetime'].dt.tz_localize(pytz.utc).dt.tz_convert(ist_timezone)
            
            completed_candle = candle_df_single.iloc[0] # Get as Series

            self.all_candles.append(completed_candle.values.tolist()) # Store as list for deque consistency
            
            # Create a DataFrame from the current deque content and process indicators
            current_deque_list = []
            for candle_data in self.all_candles:
                current_deque_list.append(candle_data)

            temp_df = pd.DataFrame(current_deque_list, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'datetime', 'datetime_ist'])
            temp_df['datetime'] = pd.to_datetime(temp_df['datetime']) # Ensure datetime objects
            temp_df['datetime_ist'] = pd.to_datetime(temp_df['datetime_ist']) # Ensure datetime objects

            self.data_df = self.indicator_processor.process(temp_df) # Process the current window
            self._current_step += 1

            return self.current_candle(), self.data_df

        except asyncio.CancelledError:
            print("WebSocket watch cancelled.")
            return None, None
        except Exception as e:
            print(f"Error in LiveDataStorage.get_next_processed_data(): {e}")
            raise e
            return None, None

    async def start_live_data(self):
        """
        Starts the continuous live data fetching loop.
        Emits 'new_candle' event for each new processed candle.
        """
        await self.connect()
        try:
            while True:
                current_candle, historical_data = await self.get_next_processed_data()
                if current_candle is not None: # Only emit if a new completed candle was processed
                    self.emit("new_candle", current_candle=current_candle, historical_data=historical_data)
                await asyncio.sleep(0.1) # Small delay to prevent busy-waiting
        except asyncio.CancelledError:
            print("Live data stream cancelled.")
        except Exception as e:
            print(f"Error in start_live_data: {e}")
            raise e  # Re-raise the exception to be handled by the caller
        finally:
            await self.close()

    def current_candle(self) -> pd.Series:
        if not self.data_df.empty:
            return self.data_df.iloc[-1]
        return None

    def previous_candle_of(self, day_count: int) -> pd.Series:
        if len(self.data_df) >= (day_count + 1):
            return self.data_df.iloc[-(day_count + 1)]
        return None

    @property
    def has_more_data(self) -> bool:
        return True

    @property
    def current_date(self):
        if not self.data_df.empty:
            return self.data_df.iloc[-1]['datetime']
        return None

    @property
    def current_step(self) -> int:
        return self._current_step

    async def close(self):
        await self.exchange.close()
        self.emit("disconnected", symbol=self.symbol, timeframe=self.timeframe)
