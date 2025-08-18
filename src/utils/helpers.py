import re
import importlib

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
