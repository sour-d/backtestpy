import pandas as pd

def simple_moving_average(data, days, key="close"):
    if len(data) < days:
        return None
    return data.iloc[-days:][key].mean()

def ma_high(data, period):
    return data['high'].rolling(window=period).mean()

def ma_low(data, period):
    return data['low'].rolling(window=period).mean()

def calculate_supertrend(df, period=10, multiplier=3):
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
            # Initial direction based on close price relative to bands
            if df['close'].iloc[i] > final_upper_band.iloc[i]:
                direction.iloc[i] = 1 # Buy
                supertrend.iloc[i] = final_lower_band.iloc[i]
            elif df['close'].iloc[i] < final_lower_band.iloc[i]:
                direction.iloc[i] = -1 # Sell
                supertrend.iloc[i] = final_upper_band.iloc[i]
            else:
                # If within bands, default to Buy (or Sell) to avoid Neutral
                # For the very first point, if it's within bands, we can't determine trend from previous
                # A common approach is to default to an uptrend or simply mark as NA until a clear signal
                # Given the strategy, we need a clear Buy/Sell. Let's default to Buy if no clear signal.
                direction.iloc[i] = 1 # Default to Buy
                supertrend.iloc[i] = final_lower_band.iloc[i]
        else:
            # Dynamic adjustment of bands
            if df['close'].iloc[i-1] <= final_lower_band.iloc[i-1]:
                final_lower_band.iloc[i] = basic_lower_band.iloc[i]
            else:
                final_lower_band.iloc[i] = max(basic_lower_band.iloc[i], final_lower_band.iloc[i-1])

            if df['close'].iloc[i-1] >= final_upper_band.iloc[i-1]:
                final_upper_band.iloc[i] = basic_upper_band.iloc[i]
            else:
                final_upper_band.iloc[i] = min(basic_upper_band.iloc[i], final_upper_band.iloc[i-1])

            # Determine current trend based on previous SuperTrend and current price
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
            else: # This case should ideally not be reached if previous supertrend was correctly set to a band
                # Fallback: if no clear previous band, determine based on current price vs bands
                if df['close'].iloc[i] > final_upper_band.iloc[i]:
                    direction.iloc[i] = 1
                elif df['close'].iloc[i] < final_lower_band.iloc[i]:
                    direction.iloc[i] = -1
                else:
                    # If still within bands, maintain previous direction (should be Buy/Sell from previous step)
                    direction.iloc[i] = direction.iloc[i-1]

            # Calculate SuperTrend value based on current direction
            if direction.iloc[i] == 1: # Uptrend
                supertrend.iloc[i] = final_lower_band.iloc[i]
            elif direction.iloc[i] == -1: # Downtrend
                supertrend.iloc[i] = final_upper_band.iloc[i]

    df['superTrend'] = supertrend
    df['superTrendDirection'] = direction.apply(lambda x: 'Buy' if x == 1 else ('Sell' if x == -1 else pd.NA)) # Use pd.NA for initial NaNs

    return df

def exponential_moving_average(data, period, column='close'):
    return data[column].ewm(span=period, adjust=False).mean()

def high_of_last(data, days):
    if len(data) < days:
        return None
    return data.iloc[-days:]["high"].max()


def low_of_last(data, days):
    if len(data) < days:
        return None
    return data.iloc[-days:]["low"].min()