def get_pair_filename(pair_config):
    """Generates a standard filename from a trading pair config."""
    # Use prefix if available, otherwise fall back to symbol-based naming
    if "prefix" in pair_config and pair_config["prefix"]:
        prefix = pair_config["prefix"]
        timeframe = pair_config["timeframe"]
        return f"{prefix}_{timeframe}.csv"
    else:
        symbol = pair_config["symbol"].replace("/", "").lower()
        timeframe = pair_config["timeframe"]
        return f"{symbol}_{timeframe}.csv"
