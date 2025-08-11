import pandas as pd
import ccxt.pro as ccxtpro
import asyncio
from collections import deque
from datetime import datetime
import os
from dotenv import load_dotenv
import pytz

from .data_manager_base import DataStorageBase
from utils.indicator_processor import IndicatorProcessor
from event_emitter import EventEmitter
from storage_manager.file_store_manager import FileStoreManager
from storage_manager.storage_manager_base import LIVE_DATA_TYPE, RAW_DATA_TYPE, PROCESSED_DATA_TYPE

class LiveDataStorage(DataStorageBase, EventEmitter):
    def __init__(self, symbol: str, timeframe: str, initial_candles: list, indicator_configs: list, is_testnet: bool = True, simulation_data: pd.DataFrame = None, logger=None):
        DataStorageBase.__init__(self, pd.DataFrame())
        EventEmitter.__init__(self)
        
        self.symbol = symbol
        self.timeframe = timeframe
        self.is_testnet = is_testnet
        self.indicator_configs = indicator_configs
        self.simulation_mode = simulation_data is not None
        self.simulation_data = simulation_data
        self.simulation_step = 0
        self.logger = logger

        if not self.simulation_mode:
            load_dotenv()
            api_key = os.getenv("BYBIT_API_KEY")
            api_secret = os.getenv("BYBIT_API_SECRET")

            if not api_key or not api_secret:
                if self.logger:
                    self.logger.error("BYBIT_API_KEY and BYBIT_API_SECRET must be set in a .env file for LiveDataStorage.")
                raise ValueError("BYBIT_API_KEY and BYBIT_API_SECRET must be set in a .env file for LiveDataStorage.")

            self.exchange = ccxtpro.bybit({
                'apiKey': api_key,
                'secret': api_secret,
                'options': {'defaultType': 'swap'},
                'enableRateLimit': True,
            })

            if self.is_testnet:
                self.exchange.set_sandbox_mode(True)
        else:
            self.exchange = None

        # Initialize FileStoreManager for live data
        symbol_info = {'symbol': symbol, 'timeframe': timeframe, 'start': datetime.now().strftime('%Y-%m-%d')}
        self.file_store_manager = FileStoreManager(symbol_info, data_type=LIVE_DATA_TYPE)

        self.all_candles = deque(maxlen=500)
        if not self.simulation_mode:
            for candle in initial_candles:
                self.all_candles.append(candle)
        
        self._current_step = len(self.all_candles)

        initial_df_list = []
        for candle_data in self.all_candles:
            if len(candle_data) == 7:
                initial_df_list.append(candle_data)
            else:
                temp_candle_df = pd.DataFrame([candle_data], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                temp_candle_df['datetime'] = pd.to_datetime(temp_candle_df['timestamp'], unit='ms')
                initial_df_list.append(temp_candle_df.iloc[0].values.tolist())

        initial_df = pd.DataFrame(initial_df_list, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'datetime'])
        initial_df['datetime'] = pd.to_datetime(initial_df['datetime'])

        ist_timezone = pytz.timezone('Asia/Kolkata')
        initial_df['datetime_ist'] = initial_df['datetime'].dt.tz_localize(pytz.utc).dt.tz_convert(ist_timezone)

        self.indicator_processor = IndicatorProcessor(self.indicator_configs)
        self.data_df = self.indicator_processor.process(initial_df)
        
        # Save initial raw candles to file
        self.file_store_manager.save_dataframe(initial_df, RAW_DATA_TYPE)
        # Save initial processed candles to file
        self.file_store_manager.save_dataframe(self.data_df, PROCESSED_DATA_TYPE)

        if self.logger:
            self.logger.info(f"LiveDataStorage initialized for {symbol} ({timeframe}). Initial data saved.")

    async def connect(self):
        if not self.simulation_mode:
            await self.exchange.load_markets()
            if self.logger:
                self.logger.info(f"Connected to Bybit for {self.symbol} ({self.timeframe}).")

    async def get_next_processed_data(self):
        """
        Fetches the next completed candle from the WebSocket or simulation data, 
        processes it, updates internal state, and returns the candle and historical data.
        Does NOT loop or emit events directly.
        """
        if self.simulation_mode:
            if self.simulation_step < len(self.simulation_data):
                completed_candle_raw = self.simulation_data.iloc[self.simulation_step].values.tolist()
                if self.logger:
                    self.logger.info(f"Simulating new candle: {completed_candle_raw}")
                self.simulation_step += 1
            else:
                return None, None # No more simulation data
        else:
            try:
                ohlcv_cache = await self.exchange.watch_ohlcv(self.symbol, self.timeframe)
                
                if len(ohlcv_cache) < 2:
                    return None, None # No new completed candle yet

                completed_candle_raw = ohlcv_cache[-2]
                completed_candle_timestamp = completed_candle_raw[0]

                if self.all_candles and completed_candle_timestamp <= self.all_candles[-1][0]:
                    return None, None
                
                if self.logger:
                    self.logger.info(f"New candle received: {completed_candle_raw}")

            except asyncio.CancelledError:
                if self.logger:
                    self.logger.warning("WebSocket watch cancelled.")
                return None, None
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in LiveDataStorage.get_next_processed_data(): {e}")
                raise e

        # Convert raw candle to pandas Series with datetime and IST
        candle_df_single = pd.DataFrame([completed_candle_raw], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'datetime'])
        candle_df_single['datetime'] = pd.to_datetime(candle_df_single['timestamp'], unit='ms')
        
        ist_timezone = pytz.timezone('Asia/Kolkata')
        candle_df_single['datetime_ist'] = candle_df_single['datetime'].dt.tz_localize(pytz.utc).dt.tz_convert(ist_timezone)
        
        completed_candle = candle_df_single.iloc[0] # Get as Series

        # Save the new candle to the raw data file
        try:
            existing_df = self.file_store_manager.load_dataframe(RAW_DATA_TYPE)
            if not existing_df.empty:
                # Append new candle and save
                updated_df = pd.concat([existing_df, candle_df_single], ignore_index=True)
                self.file_store_manager.save_dataframe(updated_df, RAW_DATA_TYPE)
            else:
                # If file was empty, save the new candle directly
                self.file_store_manager.save_dataframe(candle_df_single, RAW_DATA_TYPE)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving live raw data: {e}")

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

        # Save the processed data
        try:
            self.file_store_manager.save_dataframe(self.data_df, PROCESSED_DATA_TYPE)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving live processed data: {e}")

        return self.current_candle(), self.data_df

    async def start_live_data(self):
        """
        Starts the continuous live data fetching loop.
        Emits 'new_candle' event for each new processed candle.
        """
        if not self.simulation_mode:
            await self.connect()
        try:
            while True:
                current_candle, historical_data = await self.get_next_processed_data()
                if current_candle is not None: # Only emit if a new completed candle was processed
                    self.emit("new_candle", current_candle=current_candle, historical_data=historical_data)
                    if self.simulation_mode:
                        await asyncio.sleep(0.01) # a small delay to simulate live ticks
                    else:
                        await asyncio.sleep(0.1) # Small delay to prevent busy-waiting
                else:
                    if self.simulation_mode:
                        if self.logger:
                            self.logger.info("--- Live Simulation Finished ---")
                        break # End of simulation

        except asyncio.CancelledError:
            if self.logger:
                self.logger.warning("Live data stream cancelled.")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in start_live_data: {e}")
            raise e  # Re-raise the exception to be handled by the caller
        finally:
            await self.close() # Process the current window
        self._current_step += 1

        # Save the processed data
        try:
            self.file_store_manager.save_dataframe(self.data_df, PROCESSED_DATA_TYPE)
        except Exception as e:
            print(f"Error saving live processed data: {e}")

        return self.current_candle(), self.data_df

    async def start_live_data(self):
        """
        Starts the continuous live data fetching loop.
        Emits 'new_candle' event for each new processed candle.
        """
        if not self.simulation_mode:
            await self.connect()
        try:
            while True:
                current_candle, historical_data = await self.get_next_processed_data()
                if current_candle is not None: # Only emit if a new completed candle was processed
                    self.emit("new_candle", current_candle=current_candle, historical_data=historical_data)
                    if self.simulation_mode:
                        await asyncio.sleep(0.01) # a small delay to simulate live ticks
                    else:
                        await asyncio.sleep(0.1) # Small delay to prevent busy-waiting
                else:
                    if self.simulation_mode:
                        print("--- Live Simulation Finished ---")
                        break # End of simulation

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
        if not self.simulation_mode and self.exchange:
            await self.exchange.close()
            self.emit("disconnected", symbol=self.symbol, timeframe=self.timeframe)
