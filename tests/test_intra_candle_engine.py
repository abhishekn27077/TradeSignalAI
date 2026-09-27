"""
tests/test_intra_candle_engine.py
=================================
Test Suite for Intra-Candle Sub-Bar Reconstruction Engine.

Benchmarked against Freqtrade's detail timeframe and LEAN slice-based consolidators.
"""

import pytest
import pandas as pd
import numpy as np

from app.backtesting.intra_candle_engine import (
    IntraCandleReconstructionEngine,
    ExecutionFeeTier,
    IntraCandleExecutionResult,
)


class TestIntraCandleEngine:
    def setup_method(self):
        self.engine = IntraCandleReconstructionEngine(
            default_fee_tier=ExecutionFeeTier(maker_fee_bps=2.0, taker_fee_bps=5.0, slippage_bps=3.0)
        )

    def test_chronological_tp_hit_first(self):
        """
        Verify that when 1m sub-bars cross TP before SL, outcome is strictly WON (TP_HIT).
        """
        # Create 20 sub-bars where TP (105.0) is hit at bar 5, and price later drops to SL (95.0) at bar 15
        sub_bars = []
        for i in range(20):
            if i < 5:
                # Hovering around 100
                sub_bars.append({"open": 100.0, "high": 102.0, "low": 99.0, "close": 101.0, "timestamp": f"10:{i:02d}"})
            elif i == 5:
                # Hits TP at 105.5
                sub_bars.append({"open": 101.0, "high": 105.5, "low": 100.5, "close": 105.0, "timestamp": "10:05"})
            elif i < 15:
                sub_bars.append({"open": 105.0, "high": 106.0, "low": 104.0, "close": 104.5, "timestamp": f"10:{i:02d}"})
            else:
                # Later drops to SL (94.0)
                sub_bars.append({"open": 104.0, "high": 104.5, "low": 94.0, "close": 94.5, "timestamp": f"10:{i:02d}"})

        df_sub = pd.DataFrame(sub_bars)

        res = self.engine.resolve_trade_path(
            direction="BUY",
            target_entry=100.0,
            stop_loss=95.0,
            take_profit=105.0,
            sub_bars=df_sub,
        )

        assert res.outcome == "WON"
        assert res.exit_reason == "TP_HIT"
        assert res.exit_sub_bar_index == 5
        assert res.exit_sub_bar_time == "10:05"
        assert res.net_pnl > 0.0
        assert res.gross_r > 0.0
        assert res.total_fees_paid > 0.0

    def test_chronological_sl_hit_first(self):
        """
        Verify that when 1m sub-bars cross SL before TP, outcome is strictly LOST (SL_HIT).
        """
        sub_bars = []
        for i in range(20):
            if i < 3:
                sub_bars.append({"open": 100.0, "high": 101.0, "low": 99.0, "close": 99.5, "timestamp": f"10:{i:02d}"})
            elif i == 3:
                # Drops to 94.0, hitting SL (95.0)
                sub_bars.append({"open": 99.5, "high": 99.5, "low": 94.0, "close": 94.5, "timestamp": "10:03"})
            else:
                # Later would have rallied to 110.0
                sub_bars.append({"open": 95.0, "high": 110.0, "low": 94.5, "close": 109.0, "timestamp": f"10:{i:02d}"})

        df_sub = pd.DataFrame(sub_bars)

        res = self.engine.resolve_trade_path(
            direction="BUY",
            target_entry=100.0,
            stop_loss=95.0,
            take_profit=105.0,
            sub_bars=df_sub,
        )

        assert res.outcome == "LOST"
        assert res.exit_reason == "SL_HIT"
        assert res.exit_sub_bar_index == 3
        assert res.exit_sub_bar_time == "10:03"
        assert res.net_pnl < 0.0
        assert res.net_r < 0.0

    def test_intra_bar_ambiguity_conservative_loss(self):
        """
        Verify that when BOTH SL and TP are touched inside the very same 1m sub-bar,
        it resolves conservatively as LOST (SL first).
        """
        # Single 1m bar with massive range covering both SL (95.0) and TP (105.0)
        df_sub = pd.DataFrame([{
            "open": 100.0,
            "high": 108.0,  # > TP
            "low": 92.0,    # < SL
            "close": 102.0,
            "timestamp": "10:00",
        }])

        res = self.engine.resolve_trade_path(
            direction="BUY",
            target_entry=100.0,
            stop_loss=95.0,
            take_profit=105.0,
            sub_bars=df_sub,
        )

        assert res.outcome == "LOST"
        assert "AMBIGUITY" in res.exit_reason
        assert res.exit_sub_bar_index == 0

    def test_time_expiry_exit(self):
        """
        Verify that when neither SL nor TP is reached during the sub-bar window,
        outcome resolves as TIME_EXIT at the final close price.
        """
        df_sub = pd.DataFrame([
            {"open": 100.0, "high": 102.0, "low": 98.0, "close": 101.5, "timestamp": f"10:{i:02d}"}
            for i in range(10)
        ])

        res = self.engine.resolve_trade_path(
            direction="BUY",
            target_entry=100.0,
            stop_loss=95.0,
            take_profit=105.0,
            sub_bars=df_sub,
        )

        assert res.outcome == "TIME_EXIT"
        assert res.exit_reason == "TIME_EXPIRY"
        assert res.exit_sub_bar_index == 9
        assert res.exit_price == 101.5
