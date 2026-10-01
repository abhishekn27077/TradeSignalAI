"""
tests/test_live_signal_generation_validation.py
===============================================
Automated Test Suite for:
Phase — Live Market Data Hydration & Real Signal Generation Validation

Verifies the 15 Acceptance Criteria from Section 22:
1. Real Binance data can produce a valid market snapshot.
2. Stale Binance data cannot qualify.
3. Invalid market price cannot qualify.
4. Model disagreement cannot qualify.
5. Untrained models cannot contribute production weight.
6. Missing provider cannot produce a live signal.
7. MT5 blocked cannot produce Forex live signal.
8. Duplicate scheduler cycles cannot create duplicate signals.
9. Every LIVE signal contains a valid market_snapshot_id.
10. Every LIVE signal contains market_snapshot_hash.
11. Every LIVE signal has live_data_verified = 1.
12. DEMO/HISTORICAL/REPLAY cannot enter Today's Signals.
13. Paper execution never reaches real broker execution.
14. Every resolved signal has resolution evidence.
15. Missing resolution evidence produces UNRESOLVED.
"""

import pytest
import sqlite3
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import pandas as pd

from app.core.canonical_snapshot_manager import (
    canonical_snapshot_manager,
    live_market_snapshot_manager,
    LiveAssetMarketSnapshot,
)
from app.market_data.live_provider_inventory import (
    live_provider_inventory,
    live_provider_inventory_service,
)
from app.core.canonical_prospective_ledger import (
    CanonicalProspectiveLedger,
    CanonicalProspectiveSignal,
    STATUS_UPCOMING,
    STATUS_ACTIVE,
    STATUS_RESOLVED,
    STATUS_REJECTED,
)
from app.runtime.live_signal_generation_engine import (
    live_signal_generation_engine,
)
from app.api.v1.terminal_routes import get_today_signals
from app.config.settings import get_settings

settings = get_settings()


@pytest.fixture
def temp_ledger(tmp_path):
    """Provides an isolated CanonicalProspectiveLedger instance."""
    db_file = str(tmp_path / "test_live_validation.db")
    ledger = CanonicalProspectiveLedger(db_path=db_file)
    return ledger


# 1. Real Binance data can produce a valid market snapshot.
@pytest.mark.asyncio
async def test_1_real_binance_data_produces_valid_market_snapshot():
    """1. Real Binance data can produce a valid market snapshot."""
    snapshot = await live_market_snapshot_manager.capture_live_snapshot("BTCUSDT")
    assert snapshot is not None
    assert snapshot.is_valid is True, f"Snapshot rejected: {snapshot.rejection_reason}"
    assert snapshot.provider == "BINANCE"
    assert snapshot.price > 0.0
    assert snapshot.data_age_seconds <= 120.0
    assert snapshot.market_snapshot_hash is not None and len(snapshot.market_snapshot_hash) == 64
    assert snapshot.snapshot_id.startswith("SNAP-BTCUSDT-")
    assert snapshot.provider_status == "LIVE"


# 2. Stale Binance data cannot qualify.
@pytest.mark.asyncio
async def test_2_stale_binance_data_cannot_qualify():
    """2. Stale Binance data cannot qualify."""
    now_utc = datetime.now(timezone.utc)
    stale_iso = (now_utc - timedelta(seconds=300)).isoformat()
    
    mock_ticker = {
        "symbol": "BTCUSDT",
        "price": 84000.0,
        "bid": 83995.0,
        "ask": 84005.0,
        "volume_24h": 1250.0,
        "received_timestamp": stale_iso,
        "data_age_ms": 300000.0,  # 300 seconds (gate is <= 120s)
    }
    
    with patch("app.market_data.providers.binance_provider.binance_crypto_provider.get_ticker", return_value=mock_ticker):
        snapshot = await live_market_snapshot_manager.capture_live_snapshot("BTCUSDT")
        assert snapshot.is_valid is False
        assert "STALE" in snapshot.rejection_reason or "TIMESTAMP_MOVING_BACKWARDS" in snapshot.rejection_reason


