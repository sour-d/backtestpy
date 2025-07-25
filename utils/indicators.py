def simple_moving_average(data, days, key="close"):
    if len(data) < days:
        return None
    return data.iloc[-days:][key].mean()


def high_of_last(data, days):
    if len(data) < days:
        return None
    return data.iloc[-days:]["high"].max()


def low_of_last(data, days):
    if len(data) < days:
        return None
    return data.iloc[-days:]["low"].min()
