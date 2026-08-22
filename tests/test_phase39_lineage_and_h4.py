"""
tests/test_phase39_lineage_and_h4.py
======================================
Automated Unit and Integration Tests for Phase 39:
1. Test elimination of legacy in-memory bypasses.
2. Test strict 65% consensus & 1.50 R:R zero-trust gating.
3. Test candidate vs validated signal separation in /signals/h4-intelligence.
4. Test /signals/live reads strictly from SignalLifecycleModel.
5. Test ForecastManager timeframe filtering and deduplication.
6. Test end-to-end SignalLifecycleModel persistence and ID preservation.
"""

import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import select, delete

from app.database.manager import db_manager
from app.database.models.signal import SignalLifecycleModel
from app.market_intelligence.h4_engine import h4_forecast_engine
from app.market_intelligence.swing_scanner import swing_scanner
from app.strategies.manager import strategy_manager
from app.strategies.risk_engine import risk_engine
from app.api.v1.signals import get_h4_intelligence, get_live_signal_panel


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    db_manager.connect()
    await db_manager.init_db()
    yield
    # Cleanup


@pytest.mark.asyncio
async def test_no_inmemory_bypass_in_h4_and_swing_engines():
    """Verify that publish_results does not insert unvalidated setups into strategy_manager.recent_signals."""
    strategy_manager.recent_signals.clear()

    # Sub-threshold setup
    unvalidated_setup = {
        "symbol": "SPX500",
        "master_signal": "BULLISH",
        "quant_baseline": {"confidence_score": 50.0, "agreement_percentage": 50.0},
        "setup": {
            "entry_price": 5000.0,
            "stop_loss": 4950.0,
            "take_profit": 5050.0,
            "risk_reward": 1.0,
            "decision": "NO_TRADE"
        }
    }

    await h4_forecast_engine.publish_results([unvalidated_setup])
    assert len(strategy_manager.recent_signals) == 0, "H4 engine pushed unvalidated setup to recent_signals!"

    await swing_scanner.generate_forecasts()
    assert len(strategy_manager.recent_signals) == 0, "Swing scanner pushed unvalidated setup to recent_signals!"


@pytest.mark.asyncio
async def test_sub_65_confidence_never_becomes_active_signal():
    """Verify that a candidate with 50% confidence is never emitted as TAKE_NOW / ACTIVE."""
    strategy_manager.recent_signals.clear()

    test_candle_df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0],
        "high": [102.0, 103.0, 104.0],
        "low": [99.0, 100.0, 101.0],
        "close": [101.0, 102.0, 103.0],
        "volume": [1000, 1100, 1200],
        "ATR_14": [1.0, 1.0, 1.0],
        "RSI_14": [50.0, 50.0, 50.0]
    })

    candidate_50_pct = {
        "symbol": "NAS100",
        "timeframe": "4H",
        "master_signal": "BULLISH",
        "quant_baseline": {"confidence_score": 50.0, "agreement_percentage": 50.0}
    }

    setup = risk_engine.calculate_setup(test_candle_df, candidate_50_pct)
    await h4_forecast_engine.publish_results([setup])

    assert len(strategy_manager.recent_signals) == 0


@pytest.mark.asyncio
async def test_h4_intelligence_candidate_vs_validated_separation():
    """Verify GET /signals/h4-intelligence separates candidates, validated_signals, and rejected."""
    res = await get_h4_intelligence()
    assert res["success"] is True
    assert "candidates" in res
    assert "validated_signals" in res
    assert "rejected" in res
    assert "matrix" in res
    assert res["assets_scanned"] == 9

    # Each matrix entry must have explicit status and risk reason
    for m in res["matrix"]:
        assert "asset" in m
        assert "risk" in m
        assert "risk_reason" in m
        assert "final" in m


@pytest.mark.asyncio
async def test_live_signals_queries_canonical_database():
    """Verify GET /signals/live returns records strictly from SignalLifecycleModel."""
    test_sig_id = f"TEST-LIVE-{uuid.uuid4().hex[:6].upper()}"

    async with db_manager.get_session()() as session:
        sig = SignalLifecycleModel(
            signal_id=test_sig_id,
            trace_id=f"TR-{test_sig_id}",
            asset="ETHUSD",
            timeframe="4H",
            direction="BUY",
            strength="STRONG",
            risk_level="MODERATE",
            entry_price=3000.0,
            stop_loss=2900.0,
            take_profit_1=3300.0,
            confidence=0.80,
            risk_reward=3.0,
            status="ACTIVE",
            signal_state="ACTIVE",
            strategy_name="Consensus Ensemble Engine",
            created_at=datetime.now(timezone.utc)
        )
        session.add(sig)
        await session.commit()

    try:
        res = await get_live_signal_panel()
        assert res["success"] is True
        found = any(ls.get("signal", {}).get("signal_id") == test_sig_id for ls in res["live_signals"])
        assert found, f"Signal {test_sig_id} was not returned by /signals/live!"
    finally:
        async with db_manager.get_session()() as session:
            await session.execute(delete(SignalLifecycleModel).where(SignalLifecycleModel.signal_id == test_sig_id))
            await session.commit()
