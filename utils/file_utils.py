def get_pair_filename(pair_config):
    """Generates a standard filename from a trading pair config."""
    symbol = pair_config["symbol"].replace("/", "").lower()
    timeframe = pair_config["timeframe"]
    return f"{symbol}_{timeframe}.csv"
