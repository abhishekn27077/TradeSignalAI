import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Backtesting.engine import RealisticBacktestEngine, BacktestSummary


@dataclass
class WalkForwardWindow:
    window_id: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int
    train_trades: int
    train_sharpe: float
    train_win_rate: float
    test_trades: int
    test_sharpe: float
    test_win_rate: float
    wfe_ratio: float  # Walk Forward Efficiency = test_sharpe / max(0.01, train_sharpe)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "window_id": self.window_id,
            "train_start": self.train_start,
            "train_end": self.train_end,
            "test_start": self.test_start,
            "test_end": self.test_end,
            "train_trades": self.train_trades,
            "train_sharpe": round(float(self.train_sharpe), 2),
            "train_win_rate": round(float(self.train_win_rate), 2),
            "test_trades": self.test_trades,
            "test_sharpe": round(float(self.test_sharpe), 2),
            "test_win_rate": round(float(self.test_win_rate), 2),
            "wfe_ratio": round(float(self.wfe_ratio), 2),
        }


@dataclass
class WalkForwardReport:
    asset: str
    timeframe: str
    total_windows: int
    avg_in_sample_sharpe: float
    avg_out_of_sample_sharpe: float
    overall_wfe: float
    is_robust: bool
    windows: List[WalkForwardWindow] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "timeframe": self.timeframe,
            "total_windows": self.total_windows,
            "avg_in_sample_sharpe": round(float(self.avg_in_sample_sharpe), 2),
            "avg_out_of_sample_sharpe": round(float(self.avg_out_of_sample_sharpe), 2),
            "overall_wfe": round(float(self.overall_wfe), 2),
            "is_robust": self.is_robust,
            "windows": [w.to_dict() for w in self.windows]
        }


class WalkForwardEngine:
    """
    Rolling Out-of-Sample Walk-Forward Engine.
    Evaluates out-of-sample strategy persistence and Walk Forward Efficiency (WFE).
    """

    def __init__(self, n_windows: int = 4, train_ratio: float = 0.70):
        self.n_windows = n_windows
        self.train_ratio = train_ratio
        self.bt_engine = RealisticBacktestEngine()

    def run_walk_forward(
        self,
        df: pd.DataFrame,
        signals: List[Dict[str, Any]],
        asset: str = "UNKNOWN",
        timeframe: str = "1H"
    ) -> WalkForwardReport:
        if df is None or len(df) < 50 or not signals:
            return WalkForwardReport(
                asset=asset, timeframe=timeframe, total_windows=0,
                avg_in_sample_sharpe=0.0, avg_out_of_sample_sharpe=0.0,
                overall_wfe=0.0, is_robust=False
            )

        n = len(df)
        window_size = n // self.n_windows
        windows: List[WalkForwardWindow] = []

        is_sharpes: List[float] = []
        oos_sharpes: List[float] = []

        for w in range(self.n_windows):
            w_start = w * (window_size // 2)
            w_end = min(n, w_start + window_size)
            if (w_end - w_start) < 20:
                continue

            split_pt = w_start + int((w_end - w_start) * self.train_ratio)

            train_df = df.iloc[w_start:split_pt].copy().reset_index(drop=True)
            test_df = df.iloc[split_pt:w_end].copy().reset_index(drop=True)

            train_sigs = [s for s in signals if w_start <= s.get("candle_index", 0) < split_pt]
            test_sigs = [s for s in signals if split_pt <= s.get("candle_index", 0) < w_end]

            # Adjust signal indices relative to sub-dataframes
            adj_train_sigs = [{**s, "candle_index": s["candle_index"] - w_start} for s in train_sigs]
            adj_test_sigs = [{**s, "candle_index": s["candle_index"] - split_pt} for s in test_sigs]

            train_summary = self.bt_engine.run_backtest(train_df, adj_train_sigs, asset=asset, timeframe=timeframe)
            test_summary = self.bt_engine.run_backtest(test_df, adj_test_sigs, asset=asset, timeframe=timeframe)

            wfe = test_summary.sharpe_ratio / max(0.1, train_summary.sharpe_ratio)
            is_sharpes.append(train_summary.sharpe_ratio)
            oos_sharpes.append(test_summary.sharpe_ratio)

            windows.append(WalkForwardWindow(
                window_id=w + 1,
                train_start=w_start,
                train_end=split_pt,
                test_start=split_pt,
                test_end=w_end,
                train_trades=train_summary.total_trades,
                train_sharpe=train_summary.sharpe_ratio,
                train_win_rate=train_summary.win_rate,
                test_trades=test_summary.total_trades,
                test_sharpe=test_summary.sharpe_ratio,
                test_win_rate=test_summary.win_rate,
                wfe_ratio=wfe
            ))

        avg_is = float(np.mean(is_sharpes)) if is_sharpes else 0.0
        avg_oos = float(np.mean(oos_sharpes)) if oos_sharpes else 0.0
        overall_wfe = avg_oos / max(0.1, avg_is)
        is_robust = overall_wfe >= 0.50 and avg_oos > 0.50

        return WalkForwardReport(
            asset=asset,
            timeframe=timeframe,
            total_windows=len(windows),
            avg_in_sample_sharpe=avg_is,
            avg_out_of_sample_sharpe=avg_oos,
            overall_wfe=overall_wfe,
            is_robust=is_robust,
            windows=windows
        )
