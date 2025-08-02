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

    def _calculate_position_size(self, risk_per_share, price):
        """Calculate position size based on fixed risk amount."""
        # Fixed risk amount based on initial capital
        max_risk_amount = self.risk_per_trade
        
        # Calculate max position size based on risk management
        if risk_per_share <= 0:
            return 0
            
        max_by_risk = max_risk_amount / risk_per_share
        
        # Calculate max position size based on available capital
        max_by_capital = self.capital / price
        
        # Take the minimum to ensure we don't exceed either constraint
        position_size = min(max_by_risk, max_by_capital)
        
        return max(0, round(position_size, 2))

    def open_position(
        self, trade_type, price, stop_loss, risk_per_share, entry_date, entry_step
    ):
        if self.current_trade:
            return  # Already in a trade

        qty = self._calculate_position_size(risk_per_share, price)
        if qty == 0:
            return

        trade_value = qty * price
        entry_fee = trade_value * self.fee_pct

        # FIXED: Handle long and short positions differently
        if trade_type == "buy":
            # Long position: we pay for shares + fee
            self.capital -= trade_value + entry_fee
        else:  # trade_type == "sell" (short)
            # Short position: we receive cash from sale - fee
            self.capital += trade_value - entry_fee
            
        self.total_fees_paid += entry_fee

        # Calculate actual risk taken (should be close to risk_per_trade for proper sizing)
        actual_risk_taken = qty * risk_per_share

        self.current_trade = {
            "entry_price": price,
            "quantity": qty,
            "type": trade_type,
            "stop_loss": stop_loss if stop_loss is not None else (
                price - risk_per_share if trade_type == "buy" else price + risk_per_share
            ),
            "risk_taken": actual_risk_taken,
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

        # FIXED: Handle long and short position closures differently
        if self.current_trade["type"] == "buy":
            # Closing long position: we sell shares and receive cash - fee
            self.capital += trade_value - exit_fee
        else:  # closing short position
            # Closing short position: we buy shares to cover and pay cash + fee
            self.capital -= trade_value + exit_fee
            
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

    def update_stop_loss(self, new_stop_loss):
        """Update the stop loss for the current trade."""
        if self.current_trade:
            self.current_trade["stop_loss"] = new_stop_loss

    def close_any_open_trade(self, current_price, current_date, current_step):
        """Close any remaining open trade at the end of backtesting."""
        if self.current_trade:
            print(f"⚠️  WARNING: Closing unclosed trade at end of backtest")
            print(f"   Entry: {self.current_trade['entry_price']:.4f} -> Exit: {current_price:.4f}")
            self.close_position(current_price, current_date, current_step, "end_of_backtest")
            return True
        return False

    def diagnose_capital_discrepancy(self):
        """Diagnose any discrepancy between trade records and final capital."""
        if not self.trades:
            return
            
        # Calculate expected capital from trade records
        trade_net_total = sum(t["net_profit_loss"] for t in self.trades)
        expected_capital = self.initial_capital + trade_net_total
        actual_capital = self.capital
        discrepancy = actual_capital - expected_capital
        
        print(f"\n🔍 CAPITAL TRACKING DIAGNOSIS:")
        print(f"   Initial Capital:     ${self.initial_capital:,.2f}")
        print(f"   Sum of Trade P&L:    ${trade_net_total:,.2f}")
        print(f"   Expected Final:      ${expected_capital:,.2f}")
        print(f"   Actual Final:        ${actual_capital:,.2f}")
        print(f"   Discrepancy:         ${discrepancy:,.2f}")
        
        if abs(discrepancy) > 1:  # More than $1 difference
            print(f"   ⚠️  SIGNIFICANT DISCREPANCY DETECTED!")
            if self.current_trade:
                print(f"   💡 Possible cause: Unclosed trade with capital tied up")
                open_trade_value = self.current_trade["quantity"] * self.current_trade["entry_price"]
                print(f"   Open trade value: ${open_trade_value:,.2f}")
        else:
            print(f"   ✅ Capital tracking appears consistent")

    def _calculate_trading_statistics(self):
        """Calculate comprehensive trading statistics."""
        if not self.trades:
            return {
                "winning_trades": 0, "losing_trades": 0, "win_rate": 0.0,
                "avg_win": 0.0, "avg_loss": 0.0, "avg_trade": 0.0,
                "max_win": 0.0, "max_loss": 0.0, "profit_factor": 0.0,
                "expectancy": 0.0, "max_consecutive_wins": 0, "max_consecutive_losses": 0,
                "current_streak": 0, "current_streak_type": "None", "max_drawdown": 0.0,
                "max_drawdown_pct": 0.0, "sharpe_ratio": 0.0, "total_long_trades": 0,
                "total_short_trades": 0, "long_win_rate": 0.0, "short_win_rate": 0.0,
                "avg_trade_duration": 0.0, "best_trade": 0.0, "worst_trade": 0.0
            }

        # Separate winning and losing trades
        winning_trades = [t for t in self.trades if t["net_profit_loss"] > 0]
        losing_trades = [t for t in self.trades if t["net_profit_loss"] < 0]
        breakeven_trades = [t for t in self.trades if t["net_profit_loss"] == 0]
        
        # Long and short trades analysis
        long_trades = [t for t in self.trades if t["type"] == "long"]
        short_trades = [t for t in self.trades if t["type"] == "short"]
        long_winning = [t for t in long_trades if t["net_profit_loss"] > 0]
        short_winning = [t for t in short_trades if t["net_profit_loss"] > 0]

        # Basic statistics
        total_trades = len(self.trades)
        winning_count = len(winning_trades)
        losing_count = len(losing_trades)
        win_rate = (winning_count / total_trades) * 100 if total_trades > 0 else 0

        # Profit/Loss calculations - Use individual trade data for trade-specific metrics
        total_wins = sum(t["net_profit_loss"] for t in winning_trades)
        total_losses = abs(sum(t["net_profit_loss"] for t in losing_trades))  # Make positive for display
        avg_win = total_wins / winning_count if winning_count > 0 else 0
        avg_loss = total_losses / losing_count if losing_count > 0 else 0
        
        # FIXED: Use actual capital change for expectancy calculation
        actual_net_profit = self.capital - self.initial_capital
        avg_trade = actual_net_profit / total_trades if total_trades > 0 else 0

        # Max win/loss from individual trades
        max_win = max((t["net_profit_loss"] for t in self.trades), default=0)
        max_loss = min((t["net_profit_loss"] for t in self.trades), default=0)

        # FIXED: Profit factor should be based on actual wins vs losses from trades
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf') if total_wins > 0 else 0
        
        # FIXED: Expectancy is the expected value per trade based on actual performance
        expectancy = avg_trade  # This is the true expectancy

        # Consecutive wins/losses
        consecutive_stats = self._calculate_consecutive_trades()

        # Drawdown calculation
        drawdown_stats = self._calculate_drawdown()

        # Trade duration analysis
        durations = []
        for trade in self.trades:
            if 'entry_date' in trade and 'exit_date' in trade:
                try:
                    entry_date = pd.to_datetime(trade['entry_date'])
                    exit_date = pd.to_datetime(trade['exit_date'])
                    duration = (exit_date - entry_date).total_seconds() / 3600  # hours
                    durations.append(duration)
                except:
                    pass
        
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Sharpe ratio (simplified - using trade returns)
        if len(self.trades) > 1:
            trade_returns = [t["net_profit_loss_pct"] for t in self.trades]
            avg_return = sum(trade_returns) / len(trade_returns)
            return_std = (sum((r - avg_return) ** 2 for r in trade_returns) / len(trade_returns)) ** 0.5
            sharpe_ratio = avg_return / return_std if return_std > 0 else 0
        else:
            sharpe_ratio = 0

        return {
            # Win/Loss Statistics
            "winning_trades": winning_count,
            "losing_trades": losing_count,
            "breakeven_trades": len(breakeven_trades),
            "win_rate": win_rate,
            
            # Profit/Loss Analysis
            "total_wins": total_wins,
            "total_losses": total_losses,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "avg_trade": avg_trade,
            "max_win": max_win,
            "max_loss": max_loss,
            "best_trade": max_win,
            "worst_trade": max_loss,
            
            # Performance Metrics
            "profit_factor": profit_factor,
            "expectancy": expectancy,
            "sharpe_ratio": sharpe_ratio,
            
            # Consecutive Trade Analysis
            **consecutive_stats,
            
            # Drawdown Analysis
            **drawdown_stats,
            
            # Long vs Short Analysis
            "total_long_trades": len(long_trades),
            "total_short_trades": len(short_trades),
            "long_win_rate": (len(long_winning) / len(long_trades)) * 100 if long_trades else 0,
            "short_win_rate": (len(short_winning) / len(short_trades)) * 100 if short_trades else 0,
            
            # Duration Analysis
            "avg_trade_duration": avg_duration,
        }
        for trade in self.trades:
            if 'entry_date' in trade and 'exit_date' in trade:
                try:
                    entry_date = pd.to_datetime(trade['entry_date'])
                    exit_date = pd.to_datetime(trade['exit_date'])
                    duration = (exit_date - entry_date).total_seconds() / 3600  # hours
                    durations.append(duration)
                except:
                    pass
        
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Sharpe ratio (simplified - using trade returns)
        if len(self.trades) > 1:
            trade_returns = [t["net_profit_loss_pct"] for t in self.trades]
            avg_return = sum(trade_returns) / len(trade_returns)
            return_std = (sum((r - avg_return) ** 2 for r in trade_returns) / len(trade_returns)) ** 0.5
            sharpe_ratio = avg_return / return_std if return_std > 0 else 0
        else:
            sharpe_ratio = 0

        return {
            # Win/Loss Statistics
            "winning_trades": winning_count,
            "losing_trades": losing_count,
            "breakeven_trades": len(breakeven_trades),
            "win_rate": win_rate,
            
            # Profit/Loss Analysis
            "total_wins": total_wins,
            "total_losses": total_losses,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "avg_trade": avg_trade,
            "max_win": max_win,
            "max_loss": max_loss,
            "best_trade": max_win,
            "worst_trade": max_loss,
            
            # Performance Metrics
            "profit_factor": profit_factor,
            "expectancy": expectancy,
            "sharpe_ratio": sharpe_ratio,
            
            # Consecutive Trade Analysis
            **consecutive_stats,
            
            # Drawdown Analysis
            **drawdown_stats,
            
            # Long vs Short Analysis
            "total_long_trades": len(long_trades),
            "total_short_trades": len(short_trades),
            "long_win_rate": (len(long_winning) / len(long_trades)) * 100 if long_trades else 0,
            "short_win_rate": (len(short_winning) / len(short_trades)) * 100 if short_trades else 0,
            
            # Duration Analysis
            "avg_trade_duration": avg_duration,
        }

    def _calculate_consecutive_trades(self):
        """Calculate consecutive wins/losses statistics."""
        if not self.trades:
            return {
                "max_consecutive_wins": 0,
                "max_consecutive_losses": 0,
                "current_streak": 0,
                "current_streak_type": "None"
            }

        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in self.trades:
            if trade["net_profit_loss"] > 0:  # Winning trade
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            elif trade["net_profit_loss"] < 0:  # Losing trade
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
            else:  # Breakeven trade
                current_wins = 0
                current_losses = 0

        # Current streak
        if current_wins > 0:
            current_streak = current_wins
            current_streak_type = "Wins"
        elif current_losses > 0:
            current_streak = current_losses
            current_streak_type = "Losses"
        else:
            current_streak = 0
            current_streak_type = "None"

        return {
            "max_consecutive_wins": max_consecutive_wins,
            "max_consecutive_losses": max_consecutive_losses,
            "current_streak": current_streak,
            "current_streak_type": current_streak_type
        }

    def _calculate_drawdown(self):
        """Calculate maximum drawdown statistics."""
        if not self.trades:
            return {"max_drawdown": 0.0, "max_drawdown_pct": 0.0}

        capital_history = [self.initial_capital]
        running_capital = self.initial_capital
        for trade in self.trades:
            capital_history.append(running_capital + trade["net_profit_loss"])
            running_capital += trade["net_profit_loss"]

        peak_capital = self.initial_capital
        max_drawdown = 0.0

        for capital in capital_history:
            if capital > peak_capital:
                peak_capital = capital
            
            drawdown = peak_capital - capital
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        max_drawdown_pct = (max_drawdown / peak_capital) * 100 if peak_capital > 0 else 0

        return {
            "max_drawdown": max_drawdown,
            "max_drawdown_pct": max_drawdown_pct
        }

    def summary(self):
        # Calculate overall net profit based on capital change
        net_profit = self.capital - self.initial_capital
        # Calculate overall gross profit by adding total fees back to net profit
        gross_profit = net_profit + self.total_fees_paid

        # Check for unclosed trades
        has_open_trade = self.current_trade is not None

        # Calculate detailed trading statistics
        trades_stats = self._calculate_trading_statistics()

        return {
            "total_trades": len(self.trades),
            "gross_profit": gross_profit, # This is the overall gross profit
            "total_fees_paid": self.total_fees_paid,
            "net_profit": net_profit, # This is the overall net profit
            "final_capital": self.capital,
            "initial_capital": self.initial_capital,
            "trades": self.trades,
            "has_open_trade": has_open_trade,
            "open_trade_info": self.current_trade if has_open_trade else None,
            **trades_stats  # Add all trading statistics
        }

    def print_summary(self):
        summary_data = self.summary()
        
        print("\n" + "="*60)
        print("           COMPREHENSIVE BACKTEST SUMMARY")
        print("="*60)
        
        # Basic Performance
        print(f"\n📊 BASIC PERFORMANCE:")
        print(f"   Initial Capital:     ${summary_data['initial_capital']:,.2f}")
        print(f"   Final Capital:       ${summary_data['final_capital']:,.2f}")
        print(f"   Total Return:        ${summary_data['net_profit']:,.2f} ({((summary_data['final_capital']/summary_data['initial_capital']-1)*100):+.2f}%)")
        print(f"   Gross Profit:        ${summary_data['gross_profit']:,.2f}")
        print(f"   Total Fees Paid:     ${summary_data['total_fees_paid']:,.2f}")
        
        # Trade Analysis
        print(f"\n📈 TRADE ANALYSIS:")
        print(f"   Total Trades:        {summary_data['total_trades']}")
        print(f"   Winning Trades:      {summary_data['winning_trades']} ({summary_data['win_rate']:.1f}%)")
        print(f"   Losing Trades:       {summary_data['losing_trades']} ({100-summary_data['win_rate']:.1f}%)")
        print(f"   Breakeven Trades:    {summary_data['breakeven_trades']}")
        
        # Profit/Loss Metrics
        print(f"\n💰 PROFIT/LOSS METRICS:")
        print(f"   Average Trade:       ${summary_data['avg_trade']:,.2f}")
        print(f"   Average Win:         ${summary_data['avg_win']:,.2f}")
        print(f"   Average Loss:        ${summary_data['avg_loss']:,.2f}")
        print(f"   Best Trade:          ${summary_data['best_trade']:,.2f}")
        print(f"   Worst Trade:         ${summary_data['worst_trade']:,.2f}")
        
        # Performance Ratios
        print(f"\n📊 PERFORMANCE RATIOS:")
        print(f"   Profit Factor:       {summary_data['profit_factor']:.2f}")
        print(f"   Expectancy:          ${summary_data['expectancy']:,.2f}")
        print(f"   Sharpe Ratio:        {summary_data['sharpe_ratio']:.2f}")
        
        # Risk Analysis
        print(f"\n⚠️  RISK ANALYSIS:")
        print(f"   Max Drawdown:        ${summary_data['max_drawdown']:,.2f} ({summary_data['max_drawdown_pct']:.2f}%)")
        
        # Consecutive Trades
        print(f"\n🔄 CONSECUTIVE TRADES:")
        print(f"   Max Consecutive Wins:   {summary_data['max_consecutive_wins']}")
        print(f"   Max Consecutive Losses: {summary_data['max_consecutive_losses']}")
        print(f"   Current Streak:         {summary_data['current_streak']} {summary_data['current_streak_type']}")
        
        # Long vs Short Analysis
        if summary_data['total_long_trades'] > 0 or summary_data['total_short_trades'] > 0:
            print(f"\n📊 LONG vs SHORT ANALYSIS:")
            print(f"   Long Trades:         {summary_data['total_long_trades']} (Win Rate: {summary_data['long_win_rate']:.1f}%)")
            print(f"   Short Trades:        {summary_data['total_short_trades']} (Win Rate: {summary_data['short_win_rate']:.1f}%)")
        
        # Duration Analysis
        if summary_data['avg_trade_duration'] > 0:
            print(f"\n⏱️  DURATION ANALYSIS:")
            if summary_data['avg_trade_duration'] < 24:
                print(f"   Avg Trade Duration:  {summary_data['avg_trade_duration']:.1f} hours")
            else:
                print(f"   Avg Trade Duration:  {summary_data['avg_trade_duration']/24:.1f} days")
        
        # Performance Rating
        print(f"\n🎯 PERFORMANCE RATING:")
        rating = self._get_performance_rating(summary_data)
        print(f"   Overall Rating:      {rating}")
        
        # Unclosed trades warning
        if summary_data.get('has_open_trade', False):
            open_trade = summary_data['open_trade_info']
            print(f"\n⚠️  UNCLOSED TRADE WARNING:")
            print(f"   Open Trade Type:     {open_trade['type']}")
            print(f"   Entry Price:         ${open_trade['entry_price']:.4f}")
            print(f"   Entry Date:          {open_trade['entry_date']}")
            print(f"   Stop Loss:           ${open_trade['stop_loss']:.4f}")
            print(f"   Risk Taken:          ${open_trade['risk_taken']:.2f}")
            print(f"   ⚠️  This trade is not included in final calculations!")
        
        # Add capital tracking diagnosis
        self.diagnose_capital_discrepancy()
        
        print("="*60)

    def _get_performance_rating(self, summary_data):
        """Generate a simple performance rating based on key metrics."""
        score = 0
        
        # FIXED: Check if we have negative returns first
        return_pct = ((summary_data['final_capital']/summary_data['initial_capital'])-1)*100
        
        # If overall return is negative, cap the score severely
        if return_pct < 0:
            score = max(-5, score - 3)  # Heavy penalty for negative returns
        
        # Win rate score (0-3 points)
        if summary_data['win_rate'] >= 60:
            score += 3
        elif summary_data['win_rate'] >= 50:
            score += 2
        elif summary_data['win_rate'] >= 40:
            score += 1
            
        # Profit factor score (0-3 points)
        if summary_data['profit_factor'] >= 2.0:
            score += 3
        elif summary_data['profit_factor'] >= 1.5:
            score += 2
        elif summary_data['profit_factor'] >= 1.0:
            score += 1
            
        # Return score (0-2 points) - only positive for positive returns
        if return_pct >= 20:
            score += 2
        elif return_pct >= 10:
            score += 1
            
        # Drawdown penalty (0-2 points deducted)
        if summary_data['max_drawdown_pct'] <= 5:
            pass  # No penalty
        elif summary_data['max_drawdown_pct'] <= 10:
            score -= 1
        else:
            score -= 2
            
        # Convert score to rating
        if score >= 7:
            return "⭐⭐⭐⭐⭐ EXCELLENT"
        elif score >= 5:
            return "⭐⭐⭐⭐ GOOD"
        elif score >= 3:
            return "⭐⭐⭐ AVERAGE"
        elif score >= 1:
            return "⭐⭐ BELOW AVERAGE"
        else:
            return "⭐ POOR"