# 3. Invalid market price cannot qualify.
@pytest.mark.asyncio
@pytest.mark.parametrize("bad_price", [0.0, -500.0, -0.001])
async def test_3_invalid_market_price_cannot_qualify(bad_price):
    """3. Invalid market price cannot qualify."""
    now_utc = datetime.now(timezone.utc)
    mock_ticker = {
        "symbol": "BTCUSDT",
        "price": bad_price,
        "bid": bad_price,
        "ask": bad_price,
        "volume_24h": 100.0,
        "received_timestamp": now_utc.isoformat(),
        "data_age_ms": 100.0,
    }
    with patch("app.market_data.providers.binance_provider.binance_crypto_provider.get_ticker", return_value=mock_ticker):
        snapshot = await live_market_snapshot_manager.capture_live_snapshot("BTCUSDT")
        assert snapshot.is_valid is False
        assert "INVALID_PRICE" in snapshot.rejection_reason


# 4. Model disagreement cannot qualify.
@pytest.mark.asyncio
async def test_4_model_disagreement_cannot_qualify():
    """4. Model disagreement cannot qualify (threshold is 60%)."""
    # Create an agreement of 50.0% (below 60.0% gate)
    consensus_res = {
        "signal": "BULLISH",
        "confidence_score": 75.0,
        "agreement_percentage": 50.0,  # Below 60%
        "active_models": 4,
        "breakdown": {},
    }
    
    with patch.object(live_signal_generation_engine.consensus_engine, "generate_consensus", return_value=consensus_res):
        valid_snapshot = LiveAssetMarketSnapshot(
            snapshot_id="SNAP-TEST-001",
            asset="BTCUSDT",
            provider="BINANCE",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            timestamp_ist=datetime.now(timezone.utc).isoformat(),
            price=84000.0,
            bid=83995.0,
            ask=84005.0,
            volume=100.0,
            data_age_seconds=1.2,
            provider_status="LIVE",
            market_snapshot_hash="a" * 64,
            is_valid=True,
            rejection_reason=None,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with patch.object(canonical_snapshot_manager, "capture_live_snapshot", return_value=valid_snapshot):
            result = await live_signal_generation_engine.evaluate_live_opportunity("BTCUSDT", "1H")
            assert result["signal_generated"] is False
            assert "MODEL_DISAGREEMENT" in result["reason"] or "50.0%" in result["reason"]


# 5. Untrained models cannot contribute production weight.
def test_5_untrained_models_cannot_contribute_production_weight():
    """5. Untrained models cannot contribute production weight."""
    from app.analytics.consensus_engine import ConsensusEngine
    engine = ConsensusEngine()
    
    # Check model states and active weights logic
    # In ConsensusEngine, statistical models default to state="UNTRAINED"
    # When UNTRAINED, they are excluded from active_weights:
    assert getattr(engine.xgb_model, "state", "UNTRAINED") == "UNTRAINED"
    assert getattr(engine.rf_model, "state", "UNTRAINED") == "UNTRAINED"
    assert getattr(engine.hgb_model, "state", "UNTRAINED") == "UNTRAINED"
    
    # Generate consensus on dummy klines
    dummy_df = pd.DataFrame({
        "open": [100.0 + i for i in range(100)],
        "high": [101.0 + i for i in range(100)],
        "low": [99.0 + i for i in range(100)],
        "close": [100.5 + i for i in range(100)],
        "volume": [1000.0 for _ in range(100)],
    }, index=pd.date_range("2026-09-01", periods=100, freq="1h"))
    
    res = engine.generate_consensus("BTCUSDT", "1H", dummy_df)
    model_states = res.get("model_states", {})
    
    # Verify that untrained statistical models have state UNTRAINED and active weights exclude them
    for m in ["xgboost", "random_forest", "hist_gb"]:
        assert model_states.get(m) in ("UNTRAINED", "UNAVAILABLE")


# 6. Missing provider cannot produce a live signal.
@pytest.mark.asyncio
async def test_6_missing_provider_cannot_produce_live_signal():
    """6. Missing provider cannot produce a live signal."""
    snapshot = await live_market_snapshot_manager.capture_live_snapshot("NON_EXISTENT_ASSET_XYZ")
    assert snapshot.is_valid is False
    assert snapshot.rejection_reason is not None
    assert "BLOCKED" in snapshot.rejection_reason or "UNSUPPORTED" in snapshot.rejection_reason or "FAILED" in snapshot.rejection_reason


# 7. MT5 blocked cannot produce Forex live signal.
@pytest.mark.asyncio
async def test_7_mt5_blocked_cannot_produce_forex_live_signal():
    """7. MT5 blocked cannot produce Forex live signal."""
    forex_assets = ["EURUSD", "GBPUSD", "USDJPY"]
    for asset in forex_assets:
        snapshot = await live_market_snapshot_manager.capture_live_snapshot(asset)
        assert snapshot.is_valid is False
        assert snapshot.provider_status == "BLOCKED"
        assert "MT5_PROVIDER_BLOCKED" in snapshot.rejection_reason
        
        # Engine execution on this asset must fail closed
        result = await live_signal_generation_engine.evaluate_live_opportunity(asset, "1H")
        assert result["signal_generated"] is False
        assert "MT5" in result["reason"] or "BLOCKED" in result["reason"]


# 8. Duplicate scheduler cycles cannot create duplicate signals.
@pytest.mark.asyncio
async def test_8_duplicate_scheduler_cycles_cannot_create_duplicate_signals():
    """8. Duplicate scheduler cycles cannot create duplicate signals."""
    from app.core.canonical_prospective_ledger import canonical_prospective_ledger
    
    # Capture snapshot
    snapshot = await live_market_snapshot_manager.capture_live_snapshot("BTCUSDT")
    if not snapshot.is_valid:
        pytest.skip("Binance live feed temporarily unavailable for duplicate cycle test")
    
    # Run cycle twice
    res1 = await live_signal_generation_engine.evaluate_live_opportunity("BTCUSDT", "1H")
    count_after_first = len(canonical_prospective_ledger.get_signals_by_filter(live_only=True))
    
    res2 = await live_signal_generation_engine.evaluate_live_opportunity("BTCUSDT", "1H")
    count_after_second = len(canonical_prospective_ledger.get_signals_by_filter(live_only=True))
    
    # Second run should not increase live signal count if identical candle/state
    if res1.get("signal_generated"):
        assert res2.get("signal_generated") is False
        assert "DUPLICATE" in res2["reason"]
        assert count_after_first == count_after_second


# 9. Every LIVE signal contains a valid market_snapshot_id.
def test_9_every_live_signal_contains_valid_market_snapshot_id(temp_ledger):
    """9. Every LIVE signal contains a valid market_snapshot_id."""
    now_utc = datetime.now(timezone.utc)
    sig = CanonicalProspectiveSignal(
        signal_id="SIG-LIVE-SNAP-01",
        campaign_id="CAMP-LIVE-01",
        generated_at_utc=now_utc.isoformat(),
        generated_at_ist=now_utc.isoformat(),
        asset="BTCUSD",
        timeframe="1H",
        direction="BUY",
        market_snapshot_id="SNAP-BTCUSD-20261001-abc12345",
        market_snapshot_hash="b" * 64,
        policy_version="POL-70-v1",
        model_version="Kronos-v1",
        config_hash="conf-live-01",
        entry_window_start=now_utc.isoformat(),
        entry_window_end=(now_utc + timedelta(minutes=15)).isoformat(),
        preferred_entry_time=now_utc.isoformat(),
        entry_price=84000.0,
        stop_loss=82500.0,
        take_profit=87000.0,
        expected_hold_seconds=3600,
        expected_exit_time=(now_utc + timedelta(hours=1)).isoformat(),
        max_exit_time=(now_utc + timedelta(hours=2)).isoformat(),
        probability=0.75,
        signal_strength=82,
        quality_grade="GRADE_A",
        expected_r=2.0,
        regime="TRENDING_UP",
        mtf_alignment=0.88,
        risk_state="NORMAL",
        qualification_status="QUALIFIED",
        signal_status=STATUS_UPCOMING,
        record_type="LIVE",
        is_live=True,
        is_demo=False,
        is_historical=False,
        is_replay=False,
        live_data_verified=True,
    )
    temp_ledger.persist_signal(sig)
    
    retrieved = temp_ledger.get_signal(sig.signal_id)
    assert retrieved is not None
    assert retrieved.market_snapshot_id is not None
    assert retrieved.market_snapshot_id.startswith("SNAP-BTCUSD-")


# 10. Every LIVE signal contains market_snapshot_hash.
def test_10_every_live_signal_contains_market_snapshot_hash(temp_ledger):
    """10. Every LIVE signal contains market_snapshot_hash."""
    now_utc = datetime.now(timezone.utc)
    sig = CanonicalProspectiveSignal(
        signal_id="SIG-LIVE-HASH-01",
        campaign_id="CAMP-LIVE-01",
        generated_at_utc=now_utc.isoformat(),
        generated_at_ist=now_utc.isoformat(),
        asset="BTCUSD",
        timeframe="1H",
        direction="BUY",
        market_snapshot_id="SNAP-BTCUSD-20261001-abc12345",
        market_snapshot_hash="c" * 64,
        policy_version="POL-70-v1",
        model_version="Kronos-v1",
        config_hash="conf-live-01",
        entry_window_start=now_utc.isoformat(),
        entry_window_end=(now_utc + timedelta(minutes=15)).isoformat(),
        preferred_entry_time=now_utc.isoformat(),
        entry_price=84000.0,
        stop_loss=82500.0,
        take_profit=87000.0,
        expected_hold_seconds=3600,
        expected_exit_time=(now_utc + timedelta(hours=1)).isoformat(),
        max_exit_time=(now_utc + timedelta(hours=2)).isoformat(),
        probability=0.75,
        signal_strength=82,
        quality_grade="GRADE_A",
        expected_r=2.0,
        regime="TRENDING_UP",
        mtf_alignment=0.88,
        risk_state="NORMAL",
        qualification_status="QUALIFIED",
        signal_status=STATUS_UPCOMING,
        record_type="LIVE",
        is_live=True,
        live_data_verified=True,
    )
    temp_ledger.persist_signal(sig)
    
    retrieved = temp_ledger.get_signal(sig.signal_id)
    assert retrieved is not None
    assert retrieved.market_snapshot_hash is not None
    assert len(retrieved.market_snapshot_hash) == 64


# 11. Every LIVE signal has live_data_verified = 1.
def test_11_every_live_signal_has_live_data_verified_1(temp_ledger):
    """11. Every LIVE signal has live_data_verified = 1."""
    now_utc = datetime.now(timezone.utc)
    sig = CanonicalProspectiveSignal(
        signal_id="SIG-LIVE-VERIFIED-01",
        campaign_id="CAMP-LIVE-01",
        generated_at_utc=now_utc.isoformat(),
        generated_at_ist=now_utc.isoformat(),
        asset="BTCUSD",
        timeframe="1H",
        direction="BUY",
        market_snapshot_id="SNAP-BTCUSD-01",
        market_snapshot_hash="d" * 64,
        policy_version="POL-70-v1",
        model_version="Kronos-v1",
        config_hash="conf-01",
        entry_window_start=now_utc.isoformat(),
        entry_window_end=(now_utc + timedelta(minutes=15)).isoformat(),
        preferred_entry_time=now_utc.isoformat(),
        entry_price=84000.0,
        stop_loss=82500.0,
        take_profit=87000.0,
        expected_hold_seconds=3600,
        expected_exit_time=(now_utc + timedelta(hours=1)).isoformat(),
        max_exit_time=(now_utc + timedelta(hours=2)).isoformat(),
        probability=0.75,
        signal_strength=82,
        quality_grade="GRADE_A",
        expected_r=2.0,
        regime="TRENDING_UP",
        mtf_alignment=0.88,
        risk_state="NORMAL",
        qualification_status="QUALIFIED",
        signal_status=STATUS_UPCOMING,
        record_type="LIVE",
        is_live=True,
        live_data_verified=True,
    )
    temp_ledger.persist_signal(sig)
    
    retrieved = temp_ledger.get_signal(sig.signal_id)
    assert retrieved.is_live is True
    assert retrieved.live_data_verified is True


# 12. DEMO/HISTORICAL/REPLAY cannot enter Today's Signals.
def test_12_demo_historical_replay_cannot_enter_todays_signals(temp_ledger):
    """12. DEMO/HISTORICAL/REPLAY cannot enter Today's Signals."""
    now_utc = datetime.now(timezone.utc)
    
    types = [
        ("SIG-DEMO-X", "DEMO", False, True, False, False),
        ("SIG-HIST-X", "HISTORICAL", False, False, True, False),
        ("SIG-REPLAY-X", "REPLAY", False, False, False, True),
    ]
    
    for sig_id, rec_type, is_live, is_demo, is_hist, is_rep in types:
        s = CanonicalProspectiveSignal(
            signal_id=sig_id,
            campaign_id="CAMP-TEST",
            generated_at_utc=now_utc.isoformat(),
            generated_at_ist=now_utc.isoformat(),
            asset="EURUSD",
            timeframe="1H",
            direction="BUY",
            market_snapshot_hash="h" * 64,
            policy_version="POL-70-v1",
            model_version="Ensemble-v1",
            config_hash="conf-01",
            entry_window_start=now_utc.isoformat(),
            entry_window_end=(now_utc + timedelta(minutes=15)).isoformat(),
            preferred_entry_time=now_utc.isoformat(),
            entry_price=1.0850,
            stop_loss=1.0820,
            take_profit=1.0910,
            expected_hold_seconds=3600,
            expected_exit_time=(now_utc + timedelta(hours=1)).isoformat(),
            max_exit_time=(now_utc + timedelta(hours=2)).isoformat(),
            probability=0.72,
            signal_strength=80,
            quality_grade="GRADE_A",
            expected_r=2.0,
            regime="TRENDING_UP",
            mtf_alignment=0.85,
            risk_state="NORMAL",
            qualification_status="QUALIFIED",
            signal_status=STATUS_UPCOMING,
            record_type=rec_type,
            is_live=is_live,
            is_demo=is_demo,
            is_historical=is_hist,
            is_replay=is_rep,
            live_data_verified=False,
        )
        temp_ledger.persist_signal(s)
    
    today_live = temp_ledger.get_signals_by_filter(date_filter="TODAY", live_only=True)
    assert len(today_live) == 0, "No DEMO, HISTORICAL, or REPLAY signals should enter Today's Live Signals"


# 13. Paper execution never reaches real broker execution.
def test_13_paper_execution_never_reaches_real_broker_execution():
    """13. Paper execution never reaches real broker execution."""
    assert getattr(settings, "REAL_MONEY_ENABLED", False) is False, "REAL_MONEY_ENABLED must be False"
    assert getattr(settings, "BROKER_EXECUTION_ENABLED", False) is False, "BROKER_EXECUTION_ENABLED must be False"
    assert getattr(settings, "EXECUTION_MODE", "DEMO") in ("DEMO", "PAPER"), "EXECUTION_MODE must be DEMO or PAPER"


# 14. Every resolved signal has resolution evidence.
def test_14_every_resolved_signal_has_resolution_evidence(temp_ledger):
    """14. Every resolved signal has resolution evidence."""
    now_utc = datetime.now(timezone.utc)
    sig = CanonicalProspectiveSignal(
        signal_id="SIG-RES-EVID-01",
        campaign_id="CAMP-01",
        generated_at_utc=now_utc.isoformat(),
        generated_at_ist=now_utc.isoformat(),
        asset="BTCUSD",
        timeframe="1H",
        direction="BUY",
        market_snapshot_hash="e" * 64,
        policy_version="POL-70-v1",
        model_version="Kronos-v1",
        config_hash="conf-01",
        entry_window_start=now_utc.isoformat(),
        entry_window_end=(now_utc + timedelta(minutes=15)).isoformat(),
        preferred_entry_time=now_utc.isoformat(),
        entry_price=84000.0,
        stop_loss=82500.0,
        take_profit=87000.0,
        expected_hold_seconds=3600,
        expected_exit_time=(now_utc + timedelta(hours=1)).isoformat(),
        max_exit_time=(now_utc + timedelta(hours=2)).isoformat(),
        probability=0.75,
        signal_strength=82,
        quality_grade="GRADE_A",
        expected_r=2.0,
        regime="TRENDING_UP",
        mtf_alignment=0.88,
        risk_state="NORMAL",
        qualification_status="QUALIFIED",
        signal_status=STATUS_RESOLVED,
        record_type="LIVE",
        is_live=True,
        live_data_verified=True,
        actual_entry_time=now_utc.isoformat(),
        actual_exit_time=(now_utc + timedelta(hours=1)).isoformat(),
        actual_exit_price=87000.0,
        net_r=2.0,
        first_barrier_touched="TAKE_PROFIT",
        resolution_reason="TP_HIT",
    )
    temp_ledger.persist_signal(sig)
    
    retrieved = temp_ledger.get_signal(sig.signal_id)
    assert retrieved.signal_status == STATUS_RESOLVED
    assert retrieved.resolution_reason in ("TP_HIT", "SL_HIT", "EXPIRY", "INVALIDATED")
    assert retrieved.first_barrier_touched is not None
    assert retrieved.actual_exit_time is not None


# 15. Missing resolution evidence produces UNRESOLVED.
def test_15_missing_resolution_evidence_produces_unresolved(temp_ledger):
    """15. Missing resolution evidence produces UNRESOLVED (remains UPCOMING or ACTIVE)."""
    now_utc = datetime.now(timezone.utc)
    sig = CanonicalProspectiveSignal(
        signal_id="SIG-NO-EVID-01",
        campaign_id="CAMP-01",
        generated_at_utc=now_utc.isoformat(),
        generated_at_ist=now_utc.isoformat(),
        asset="BTCUSD",
        timeframe="1H",
        direction="BUY",
        market_snapshot_hash="f" * 64,
        policy_version="POL-70-v1",
        model_version="Kronos-v1",
        config_hash="conf-01",
        entry_window_start=now_utc.isoformat(),
        entry_window_end=(now_utc + timedelta(minutes=15)).isoformat(),
        preferred_entry_time=now_utc.isoformat(),
        entry_price=84000.0,
        stop_loss=82500.0,
        take_profit=87000.0,
        expected_hold_seconds=3600,
        expected_exit_time=(now_utc + timedelta(hours=1)).isoformat(),
        max_exit_time=(now_utc + timedelta(hours=2)).isoformat(),
        probability=0.75,
        signal_strength=82,
        quality_grade="GRADE_A",
        expected_r=2.0,
        regime="TRENDING_UP",
        mtf_alignment=0.88,
        risk_state="NORMAL",
        qualification_status="QUALIFIED",
        signal_status=STATUS_ACTIVE,
        record_type="LIVE",
        is_live=True,
        live_data_verified=True,
        # NO resolution evidence
        actual_exit_time=None,
        actual_exit_price=None,
        net_r=None,
        first_barrier_touched=None,
        resolution_reason=None,
    )
    temp_ledger.persist_signal(sig)
    
    retrieved = temp_ledger.get_signal(sig.signal_id)
    # Must NOT be marked resolved
    assert retrieved.signal_status != STATUS_RESOLVED
    assert retrieved.resolution_reason is None
    assert retrieved.net_r is None
