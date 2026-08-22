import math
from typing import Any

import numpy as np

from app.database.models.journal import TradeRecord


class AnalyticsEngine:
    """Calculates global performance metrics from journal entries."""
    
    @staticmethod
    def calculate_statistics(trades: list[TradeRecord], initial_capital: float = 10000.0) -> dict[str, Any]:
        if not trades:
            return {}
            
        pnls = [t.pnl for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        net_profit = sum(pnls)
        
        win_rate = len(wins) / len(trades)
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        avg_win = np.mean(wins) if wins else 0.0
        avg_loss = abs(np.mean(losses)) if losses else 0.0
        risk_reward = (avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        # Max Drawdown & Recovery Factor
        equity = initial_capital
        peak = initial_capital
        max_dd = 0.0
        for pnl in pnls:
            equity += pnl
            peak = max(peak, equity)
            dd = peak - equity
            max_dd = max(max_dd, dd)
        
        max_dd_percent = (max_dd / peak) * 100 if peak > 0 else 0.0
        recovery_factor = net_profit / max_dd if max_dd > 0 else float('inf')
        
        # Risk / Ratios
        returns = np.array([pnl / initial_capital for pnl in pnls])
        std_dev = np.std(returns) if len(returns) > 1 else 0.0
        mean_ret = np.mean(returns) if len(returns) > 0 else 0.0
        sharpe = (mean_ret / std_dev) * math.sqrt(252) if std_dev > 0 else 0.0
        
        downside_returns = np.array([r for r in returns if r < 0])
        downside_std_dev = np.std(downside_returns) if len(downside_returns) > 1 else 0.0
        sortino = (mean_ret / downside_std_dev) * math.sqrt(252) if downside_std_dev > 0 else float('inf') if mean_ret > 0 else 0.0
        
        # Trade metrics
        largest_win = max(wins) if wins else 0.0
        largest_loss = min(losses) if losses else 0.0
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        # Groupings for Phase 8 & 10
        strategy_pnl = {}
        regime_pnl = {}
        session_pnl = {}
        quality_dist = {}
        hold_times = []
        
        for t in trades:
            # Strategy Ranking
            strat = getattr(t, 'strategy', 'Unknown')
            strategy_pnl[strat] = strategy_pnl.get(strat, 0) + t.pnl
            
            # Regime Ranking
            regime = getattr(t, 'market_regime', 'Unknown')
            if regime:
                regime_pnl[regime] = regime_pnl.get(regime, 0) + t.pnl
                
            # Session Analysis
            session = getattr(t, 'session', 'Unknown')
            if session:
                session_pnl[session] = session_pnl.get(session, 0) + t.pnl
                
            # Trade Quality
            qual = getattr(t, 'trade_quality', 'Unknown')
            if qual:
                quality_dist[qual] = quality_dist.get(qual, 0) + 1
                
            # Holding Time
            if t.exit_time and t.entry_time:
                hold_times.append((t.exit_time - t.entry_time).total_seconds() / 3600.0)

        strategy_ranking = sorted([{"name": k, "pnl": v} for k, v in strategy_pnl.items()], key=lambda x: x["pnl"], reverse=True)
        regime_ranking = sorted([{"regime": k, "pnl": v} for k, v in regime_pnl.items()], key=lambda x: x["pnl"], reverse=True)
        session_analysis = sorted([{"session": k, "pnl": v} for k, v in session_pnl.items()], key=lambda x: x["pnl"], reverse=True)
        
        return {
            "total_trades": len(trades),
            "net_profit": net_profit,
            "win_rate": win_rate * 100,
            "profit_factor": profit_factor,
            "average_win": avg_win,
            "average_loss": avg_loss,
            "largest_win": largest_win,
            "largest_loss": largest_loss,
            "expectancy": expectancy,
            "risk_reward_ratio": risk_reward,
            "max_drawdown_percent": max_dd_percent,
            "recovery_factor": recovery_factor,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "consecutive_wins": AnalyticsEngine._max_consecutive(pnls, True),
            "consecutive_losses": AnalyticsEngine._max_consecutive(pnls, False),
            
            # Phase 8 & 10 Advanced Metrics
            "strategy_ranking": strategy_ranking,
            "regime_ranking": regime_ranking,
            "session_analysis": session_analysis,
            "trade_quality_distribution": quality_dist,
            "avg_holding_time_hours": sum(hold_times)/len(hold_times) if hold_times else 0.0
        }

    @staticmethod
    def _max_consecutive(pnls: list[float], positive: bool) -> int:
        max_streak = 0
        current_streak = 0
        for p in pnls:
            condition = (p > 0) if positive else (p <= 0)
            if condition:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        return max_streak
        
    @staticmethod
    def calibrate_confidence(strategy_name: str, base_confidence: float, trades: list[TradeRecord]) -> float:
        """
        Phase 9: Confidence Calibration
        Adjusts the raw AI/Strategy confidence based on the historical win rate of that specific strategy.
        """
        strat_trades = [t for t in trades if getattr(t, 'strategy', None) == strategy_name]
        if not strat_trades or len(strat_trades) < 10:
            return base_confidence # Not enough data to calibrate
            
        wins = len([t for t in strat_trades if t.pnl > 0])
        win_rate = wins / len(strat_trades)
        
        # If win rate is high, boost confidence slightly. If low, penalize it.
        # Calibration curve: centered at 0.5 win rate
        calibration_multiplier = 0.5 + win_rate 
        
        calibrated = base_confidence * calibration_multiplier
        return min(1.0, max(0.0, calibrated))

analytics_engine = AnalyticsEngine()
