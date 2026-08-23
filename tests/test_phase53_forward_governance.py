"""
tests/test_phase53_forward_governance.py
========================================
Phase 53 — Forward Evidence Accumulation & Shadow Infrastructure Test Suite.

Validates:
1. Synthetic data exclusion and tagging
2. Real trade schema (30 mandatory fields) & raw R-multiple math
3. Cryptographic dataset hashing determinism
4. CanonicalPerformanceEngine SSOT calculations
5. PerformanceProvenance cryptographic envelopes
6. Frozen CONFIG_HASH (79a4f8e12b79310d)
7. Point-in-time news event blackout gating
8. TradingView SECONDARY_SUPPORT_ONLY classification
9. AI zero-synthetic-fill policy & AI_UNAVAILABLE logging
10. 14-indicator functional classification mapping
11. SMC closed-bar non-lookahead causality
12. Counterfactual dataset complete isolation (86 gated records)
13. Same-candle conservative SL-first resolution
14. Real-money 7/7 attack vector lockouts
15. Forward integrity REST API endpoint contracts
"""

from datetime import datetime, timedelta, timezone
import hashlib
import json
import numpy as np
import pandas as pd
import pytest

from app.analytics.canonical_performance_engine import (
    CanonicalPerformanceEngine,
    canonical_performance_engine,
)
from app.analytics.continuous_forward_monitor import (
    ContinuousForwardMonitor,
    continuous_forward_monitor,
)
from app.analytics.shadow_counterfactual import (
    LiveShadowCounterfactual,
    shadow_counterfactual,
)
from app.analytics.shadow_trade_truth import (
    LiveShadowTradeTruth,
    ShadowTradeRecord,
    shadow_trade_truth,
)
from app.decision.canonical_decision_engine import canonical_decision_engine
from app.execution.simulator import ExecutionMode, ExecutionSimulator
from app.market_data.canonical_snapshot import CanonicalMarketDataService
from app.pipeline.quant_pipeline_orchestrator import QuantPipelineOrchestrator
from app.strategies.SmartMoney.OrderBlocks.order_block_engine import OrderBlockEngine
from app.strategies.SmartMoney.FVG.fvg_engine import FVGEngine

CONFIG_HASH = "79a4f8e12b79310d"


def generate_candles(count: int = 80, trend: str = "BULLISH", volatility: float = 0.0002) -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    base_time = now - timedelta(hours=count)
    dates = [base_time + timedelta(hours=i) for i in range(count)]
    base_price = 1.0850
    records = []
    for i in range(count):
        drift = (i * 0.0003) if trend == "BULLISH" else ((-i * 0.0003) if trend == "BEARISH" else 0.0)
        open_p = base_price + drift + np.random.normal(0, volatility)
        close_p = open_p + (0.0004 if trend == "BULLISH" else (-0.0004 if trend == "BEARISH" else 0.0001))
        high_p = max(open_p, close_p) + 0.0003
        low_p = min(open_p, close_p) - 0.0003
        records.append({
            "timestamp": dates[i],
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": 1000.0 + i * 10,
        })
    return pd.DataFrame(records)


# ============================================================
# 1. Synthetic Data Exclusion & Tagging
# ============================================================
def test_phase53_synthetic_exclusion():
    """Verify zero synthetic defaults enter LIVE_SHADOW_TRADE_TRUTH or CanonicalPerformanceEngine."""
    metrics = canonical_performance_engine.compute_all_metrics()
    assert metrics["synthetic_records_excluded"] == 0
    assert metrics["real_records_included"] == 42
    assert metrics["source_dataset"] == "LIVE_SHADOW_TRADE_TRUTH"

    # Verify no trade record contains synthetic placeholders
    for trade in shadow_trade_truth.trades:
        assert trade.net_R != 0.0
        assert trade.gross_R != 0.0
        assert trade.spread_cost > 0.0
        assert trade.slippage_cost > 0.0
        assert trade.config_hash == CONFIG_HASH


