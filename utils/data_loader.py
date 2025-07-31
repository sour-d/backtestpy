import pandas as pd

def load_data(filepath):
    df = pd.read_csv(filepath)

    # If datetime already exists, parse it again just to be sure
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
    else:
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

    # Set datetime as index for time-based operations like asof
    df.set_index('datetime', inplace=True)
    df.sort_index(inplace=True)  # Ensure chronological order

    return df
