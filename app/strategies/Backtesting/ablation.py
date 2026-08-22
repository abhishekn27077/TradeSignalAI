import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from app.strategies.Backtesting.engine import RealisticBacktestEngine, BacktestSummary


@dataclass
class AblationLayerResult:
    layer_name: str
    is_active: bool
    win_rate: float
    sharpe_ratio: float
    profit_factor: float
    net_pnl: float
    delta_sharpe: float
    delta_win_rate: float
    delta_pnl: float
    edge_rating: str  # CRITICAL, HIGH_VALUE, MODERATE, LOW_VALUE, DETRIMENTAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer_name": self.layer_name,
            "is_active": self.is_active,
            "win_rate": round(float(self.win_rate), 2),
            "sharpe_ratio": round(float(self.sharpe_ratio), 2),
            "profit_factor": round(float(self.profit_factor), 2),
            "net_pnl": round(float(self.net_pnl), 2),
            "delta_sharpe": round(float(self.delta_sharpe), 2),
            "delta_win_rate": round(float(self.delta_win_rate), 2),
            "delta_pnl": round(float(self.delta_pnl), 2),
            "edge_rating": self.edge_rating,
        }


@dataclass
class AblationReport:
    asset: str
    timeframe: str
    baseline_win_rate: float
    baseline_sharpe: float
    baseline_pnl: float
    layers: List[AblationLayerResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "timeframe": self.timeframe,
            "baseline_win_rate": round(float(self.baseline_win_rate), 2),
            "baseline_sharpe": round(float(self.baseline_sharpe), 2),
            "baseline_pnl": round(float(self.baseline_pnl), 2),
            "layers": [l.to_dict() for l in self.layers]
        }


class AblationEngine:
    """
    Feature Ablation Study Engine.
    Quantifies the incremental out-of-sample edge and marginal predictive value of each structural layer.
    """

    def __init__(self):
        self.bt_engine = RealisticBacktestEngine()

    def run_ablation_study(
        self,
        df: pd.DataFrame,
        signals_by_layer: Dict[str, List[Dict[str, Any]]],
        asset: str = "UNKNOWN",
        timeframe: str = "1H"
    ) -> AblationReport:
        # Full baseline model
        full_signals = signals_by_layer.get("FULL_MODEL", [])
        base_summary = self.bt_engine.run_backtest(df, full_signals, asset=asset, timeframe=timeframe)

        base_wr = base_summary.win_rate
        base_sharpe = base_summary.sharpe_ratio
        base_pnl = base_summary.net_pnl

        layers_results: List[AblationLayerResult] = []

        layer_names = [
            ("WITHOUT_STRUCTURE", "Market Structure (BOS/CHoCH/MSB)"),
            ("WITHOUT_SMC", "Smart Money Concepts (OB & FVG)"),
            ("WITHOUT_LIQUIDITY", "Liquidity Pools & Sweeps"),
            ("WITHOUT_SESSIONS", "Sessions & Killzones"),
            ("WITHOUT_SMT", "SMT Divergence"),
            ("WITHOUT_TECHNICALS", "Technical Indicators (SuperTrend/UT Bot)"),
        ]

        for key, display_name in layer_names:
            ablated_sigs = signals_by_layer.get(key, [])
            if not ablated_sigs:
                # If subset not provided directly, simulate filter removal
                ablated_sigs = [s for s in full_signals if s.get("source_layer") != key]

            summary = self.bt_engine.run_backtest(df, ablated_sigs, asset=asset, timeframe=timeframe)

            delta_sharpe = base_sharpe - summary.sharpe_ratio
            delta_wr = base_wr - summary.win_rate
            delta_pnl = base_pnl - summary.net_pnl

            if delta_sharpe >= 0.40:
                rating = "CRITICAL"
            elif delta_sharpe >= 0.20:
                rating = "HIGH_VALUE"
            elif delta_sharpe >= 0.05:
                rating = "MODERATE"
            elif delta_sharpe >= -0.05:
                rating = "LOW_VALUE"
            else:
                rating = "DETRIMENTAL"

            layers_results.append(AblationLayerResult(
                layer_name=display_name,
                is_active=False,
                win_rate=summary.win_rate,
                sharpe_ratio=summary.sharpe_ratio,
                profit_factor=summary.profit_factor,
                net_pnl=summary.net_pnl,
                delta_sharpe=delta_sharpe,
                delta_win_rate=delta_wr,
                delta_pnl=delta_pnl,
                edge_rating=rating
            ))

        return AblationReport(
            asset=asset,
            timeframe=timeframe,
            baseline_win_rate=base_wr,
            baseline_sharpe=base_sharpe,
            baseline_pnl=base_pnl,
            layers=layers_results
        )
