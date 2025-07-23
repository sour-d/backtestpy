import pandas as pd

def load_data(filepath):
    df = pd.read_csv(filepath)

    # If datetime already exists, parse it again just to be sure
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
    else:
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

    # Optional: set datetime as index
    df.set_index('datetime', inplace=True)

    return df
