import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from app.strategies.Backtesting.engine import BacktestTrade


@dataclass
class MonteCarloReport:
    asset: str
    timeframe: str
    iterations: int
    median_max_drawdown_pct: float
    percentile_95_drawdown_pct: float
    percentile_99_drawdown_pct: float
    probability_of_ruin_pct: float     # Drawdown > 20%
    expected_losing_streak_95pct: int
    median_ending_pnl: float
    pnl_confidence_interval_95: List[float]
    is_statistically_robust: bool
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "timeframe": self.timeframe,
            "iterations": self.iterations,
            "median_max_drawdown_pct": round(float(self.median_max_drawdown_pct), 2),
            "percentile_95_drawdown_pct": round(float(self.percentile_95_drawdown_pct), 2),
            "percentile_99_drawdown_pct": round(float(self.percentile_99_drawdown_pct), 2),
            "probability_of_ruin_pct": round(float(self.probability_of_ruin_pct), 2),
            "expected_losing_streak_95pct": self.expected_losing_streak_95pct,
            "median_ending_pnl": round(float(self.median_ending_pnl), 2),
            "pnl_confidence_interval_95": [round(float(x), 2) for x in self.pnl_confidence_interval_95],
            "is_statistically_robust": self.is_statistically_robust,
            "details": self.details,
        }


class MonteCarloEngine:
    """
    Bootstrap Monte Carlo Trade Sequence Resampling Engine.
    Evaluates tail risk distributions, drawdown boundaries, and ruin probabilities across 1000+ permutations.
    """

    def __init__(self, iterations: int = 1000, initial_capital: float = 10000.0):
        self.iterations = iterations
        self.initial_capital = initial_capital

    def run_simulation(
        self,
        trades: List[BacktestTrade],
        asset: str = "UNKNOWN",
        timeframe: str = "1H"
    ) -> MonteCarloReport:
        if not trades or len(trades) < 5:
            return MonteCarloReport(
                asset=asset, timeframe=timeframe, iterations=self.iterations,
                median_max_drawdown_pct=0.0, percentile_95_drawdown_pct=0.0,
                percentile_99_drawdown_pct=0.0, probability_of_ruin_pct=0.0,
                expected_losing_streak_95pct=0, median_ending_pnl=0.0,
                pnl_confidence_interval_95=[0.0, 0.0], is_statistically_robust=False
            )

        pnls = np.array([t.net_pnl for t in trades])
        n_trades = len(pnls)

        simulated_max_dds = []
        simulated_ending_pnls = []
        simulated_losing_streaks = []
        ruin_count = 0

        for _ in range(self.iterations):
            # Bootstrap resample with replacement
            sampled_pnls = np.random.choice(pnls, size=n_trades, replace=True)
            equity_curve = self.initial_capital + np.cumsum(sampled_pnls)

            # Drawdown calculation
            peak = np.maximum.accumulate(equity_curve)
            dd_pct = ((peak - equity_curve) / peak) * 100.0
            max_dd = float(np.max(dd_pct))
            simulated_max_dds.append(max_dd)

            if max_dd >= 20.0:
                ruin_count += 1

            ending_pnl = float(np.sum(sampled_pnls))
            simulated_ending_pnls.append(ending_pnl)

            # Longest losing streak in sample
            max_streak = 0
            cur_streak = 0
            for p in sampled_pnls:
                if p < 0:
                    cur_streak += 1
                    max_streak = max(max_streak, cur_streak)
                else:
                    cur_streak = 0
            simulated_losing_streaks.append(max_streak)

        median_dd = float(np.median(simulated_max_dds))
        dd_95 = float(np.percentile(simulated_max_dds, 95))
        dd_99 = float(np.percentile(simulated_max_dds, 99))
        prob_ruin = (ruin_count / self.iterations) * 100.0
        streak_95 = int(np.percentile(simulated_losing_streaks, 95))
        median_pnl = float(np.median(simulated_ending_pnls))
        ci_lower = float(np.percentile(simulated_ending_pnls, 2.5))
        ci_upper = float(np.percentile(simulated_ending_pnls, 97.5))

        is_robust = (prob_ruin < 5.0) and (dd_95 < 15.0) and (ci_lower > 0)

        return MonteCarloReport(
            asset=asset,
            timeframe=timeframe,
            iterations=self.iterations,
            median_max_drawdown_pct=median_dd,
            percentile_95_drawdown_pct=dd_95,
            percentile_99_drawdown_pct=dd_99,
            probability_of_ruin_pct=prob_ruin,
            expected_losing_streak_95pct=streak_95,
            median_ending_pnl=median_pnl,
            pnl_confidence_interval_95=[ci_lower, ci_upper],
            is_statistically_robust=is_robust
        )
