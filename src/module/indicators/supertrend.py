import pandas as pd
from .base import Indicator

class SuperTrendIndicator(Indicator):
    def apply(self, data_df: pd.DataFrame) -> pd.DataFrame:
        period = self.params.get("period", 10)
        multiplier = self.params.get("multiplier", 3)

        df = data_df.copy()
        
        # Calculate Average True Range (ATR)
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.ewm(span=period, adjust=False).mean()

        # Calculate Basic Upper and Lower Bands
        basic_upper_band = ((df['high'] + df['low']) / 2) + (multiplier * atr)
        basic_lower_band = ((df['high'] + df['low']) / 2) - (multiplier * atr)

        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int) # 1 for uptrend, -1 for downtrend

        # Initialize final bands and SuperTrend values
        final_upper_band = pd.Series(index=df.index, dtype=float)
        final_lower_band = pd.Series(index=df.index, dtype=float)

        # Iterate to calculate SuperTrend
        for i in range(len(df)):
            if pd.isna(basic_upper_band.iloc[i]) or pd.isna(basic_lower_band.iloc[i]):
                supertrend.iloc[i] = pd.NA
                direction.iloc[i] = pd.NA
                final_upper_band.iloc[i] = pd.NA
                final_lower_band.iloc[i] = pd.NA
                continue

            if i == 0:
                final_upper_band.iloc[i] = basic_upper_band.iloc[i]
                final_lower_band.iloc[i] = basic_lower_band.iloc[i]
                direction.iloc[i] = pd.NA
                supertrend.iloc[i] = pd.NA
            else:
                if df['close'].iloc[i-1] <= final_lower_band.iloc[i-1]:
                    final_lower_band.iloc[i] = basic_lower_band.iloc[i]
                else:
                    final_lower_band.iloc[i] = max(basic_lower_band.iloc[i], final_lower_band.iloc[i-1])

                if df['close'].iloc[i-1] >= final_upper_band.iloc[i-1]:
                    final_upper_band.iloc[i] = basic_upper_band.iloc[i]
                else:
                    final_upper_band.iloc[i] = min(basic_upper_band.iloc[i], final_upper_band.iloc[i-1])

                if supertrend.iloc[i-1] == final_upper_band.iloc[i-1]: # Previous was downtrend
                    if df['close'].iloc[i] > final_upper_band.iloc[i]:
                        direction.iloc[i] = 1 # Change to uptrend
                    else:
                        direction.iloc[i] = -1 # Remain downtrend
                elif supertrend.iloc[i-1] == final_lower_band.iloc[i-1]: # Previous was uptrend
                    if df['close'].iloc[i] < final_lower_band.iloc[i]:
                        direction.iloc[i] = -1 # Change to downtrend
                    else:
                        direction.iloc[i] = 1 # Remain uptrend
                else:
                    if df['close'].iloc[i] > final_upper_band.iloc[i]:
                        direction.iloc[i] = 1
                    elif df['close'].iloc[i] < final_lower_band.iloc[i]:
                        direction.iloc[i] = -1
                    else:
                        direction.iloc[i] = direction.iloc[i-1]

                if direction.iloc[i] == 1: # Uptrend
                    supertrend.iloc[i] = final_lower_band.iloc[i]
                elif direction.iloc[i] == -1: # Downtrend
                    supertrend.iloc[i] = final_upper_band.iloc[i]

        df['superTrend'] = supertrend
        df['superTrendDirection'] = direction.apply(lambda x: 'Buy' if x == 1 else ('Sell' if x == -1 else pd.NA))

        return df
