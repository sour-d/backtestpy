from .moving_average import MAHighIndicator, MALowIndicator
from .supertrend import SuperTrendIndicator
from .ema import EMAIndicator

INDICATOR_MAP = {
    "ma_high": MAHighIndicator,
    "ma_low": MALowIndicator,
    "supertrend": SuperTrendIndicator,
    "ema": EMAIndicator,
}

def create_indicator(name: str, **params):
    """
    Factory function to create an indicator instance.
    """
    indicator_class = INDICATOR_MAP.get(name.lower())
    if not indicator_class:
        # In the future, you could add a check here for library indicators
        raise ValueError(f"Indicator '{name}' not recognized.")
    
    return indicator_class(**params)
