"""
tests/test_phase33_risk.py
Phase 33 — Risk Engine v2 tests.
"""
import pytest
import pandas as pd
import numpy as np

from app.strategies.risk_engine import RiskEngine, DECISION_TAKE_NOW, DECISION_WAIT, DECISION_NO_TRADE


def _make_df(close: float, atr: float, rsi: float) -> pd.DataFrame:
    return pd.DataFrame([{
        "close": close,
        "ATR_14": atr,
        "RSI_14": rsi,
        "high": close + atr,
        "low": close - atr,
    }])


def _make_consensus(signal: str) -> dict:
    return {
        "master_signal": signal,
        "consensus_expected_return": 0.01,
        "agreement_percentage": 70,
        "breakdown": {},
        "intelligence": {},
    }


class TestRiskEngineV2:
    engine = RiskEngine(min_risk_reward=1.5)

    def test_bullish_take_now(self):
        df = _make_df(close=100.0, atr=1.0, rsi=50.0)
        consensus = self.engine.calculate_setup(df, _make_consensus("BULLISH"))
        assert consensus["master_signal"] == DECISION_TAKE_NOW
        assert "setup" in consensus
        assert "risk_trace" in consensus
        assert consensus["risk_trace"]["decision"] == DECISION_TAKE_NOW

    def test_bearish_take_now(self):
        df = _make_df(close=100.0, atr=1.0, rsi=50.0)
        consensus = self.engine.calculate_setup(df, _make_consensus("BEARISH"))
        assert consensus["master_signal"] == DECISION_TAKE_NOW

    def test_bullish_rsi_overbought_returns_wait(self):
        df = _make_df(close=100.0, atr=1.0, rsi=75.0)
        consensus = self.engine.calculate_setup(df, _make_consensus("BULLISH"))
        assert consensus["master_signal"] == DECISION_WAIT
        assert consensus["risk_trace"]["wait_reason"] == "RSI_OVERBOUGHT"

    def test_bearish_rsi_oversold_returns_wait(self):
        df = _make_df(close=100.0, atr=1.0, rsi=25.0)
        consensus = self.engine.calculate_setup(df, _make_consensus("BEARISH"))
        assert consensus["master_signal"] == DECISION_WAIT
        assert consensus["risk_trace"]["wait_reason"] == "RSI_OVERSOLD"

    def test_poor_rr_returns_no_trade(self):
        # min_rr=1.5 but we'll set atr so that RR is < 1.5
        engine = RiskEngine(min_risk_reward=5.0)  # very high threshold
        df = _make_df(close=100.0, atr=1.0, rsi=50.0)
        consensus = engine.calculate_setup(df, _make_consensus("BULLISH"))
        assert consensus["master_signal"] == DECISION_NO_TRADE
        assert "POOR_RISK_REWARD" in consensus["risk_trace"]["reason"]

    def test_neutral_signal_returns_no_trade(self):
        consensus = self.engine.calculate_setup(
            _make_df(100.0, 1.0, 50.0), _make_consensus("NEUTRAL")
        )
        assert consensus["master_signal"] == "NEUTRAL"
        assert consensus["risk_trace"]["decision"] == DECISION_NO_TRADE

    def test_entry_zero_rejected(self):
        df = _make_df(close=0.0, atr=0.0, rsi=50.0)
        consensus = self.engine.calculate_setup(df, _make_consensus("BULLISH"))
        assert consensus["master_signal"] == DECISION_NO_TRADE
        assert consensus["risk_trace"]["validity"]["entry_valid"] is False

    def test_empty_df_rejected(self):
        consensus = self.engine.calculate_setup(pd.DataFrame(), _make_consensus("BULLISH"))
        assert consensus["master_signal"] == DECISION_NO_TRADE

    def test_setup_fields_complete(self):
        df = _make_df(close=100.0, atr=1.0, rsi=50.0)
        consensus = self.engine.calculate_setup(df, _make_consensus("BULLISH"))
        setup = consensus["setup"]
        assert "entry_price" in setup
        assert "stop_loss" in setup
        assert "take_profit" in setup
        assert "risk_reward_ratio" in setup
        assert "atr_at_entry" in setup
        assert "entry_zone" in setup
        assert "expected_move_pct" in setup
        assert "risk_percent" in setup

    def test_risk_trace_validity_all_true(self):
        df = _make_df(close=100.0, atr=1.0, rsi=50.0)
        consensus = self.engine.calculate_setup(df, _make_consensus("BULLISH"))
        v = consensus["risk_trace"]["validity"]
        assert v["entry_valid"] is True
        assert v["sl_valid"] is True
        assert v["tp_valid"] is True
        assert v["rr_valid"] is True

    def test_rr_is_exactly_2(self):
        # TP = entry + 3*ATR, SL = entry - 1.5*ATR → R:R = 3/1.5 = 2.0
        df = _make_df(close=100.0, atr=1.0, rsi=50.0)
        consensus = self.engine.calculate_setup(df, _make_consensus("BULLISH"))
        assert consensus["setup"]["risk_reward_ratio"] == pytest.approx(2.0, rel=0.01)

    def test_bearish_sl_above_entry(self):
        df = _make_df(close=100.0, atr=1.0, rsi=50.0)
        consensus = self.engine.calculate_setup(df, _make_consensus("BEARISH"))
        sl = consensus["setup"]["stop_loss"]
        entry = consensus["setup"]["entry_price"]
        assert sl > entry

    def test_bearish_tp_below_entry(self):
        df = _make_df(close=100.0, atr=1.0, rsi=50.0)
        consensus = self.engine.calculate_setup(df, _make_consensus("BEARISH"))
        tp = consensus["setup"]["take_profit"]
        entry = consensus["setup"]["entry_price"]
        assert tp < entry
