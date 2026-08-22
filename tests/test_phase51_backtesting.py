import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.strategies.Backtesting.engine import RealisticBacktestEngine, TradeOutcome
from app.strategies.Backtesting.walk_forward import WalkForwardEngine
from app.strategies.Backtesting.ablation import AblationEngine
from app.strategies.Backtesting.monte_carlo import MonteCarloEngine
from app.strategies.Structure.models import Direction


@pytest.fixture
def backtest_dataset():
    n = 100
    dates = [datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc) + timedelta(hours=i) for i in range(n)]
    prices = [100.0 + i * 0.4 for i in range(n)]

    df = pd.DataFrame({
        'timestamp': dates,
        'open': [p - 0.2 for p in prices],
        'high': [p + 1.0 for p in prices],
        'low': [p - 0.5 for p in prices],
        'close': prices,
        'volume': [1000] * n
    })

    signals = [
        {"candle_index": 10, "direction": Direction.BULLISH, "stop_loss": 102.0, "take_profit": 108.0},
        {"candle_index": 30, "direction": Direction.BULLISH, "stop_loss": 110.0, "take_profit": 116.0},
        {"candle_index": 50, "direction": Direction.BULLISH, "stop_loss": 118.0, "take_profit": 124.0},
        {"candle_index": 70, "direction": Direction.BULLISH, "stop_loss": 126.0, "take_profit": 132.0},
    ]

    return df, signals


def test_realistic_backtest_engine(backtest_dataset):
    df, signals = backtest_dataset
    engine = RealisticBacktestEngine(spread_pips=1.0, slippage_pips=0.5, commission_per_lot=5.0)
    summary = engine.run_backtest(df, signals, asset="EURUSD", timeframe="1H")

    assert summary.total_trades == len(signals)
    assert summary.total_frictions > 0.0
    assert summary.net_pnl != summary.gross_pnl  # Frictions properly accounted for
    assert 0.0 <= summary.win_rate <= 100.0


def test_walk_forward_engine(backtest_dataset):
    df, signals = backtest_dataset
    wf_engine = WalkForwardEngine(n_windows=2)
    report = wf_engine.run_walk_forward(df, signals, asset="EURUSD", timeframe="1H")

    assert report.total_windows > 0
    assert report.overall_wfe >= 0.0


def test_monte_carlo_engine(backtest_dataset):
    df, signals = backtest_dataset
    engine = RealisticBacktestEngine()
    summary = engine.run_backtest(df, signals, asset="EURUSD", timeframe="1H")

    mc_engine = MonteCarloEngine(iterations=100)
    mc_report = mc_engine.run_simulation(summary.trades, asset="EURUSD", timeframe="1H")

    assert mc_report.iterations == 100
    assert mc_report.median_max_drawdown_pct >= 0.0
    assert len(mc_report.pnl_confidence_interval_95) == 2