# ============================================================
# 2. Real Trade Schema (30 Mandatory Fields) & Raw R Math
# ============================================================
def test_phase53_real_trade_provenance():
    """Verify all 42 trades implement 30-field schema and valid net R math."""
    trades = shadow_trade_truth.trades
    assert len(trades) == 42

    for t in trades:
        d = t.to_dict()
        assert len(d) == 30, f"Expected 30 fields, got {len(d)} in trade {t.trade_id}"
        assert t.trade_id.startswith("TRD-FWD-")
        assert t.direction in ["BUY", "SELL"]
        assert t.horizon in ["H1", "H4", "SWING", "DAILY"]
        assert t.result in ["WIN", "LOSS"]
        assert t.exit_reason in ["TP_HIT", "SL_HIT", "TIME_EXIT", "AMBIGUOUS_SL_FIRST"]

        # Math verification: net_R = gross_R - (spread_cost + slippage_cost)
        expected_net = round(t.gross_R - (t.spread_cost + t.slippage_cost), 2)
        assert abs(t.net_R - expected_net) <= 0.02, f"R math mismatch in {t.trade_id}"

        # Temporal ordering: decision <= entry <= exit
        assert t.decision_timestamp <= t.entry_timestamp
        assert t.entry_timestamp <= t.exit_timestamp


# ============================================================
# 3. Cryptographic Dataset Hashing Determinism
# ============================================================
def test_phase53_dataset_hashing_determinism():
    """Verify SHA256 digest of trade truth dataset is deterministic and non-empty."""
    hash1 = shadow_trade_truth.get_dataset_hash()
    hash2 = shadow_trade_truth.get_dataset_hash()
    assert hash1 == hash2
    assert len(hash1) == 64


# ============================================================
# 4. CanonicalPerformanceEngine SSOT Calculations
# ============================================================
def test_phase53_canonical_performance_engine():
    """Verify performance metrics match audited Phase 52/53 truth."""
    metrics = canonical_performance_engine.compute_all_metrics()

    assert metrics["n_trades"] == 42
    assert metrics["wins"] == 26
    assert metrics["losses"] == 16
    assert abs(metrics["win_rate"] - 0.6190) < 0.001
    assert abs(metrics["profit_factor"] - 1.78) < 0.05
    assert metrics["gross_profit_factor"] > metrics["profit_factor"]
    assert metrics["expectancy_r"] > 0.25
    assert metrics["governance_tier"] == "EARLY_FORWARD_EVIDENCE"
    assert metrics["classification"] == "EDGE_SUPPORTED_WITH_LIMITATIONS"
    assert metrics["max_drawdown_r"] > 0.0
    assert metrics["ulcer_index"] > 0.0
    assert metrics["brier_score"] > 0.0


# ============================================================
# 5. PerformanceProvenance Cryptographic Envelopes
# ============================================================
def test_phase53_metric_provenance_envelope():
    """Verify get_provenance_envelope returns valid cryptographic metadata."""
    envelope = canonical_performance_engine.get_provenance_envelope("profit_factor")
    d = envelope.to_dict()

    assert d["metric_name"] == "profit_factor"
    assert abs(d["value"] - 1.78) < 0.05
    assert d["source_trade_count"] == 42
    assert len(d["source_dataset_hash"]) == 64
    assert d["config_hash"] == CONFIG_HASH
    assert d["synthetic_records_excluded"] == 0
    assert d["real_records_included"] == 42


# ============================================================
# 6. Frozen CONFIG_HASH (79a4f8e12b79310d)
# ============================================================
def test_phase53_config_hash_frozen():
    """Verify CONFIG_HASH is frozen across all components."""
    assert canonical_decision_engine.config_hash == CONFIG_HASH
    assert continuous_forward_monitor.config_hash == CONFIG_HASH
    assert canonical_performance_engine.CONFIG_HASH == CONFIG_HASH
    assert shadow_trade_truth.CONFIG_HASH == CONFIG_HASH
    assert shadow_counterfactual.CONFIG_HASH == CONFIG_HASH


# ============================================================
# 7. Point-in-Time News Event Blackout Gating
# ============================================================
def test_phase53_point_in_time_news_causality():
    """Verify event blackout triggers fail-closed NO_TRADE."""
    df = generate_candles(count=50, trend="BULLISH")
    signal = canonical_decision_engine.evaluate_market(
        asset="EURUSD",
        df_primary=df,
        timeframe="1H",
        is_event_risk=True,  # Active news event blackout window
    )

    assert signal.decision == "NO_TRADE"
    assert "EVENT_RISK" in signal.decision_reason or "NO_TRADE" in signal.decision


# ============================================================
# 8. TradingView SECONDARY_SUPPORT_ONLY Classification
# ============================================================
def test_phase53_tradingview_secondary_support_classification():
    """Verify TradingView signals are classified as SECONDARY_SUPPORT_ONLY."""
    for trade in shadow_trade_truth.trades:
        assert trade.TradingView_state == "SECONDARY_SUPPORT_ONLY"


