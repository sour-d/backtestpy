import pandas as pd


class Portfolio:
    def __init__(self, capital=100000, risk_pct=5, fee_pct=0.1):
        self.initial_capital = capital
        self.capital = capital
        self.risk_pct = risk_pct
        self.risk_per_trade = capital * (risk_pct / 100)
        self.fee_pct = fee_pct / 100
        self.total_fees_paid = 0
        self.current_trade = None
        self.trades = []

    def _calculate_buy_quantity(self, risk_per_stock, price):
        max_by_cap = self.capital / price
        max_by_risk = self.risk_per_trade / risk_per_stock
        affordable = min(max_by_cap, max_by_risk)
        return max(0, round(affordable, 2))

    def open_position(
        self, trade_type, price, risk_amount, entry_date, entry_step
    ):
        if self.current_trade:
            return  # Already in a trade

        qty = self._calculate_buy_quantity(risk_amount, price)
        if qty == 0:
            return

        trade_value = qty * price
        entry_fee = trade_value * self.fee_pct

        self.capital -= trade_value + entry_fee
        self.total_fees_paid += entry_fee

        self.current_trade = {
            "entry_price": price,
            "quantity": qty,
            "type": trade_type,
            "stop_loss": price - risk_amount
            if trade_type == "buy"
            else price + risk_amount,
            "risk_taken": risk_amount,
            "entry_step": entry_step,
            "entry_date": entry_date,
            "entry_fee": entry_fee,
        }

    def close_position(self, price, exit_date, exit_step, action="exit"):
        if not self.current_trade:
            return

        qty = self.current_trade["quantity"]
        entry_price = self.current_trade["entry_price"]

        trade_value = qty * price
        exit_fee = trade_value * self.fee_pct

        if self.current_trade["type"] == "buy":
            gross_profit_loss = (price - entry_price) * qty
        else:  # sell/short
            gross_profit_loss = (entry_price - price) * qty

        total_fees = self.current_trade["entry_fee"] + exit_fee
        net_profit_loss = gross_profit_loss - total_fees

        self.capital += trade_value - exit_fee
        self.total_fees_paid += exit_fee

        trade_record = {
            "entry_step": self.current_trade["entry_step"],
            "exit_step": exit_step,
            "entry_date": self.current_trade["entry_date"],
            "exit_date": exit_date,
            "entry_price": entry_price,
            "exit_price": price,
            "quantity": qty,
            "type": self.current_trade["type"],
            "stop_loss": self.current_trade["stop_loss"],
            "risk_taken": self.current_trade["risk_taken"],
            "exit_reason": action,
            "gross_profit_loss": gross_profit_loss,
            "entry_fee": self.current_trade["entry_fee"],
            "exit_fee": exit_fee,
            "total_fees": total_fees,
            "net_profit_loss": net_profit_loss,
            "gross_profit_loss_pct": (gross_profit_loss / (entry_price * qty)) * 100,
            "net_profit_loss_pct": (net_profit_loss / (entry_price * qty)) * 100,
        }

        self.trades.append(trade_record)
        self.current_trade = None

    def summary(self):
        # Calculate overall net profit based on capital change
        net_profit = self.capital - self.initial_capital
        # Calculate overall gross profit by adding total fees back to net profit
        gross_profit = net_profit + self.total_fees_paid

        return {
            "total_trades": len(self.trades),
            "gross_profit": gross_profit, # This is the overall gross profit
            "total_fees_paid": self.total_fees_paid,
            "net_profit": net_profit, # This is the overall net profit
            "final_capital": self.capital,
            "initial_capital": self.initial_capital,
            "trades": self.trades,
        }

    def print_summary(self):
        summary_data = self.summary()
        print("--- Backtest Summary ---")
        print(f"Total Trades: {summary_data['total_trades']}")
        print(f"Gross Profit: {summary_data['gross_profit']:.2f}") # Changed key
        print(f"Total Fees Paid: {summary_data['total_fees_paid']:.2f}")
        print(f"Net Profit: {summary_data['net_profit']:.2f}") # Changed key
        print(f"Final Capital: {summary_data['final_capital']:.2f}")
        print("------------------------")
