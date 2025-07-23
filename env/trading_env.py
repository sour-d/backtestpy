import pandas as pd

class TradingEnvironment:
    def __init__(self, data, capital=100000, risk_pct=5):
        self.data = data.reset_index(drop=True)
        self.capital = capital
        self.initial_capital = capital
        self.risk_pct = risk_pct
        self.risk = capital * (risk_pct / 100)
        self.current_step = 20
        self.current_trade = None
        self.trades = []

    def has_data(self):
        return self.current_step < len(self.data) - 1

    def now(self):
        return self.data.iloc[self.current_step]

    def prev(self, n=1):
        return self.data.iloc[self.current_step - n]

    def move(self):
        if self.has_data():
            self.current_step += 1
            return True
        return False

    def simple_moving_average(self, days, key="close"):
        return self.data.iloc[self.current_step - days:self.current_step][key].mean()

    def high_of_last(self, days):
        return self.data.iloc[self.current_step - days:self.current_step]["high"].max()

    def low_of_last(self, days):
        return self.data.iloc[self.current_step - days:self.current_step]["low"].min()

    def stocks_can_be_bought(self, risk_per_stock, price):
        max_by_cap = self.capital / price
        max_by_risk = self.risk / risk_per_stock
        affordable = min(max_by_cap, max_by_risk)
        return max(0, round(affordable, 2))

    def take_position(self, risk, price, trade_type="buy"):
        qty = self.stocks_can_be_bought(risk, price)
        if qty == 0:
            return

        self.capital -= qty * price
        self.current_trade = {
            "entry_price": price,
            "quantity": qty,
            "type": trade_type,
            "stop_loss": price - risk if trade_type == "buy" else price + risk,
        }

        self.trades.append({
            "step": self.current_step,
            "timestamp": self.data.index[self.current_step],
            "price": price,
            "quantity": qty,
            "type": trade_type,
            "action": "entry",
        })

    def exit_position(self, price, action="exit"):
        if not self.current_trade:
            return

        qty = self.current_trade["quantity"]
        self.capital += qty * price

        self.trades.append({
            "step": self.current_step,
            "timestamp": self.data.index[self.current_step],
            "price": price,
            "quantity": qty,
            "type": self.current_trade["type"],
            "action": action,
        })

        self.current_trade = None

    def summary(self):
        return {
            "final_capital": self.capital,
            "initial_capital": self.initial_capital,
            "profit": self.capital - self.initial_capital,
            "total_trades": len(self.trades),
            "trades": self.trades,
        }
