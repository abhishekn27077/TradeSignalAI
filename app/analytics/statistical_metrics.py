import math


class StatisticalMetrics:
    @staticmethod
    def calculate_win_rate(trades: list[dict]) -> float:
        if not trades: return 0.0
        wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
        return (wins / len(trades)) * 100

    @staticmethod
    def calculate_profit_factor(trades: list[dict]) -> float:
        gross_profit = sum(t.get("pnl", 0) for t in trades if t.get("pnl", 0) > 0)
        gross_loss = abs(sum(t.get("pnl", 0) for t in trades if t.get("pnl", 0) < 0))
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        return gross_profit / gross_loss

    @staticmethod
    def maximum_drawdown(trades: list[dict], initial_balance: float = 100000.0) -> float:
        peak = initial_balance
        max_dd = 0.0
        current_balance = initial_balance
        for t in trades:
            current_balance += t.get("pnl", 0)
            peak = max(peak, current_balance)
            dd = (peak - current_balance) / peak
            max_dd = max(max_dd, dd)
        return max_dd * 100

    @staticmethod
    def calculate_sharpe_ratio(trades: list[dict], risk_free_rate: float = 0.0) -> float:
        if not trades or len(trades) < 2: return 0.0
        returns = [t.get("pnl", 0) for t in trades]
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = math.sqrt(variance)
        if std_dev == 0: return 0.0
        return (avg_return - risk_free_rate) / std_dev

    @staticmethod
    def calculate_sortino_ratio(trades: list[dict], risk_free_rate: float = 0.0) -> float:
        if not trades or len(trades) < 2: return 0.0
        returns = [t.get("pnl", 0) for t in trades]
        avg_return = sum(returns) / len(returns)
        negative_returns = [r for r in returns if r < 0]
        if not negative_returns: return float('inf')
        downside_variance = sum((r - 0) ** 2 for r in negative_returns) / len(returns)
        downside_std_dev = math.sqrt(downside_variance)
        if downside_std_dev == 0: return 0.0
        return (avg_return - risk_free_rate) / downside_std_dev

    @staticmethod
    def calculate_calmar_ratio(trades: list[dict], initial_balance: float = 100000.0) -> float:
        max_dd = StatisticalMetrics.maximum_drawdown(trades, initial_balance) / 100.0
        if max_dd == 0: return float('inf')
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        cagr = total_pnl / initial_balance
        return cagr / max_dd

    @staticmethod
    def calculate_recovery_factor(trades: list[dict], initial_balance: float = 100000.0) -> float:
        max_dd_val = 0.0
        peak = initial_balance
        current_balance = initial_balance
        for t in trades:
            current_balance += t.get("pnl", 0)
            peak = max(peak, current_balance)
            dd_val = peak - current_balance
            max_dd_val = max(max_dd_val, dd_val)
        
        total_profit = sum(t.get("pnl", 0) for t in trades)
        if max_dd_val == 0: return float('inf')
        return total_profit / max_dd_val

    @staticmethod
    def calculate_average_r_multiple(trades: list[dict]) -> float:
        if not trades: return 0.0
        wins = [t.get("pnl", 0) for t in trades if t.get("pnl", 0) > 0]
        losses = [abs(t.get("pnl", 0)) for t in trades if t.get("pnl", 0) < 0]
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 1.0
        return avg_win / avg_loss

    @staticmethod
    def calculate_streaks(trades: list[dict]) -> dict:
        max_wins = 0
        max_losses = 0
        curr_wins = 0
        curr_losses = 0
        for t in trades:
            if t.get("pnl", 0) > 0:
                curr_wins += 1
                curr_losses = 0
                max_wins = max(max_wins, curr_wins)
            elif t.get("pnl", 0) < 0:
                curr_losses += 1
                curr_wins = 0
                max_losses = max(max_losses, curr_losses)
        return {"consecutive_wins": max_wins, "consecutive_losses": max_losses}
