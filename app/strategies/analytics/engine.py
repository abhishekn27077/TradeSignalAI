import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from app.logs.logger import get_logger

logger = get_logger(__name__)


@dataclass
class StrategyAnalytics:
    strategy_name: str = ""
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    avg_hold_time_minutes: float = 0.0
    avg_r_multiple: float = 0.0
    total_pnl: float = 0.0
    regime_performance: dict[str, Any] = field(default_factory=dict)
    asset_performance: dict[str, Any] = field(default_factory=dict)
    session_performance: dict[str, Any] = field(default_factory=dict)
    best_asset: str = ""
    worst_asset: str = ""

    def to_dict(self) -> dict:
        return {
            "strategy_name": self.strategy_name,
            "total_trades": self.total_trades,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": round(self.win_rate, 2),
            "profit_factor": round(self.profit_factor, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "sortino_ratio": round(self.sortino_ratio, 2),
            "max_drawdown_pct": round(self.max_drawdown_pct, 2),
            "avg_profit": round(self.avg_profit, 2),
            "avg_loss": round(self.avg_loss, 2),
            "avg_hold_time_minutes": round(self.avg_hold_time_minutes, 1),
            "avg_r_multiple": round(self.avg_r_multiple, 2),
            "total_pnl": round(self.total_pnl, 2),
            "regime_performance": self.regime_performance,
            "asset_performance": self.asset_performance,
            "session_performance": self.session_performance,
            "best_asset": self.best_asset,
            "worst_asset": self.worst_asset,
        }


class StrategyAnalyticsEngine:
    def __init__(self):
        self._analytics: dict[str, StrategyAnalytics] = {}

    def register_trade(
        self,
        strategy_name: str,
        pnl: float,
        direction: str,
        asset: str = "",
        session: str = "",
        regime: str = "",
        hold_minutes: float = 0,
        r_multiple: float = 0,
    ):
        if strategy_name not in self._analytics:
            self._analytics[strategy_name] = StrategyAnalytics(strategy_name=strategy_name)
        a = self._analytics[strategy_name]
        a.total_trades += 1
        if pnl > 0:
            a.wins += 1
        else:
            a.losses += 1
        a.total_pnl += pnl

        if not hasattr(a, '_trade_pnls'):
            a._trade_pnls = []
        a._trade_pnls.append(pnl)

        pnls = list(a._trade_pnls)
        wins_list = [p for p in pnls if p > 0]
        losses_list = [p for p in pnls if p <= 0]

        if a.total_trades > 0:
            a.win_rate = (a.wins / a.total_trades) * 100

        gross_profit = sum(wins_list) if wins_list else 0
        gross_loss = abs(sum(losses_list)) if losses_list else 0
        a.profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

        a.avg_profit = np.mean(wins_list) if wins_list else 0.0
        a.avg_loss = abs(np.mean(losses_list)) if losses_list else 0.0

        if hold_minutes > 0:
            if a.avg_hold_time_minutes == 0:
                a.avg_hold_time_minutes = hold_minutes
            else:
                a.avg_hold_time_minutes = (a.avg_hold_time_minutes * (a.total_trades - 1) + hold_minutes) / a.total_trades

        if r_multiple > 0:
            if a.avg_r_multiple == 0:
                a.avg_r_multiple = r_multiple
            else:
                a.avg_r_multiple = (a.avg_r_multiple * (a.total_trades - 1) + r_multiple) / a.total_trades

        returns_list = [p / 10000 for p in a._trade_pnls]
        if len(returns_list) > 1:
            std = np.std(returns_list)
            mean_ret = np.mean(returns_list)
            a.sharpe_ratio = (mean_ret / std) * math.sqrt(252) if std > 0 else 0.0
            downside = [r for r in returns_list if r < 0]
            downside_std = np.std(downside) if len(downside) > 1 else 0.0
            a.sortino_ratio = (mean_ret / downside_std) * math.sqrt(252) if downside_std > 0 else (float('inf') if mean_ret > 0 else 0.0)

        equity = 10000
        peak = 10000
        max_dd = 0
        for p in a._trade_pnls:
            equity += p
            peak = max(peak, equity)
            dd = peak - equity
            max_dd = max(max_dd, dd)
        a.max_drawdown_pct = (max_dd / peak) * 100 if peak > 0 else 0.0

        if regime:
            if regime not in a.regime_performance:
                a.regime_performance[regime] = {"trades": 0, "wins": 0, "pnl": 0.0}
            a.regime_performance[regime]["trades"] += 1
            if pnl > 0:
                a.regime_performance[regime]["wins"] += 1
            a.regime_performance[regime]["pnl"] += pnl

        if asset:
            if asset not in a.asset_performance:
                a.asset_performance[asset] = {"trades": 0, "wins": 0, "pnl": 0.0}
            a.asset_performance[asset]["trades"] += 1
            if pnl > 0:
                a.asset_performance[asset]["wins"] += 1
            a.asset_performance[asset]["pnl"] += pnl
            asset_pnls = {k: v["pnl"] for k, v in a.asset_performance.items()}
            if asset_pnls:
                a.best_asset = max(asset_pnls, key=asset_pnls.get)
                a.worst_asset = min(asset_pnls, key=asset_pnls.get)

        if session:
            if session not in a.session_performance:
                a.session_performance[session] = {"trades": 0, "wins": 0, "pnl": 0.0}
            a.session_performance[session]["trades"] += 1
            if pnl > 0:
                a.session_performance[session]["wins"] += 1
            a.session_performance[session]["pnl"] += pnl

    def get_analytics(self, strategy_name: str) -> StrategyAnalytics | None:
        return self._analytics.get(strategy_name)

    def get_all_analytics(self) -> dict[str, StrategyAnalytics]:
        return dict(self._analytics)

    def get_all_analytics_dict(self) -> list[dict]:
        return [a.to_dict() for a in self._analytics.values()]

    def clear(self, strategy_name: str | None = None):
        if strategy_name:
            self._analytics.pop(strategy_name, None)
        else:
            self._analytics.clear()


strategy_analytics_engine = StrategyAnalyticsEngine()
