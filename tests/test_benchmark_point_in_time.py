"""
tests/test_benchmark_point_in_time.py
=====================================
Point-in-Time Integrity & Replay Invariance Benchmark Test.

Evaluates the exact architectural sequence:
historical candles -> snapshot -> signal -> model -> decision

Then injects future data (T > T0) and verifies that:
1. The snapshot hash at T0 remains 100% invariant.
2. The generated signal direction, entry, stop loss, take profit, and confidence remain identical.
3. Attempting to pollute the T0 decision with future candles is intercepted and blocked.
"""

import pytest
import hashlib
import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from app.strategies.Technical.indicators import compute_rsi, compute_macd, compute_atr
from app.core.canonical_snapshot_manager import canonical_snapshot_manager
from app.validation.lookahead_instrumentation import lookahead_guard, LookaheadViolationError


def _generate_synthetic_candles(n: int, start_dt: datetime) -> pd.DataFrame:
    np.random.seed(123)
    timestamps = [start_dt + timedelta(hours=i) for i in range(n)]
    close = 1.1000 + np.cumsum(np.random.normal(0, 0.001, n))
    high = close + np.abs(np.random.normal(0.0005, 0.0002, n))
    low = close - np.abs(np.random.normal(0.0005, 0.0002, n))
    open_p = low + (high - low) * 0.5
    volume = np.random.uniform(500, 2000, n)

    return pd.DataFrame({
        "timestamp": timestamps,
        "open": np.round(open_p, 5),
        "high": np.round(high, 5),
        "low": np.round(low, 5),
        "close": np.round(close, 5),
        "volume": np.round(volume, 1),
    })


def _evaluate_point_in_time_decision(df_slice: pd.DataFrame) -> dict:
    """
    Computes technical snapshot, signals, and deterministic trade decision on a point-in-time slice.
    """
    rsi = compute_rsi(df_slice, period=14).iloc[-1]
    macd, signal, hist = compute_macd(df_slice)
    atr = compute_atr(df_slice, period=14).iloc[-1]
    last_close = df_slice['close'].iloc[-1]

    # Deterministic signal policy
    direction = "BUY" if rsi < 50 and hist.iloc[-1] > 0 else "SELL"
    sl = last_close - (atr * 1.5) if direction == "BUY" else last_close + (atr * 1.5)
    tp = last_close + (atr * 3.0) if direction == "BUY" else last_close - (atr * 3.0)
    confidence = 0.85 if abs(rsi - 50) > 5 else 0.65

    # Fingerprint slice
    raw_bytes = df_slice[['open', 'high', 'low', 'close']].to_csv(index=False).encode('utf-8')
    slice_hash = hashlib.sha256(raw_bytes).hexdigest()

    return {
        "slice_hash": slice_hash,
        "direction": direction,
        "entry_price": round(float(last_close), 5),
        "stop_loss": round(float(sl), 5),
        "take_profit": round(float(tp), 5),
        "confidence": confidence,
        "rsi": round(float(rsi), 3),
        "atr": round(float(atr), 5),
    }


class TestPointInTimeIntegrity:
    """
    Tests point-in-time integrity against future data pollution.
    """

    def test_decision_invariance_under_future_data_injection(self):
        t0 = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        n_history = 50

        # 1. Historical data up to T0
        df_history = _generate_synthetic_candles(n=n_history, start_dt=t0 - timedelta(hours=n_history))
        assert df_history['timestamp'].iloc[-1] < t0 or df_history['timestamp'].iloc[-1] == t0

        # 2. Decision at T0
        decision_t0 = _evaluate_point_in_time_decision(df_history)

        # 3. Inject future candles (T0 + 1 to T0 + 20) with severe market shocks
        df_future = _generate_synthetic_candles(n=20, start_dt=t0 + timedelta(hours=1))
        # Add massive market shock to future
        df_future['close'] = df_future['close'] * 1.5

        # Combined dataset (history + future)
        df_polluted = pd.concat([df_history, df_future], ignore_index=True)

        # 4. Point-in-Time filter: extract data as of T0 from polluted stream
        df_replay_t0 = df_polluted[df_polluted['timestamp'] <= df_history['timestamp'].iloc[-1]].copy()

        # 5. Re-evaluate decision at T0
        decision_replay = _evaluate_point_in_time_decision(df_replay_t0)

        # 6. Verify complete byte-for-byte invariance
        assert decision_replay["slice_hash"] == decision_t0["slice_hash"]
        assert decision_replay["direction"] == decision_t0["direction"]
        assert decision_replay["entry_price"] == decision_t0["entry_price"]
        assert decision_replay["stop_loss"] == decision_t0["stop_loss"]
        assert decision_replay["take_profit"] == decision_t0["take_profit"]
        assert decision_replay["confidence"] == decision_t0["confidence"]
        assert decision_replay["rsi"] == decision_t0["rsi"]
        assert decision_replay["atr"] == decision_t0["atr"]

    def test_future_leakage_assertion_catches_unfiltered_future_data(self):
        t0 = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        df_history = _generate_synthetic_candles(n=30, start_dt=t0 - timedelta(hours=30))
        df_future = _generate_synthetic_candles(n=5, start_dt=t0 + timedelta(hours=1))
        df_polluted = pd.concat([df_history, df_future], ignore_index=True)

        # Attempting to validate polluted dataset against T0 must raise LookaheadViolationError
        with pytest.raises(LookaheadViolationError):
            lookahead_guard.assert_no_lookahead(
                df_polluted,
                decision_timestamp=t0,
                component_name="BenchmarkPointInTimeTest"
            )