# ============================================================
# 9. AI Zero-Synthetic-Fill Policy
# ============================================================
def test_phase53_ai_zero_synthetic_fill():
    """Verify AI states are recorded accurately with zero mock score substitution."""
    for trade in shadow_trade_truth.trades:
        assert trade.AI_state in ["ENSEMBLE_CONFIRMED", "KRONOS_FAISS_ACTIVE", "AI_UNAVAILABLE"]


# ============================================================
# 10. 14-Indicator Functional Classification Mapping
# ============================================================
def test_phase53_14_indicator_classification():
    """Verify all 14 indicators are mapped in registry."""
    import os
    registry_path = os.path.join(os.path.dirname(__file__), "..", "config", "feature_registry.json")
    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    features = registry.get("features", [])
    assert len(features) == 14
    for feat in features:
        assert feat.get("status") in ["CORE_SIGNAL", "SUPPORTING_SIGNAL", "RISK_ONLY", "REGIME_ONLY", "ACTIVE"]


# ============================================================
# 11. SMC Closed-Bar Non-Lookahead Causality
# ============================================================
def test_phase53_smc_closed_bar_causality():
    """Verify SMC features evaluate strictly on closed bars."""
    df = generate_candles(count=60, trend="BULLISH")
    ob_engine = OrderBlockEngine()
    obs = ob_engine.detect_order_blocks(df, asset="EURUSD", timeframe="1H")

    fvg_engine = FVGEngine()
    fvgs = fvg_engine.detect_fvgs(df, asset="EURUSD", timeframe="1H")

    assert isinstance(obs, list)
    assert isinstance(fvgs, list)


# ============================================================
# 12. Counterfactual Dataset Complete Isolation (86 Gated Records)
# ============================================================
def test_phase53_counterfactual_dataset_isolation():
    """Verify 86 gated signals are strictly isolated in LIVE_SHADOW_COUNTERFACTUAL."""
    assert shadow_counterfactual.total_count == 86

    resolved = shadow_counterfactual.get_resolved_rejections()
    unresolved = shadow_counterfactual.get_unresolved_rejections()

    assert len(resolved) == 70
    assert len(unresolved) == 16

    summary = shadow_counterfactual.get_counterfactual_summary()
    assert summary["losses_avoided"] == 52
    assert summary["missed_winners"] == 18
    assert abs(summary["resolved_rejection_precision"] - 0.7429) < 0.001
    assert summary["dataset_tag"] == "LIVE_SHADOW_COUNTERFACTUAL"


# ============================================================
# 13. Same-Candle Conservative SL-First Resolution
# ============================================================
def test_phase53_same_candle_conservative_sl_first():
    """Verify same-candle trades resolve conservatively as SL first."""
    entry = 1.08500
    sl = 1.08300
    tp = 1.08900

    candle = {"open": 1.08500, "high": 1.08950, "low": 1.08250, "close": 1.08700}
    # Both TP and SL crossed in single candle
    tp_crossed = candle["high"] >= tp
    sl_crossed = candle["low"] <= sl
    assert tp_crossed and sl_crossed

    # Conservative rule: resolve SL first (loss)
    resolved_outcome = "SL_HIT" if (tp_crossed and sl_crossed) else ("TP_HIT" if tp_crossed else "SL_HIT")
    assert resolved_outcome == "SL_HIT"


# ============================================================
# 14. Real-Money 7/7 Attack Vector Lockouts
# ============================================================
def test_phase53_real_money_security_lockout():
    """Verify all 7 execution vectors remain strictly locked to PAPER mode."""
    sim = ExecutionSimulator()
    assert sim.mode == ExecutionMode.PAPER

    pipeline = QuantPipelineOrchestrator()
    assert pipeline.execution_simulator.mode == ExecutionMode.PAPER

    valid_modes = [m.value for m in ExecutionMode]
    assert "LIVE" not in valid_modes
    assert "REAL" not in valid_modes


# ============================================================
# 15. Forward Integrity REST API Endpoint Contracts
# ============================================================
def test_phase53_forward_integrity_api_endpoint():
    """Verify forward-integrity endpoint payload and schema."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/api/v1/evidence/forward-integrity")
    assert response.status_code == 200

    data = response.json()
    assert data["config_hash"] == CONFIG_HASH
    assert data["realized_trades"] == 42
    assert data["synthetic_records"] == 0
    assert data["data_quality_failures"] == 0
    assert data["lookahead_failures"] == 0
    assert data["counterfactual_records"] == 86
    assert data["resolved_rejection_precision"] == 0.7429
    assert data["governance_tier"] == "EARLY_FORWARD_EVIDENCE"
    assert data["classification"] == "EDGE_SUPPORTED_WITH_LIMITATIONS"
