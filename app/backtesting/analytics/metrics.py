import math

import numpy as np

from app.backtesting.types import BacktestMetrics, TradeResult


class MetricsCalculator:
    """Calculates standard quantitative finance metrics based on TradeResults."""
    
    @staticmethod
    def calculate(trades: list[TradeResult], initial_capital: float) -> BacktestMetrics:
        if not trades:
            return MetricsCalculator._empty_metrics()
            
        pnls = [t.pnl for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        
        net_profit = sum(pnls)
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        win_rate = len(wins) / len(trades)
        
        avg_win = np.mean(wins) if wins else 0.0
        avg_loss = np.mean(losses) if losses else 0.0
        
        risk_reward = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        # Drawdown calculation
        equity = initial_capital
        peak = initial_capital
        max_dd = 0.0
        
        for pnl in pnls:
            equity += pnl
            peak = max(peak, equity)
            dd = peak - equity
            max_dd = max(max_dd, dd)
                
        max_dd_percent = (max_dd / peak) if peak > 0 else 0.0
        
        # Simple Sharpe (annualized approximation based on trade returns)
        returns = np.array([t.pnl_percent for t in trades])
        std_dev = np.std(returns) if len(returns) > 1 else 0.0
        mean_ret = np.mean(returns) if len(returns) > 0 else 0.0
        sharpe = (mean_ret / std_dev) * math.sqrt(252) if std_dev > 0 else 0.0
        
        return BacktestMetrics(
            net_profit=net_profit,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            profit_factor=profit_factor,
            win_rate=win_rate,
            total_trades=len(trades),
            winning_trades=len(wins),
            losing_trades=len(losses),
            average_win=avg_win,
            average_loss=avg_loss,
            risk_reward_ratio=risk_reward,
            expectancy=expectancy,
            max_drawdown=max_dd,
            max_drawdown_percent=max_dd_percent,
            sharpe_ratio=sharpe,
            sortino_ratio=0.0, # Stub
            calmar_ratio=0.0, # Stub
            recovery_factor=net_profit / max_dd if max_dd > 0 else float('inf'),
            consecutive_wins=0, # Stub
            consecutive_losses=0 # Stub
        )
        
    @staticmethod
    def _empty_metrics() -> BacktestMetrics:
        return BacktestMetrics(
            net_profit=0, gross_profit=0, gross_loss=0, profit_factor=0, win_rate=0,
            total_trades=0, winning_trades=0, losing_trades=0, average_win=0, average_loss=0,
            risk_reward_ratio=0, expectancy=0, max_drawdown=0, max_drawdown_percent=0,
            sharpe_ratio=0, sortino_ratio=0, calmar_ratio=0, recovery_factor=0,
            consecutive_wins=0, consecutive_losses=0
        )
