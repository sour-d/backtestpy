import yaml
import re
import importlib

def load_config(mode):
    """Load and merge configuration files."""
    with open("config/common_config.yaml", 'r') as f:
        common_config = yaml.safe_load(f)

    if mode == 'live':
        config_path = 'config/live_config.yaml'
    elif mode == 'backtest':
        config_path = 'config/backtest_config.yaml'
    else:
        raise ValueError(f"Invalid mode: {mode}")

    with open(config_path, 'r') as f:
        mode_config = yaml.safe_load(f)

    # Merge configs, with mode-specific config overriding common config
    config = {**common_config, **mode_config}
    return config

def to_snake_case(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

def initialize_strategy(strategy_config, data_storage, portfolio, logger=None):
    strategy_class_name = strategy_config["class_name"]
    strategy_params = strategy_config["parameters"]
    strategy_module_name = to_snake_case(strategy_class_name)

    strategy_module = importlib.import_module(f"module.strategies.{strategy_module_name}")
    StrategyClass = getattr(strategy_module, strategy_class_name)
    
    return StrategyClass(
        data_storage=data_storage,
        portfolio=portfolio,
        logger=logger,
        **strategy_params
    )
