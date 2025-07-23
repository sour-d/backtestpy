def simple_strategy(env: object):
    current = env.now()

    # Example: Buy if price > 20 SMA
    sma = env.simple_moving_average(20)
    if not env.current_trade and current["close"] > sma:
        env.take_position(risk=10, price=current["close"], trade_type="buy")

    # Exit if price drops below 20 SMA
    elif env.current_trade and current["close"] < sma:
        env.exit_position(price=current["close"])
