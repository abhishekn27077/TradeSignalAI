"""
tests/test_phase38_lifecycle_outcomes.py
Phase 38: Comprehensive automated test suite for real lifecycle outcome resolution.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from app.execution.outcome_engine import (
    OutcomeEngine,
    OutcomeResult,
    OUTCOME_TP_HIT,
    OUTCOME_SL_HIT,
    OUTCOME_TIME_EXIT,
    OUTCOME_EXPIRED,
    OUTCOME_AMBIGUOUS,
    OUTCOME_UNRESOLVED,
)


@pytest.fixture
def engine():
    return OutcomeEngine(
        spread_pips=2.0,
        slippage_pips=0.5,
        fees_per_lot=0.0,
        lot_size=0.01,
        pip_value=10.0,
    )


@pytest.mark.asyncio
async def test_outcome_tp_hit_buy(engine):
    """BUY trade where subsequent candle high breaches take profit."""
    signal_time = datetime(2026, 8, 20, 10, 0, 0, tzinfo=timezone.utc)
    expiry_time = datetime(2026, 8, 20, 18, 0, 0, tzinfo=timezone.utc)

    mock_rates = [
        # Candle before signal
        {"timestamp": "2026-08-20T06:00:00Z", "open": 68000.0, "high": 68200.0, "low": 67900.0, "close": 68100.0},
        # Candle after signal: touches TP (69000)
        {"timestamp": "2026-08-20T14:00:00Z", "open": 68150.0, "high": 69200.0, "low": 68000.0, "close": 69100.0},
    ]

    with patch("app.market_data.service.market_service.get_rates", AsyncMock(return_value=mock_rates)):
        res = await engine.resolve(
            symbol="BTCUSD",
            timeframe="H4",
            direction="BUY",
            entry_price=68100.0,
            stop_loss=67500.0,
            take_profit=69000.0,
            signal_time=signal_time,
            expiry_time=expiry_time,
        )

        assert res.outcome == OUTCOME_TP_HIT
        assert res.exit_price == 69000.0
        assert res.net_pnl is not None
        assert res.net_pnl > 0
        assert res.r_multiple is not None
        assert res.r_multiple > 1.0


@pytest.mark.asyncio
async def test_outcome_sl_hit_sell(engine):
    """SELL trade where subsequent candle high breaches stop loss."""
    signal_time = datetime(2026, 8, 20, 10, 0, 0, tzinfo=timezone.utc)
    expiry_time = datetime(2026, 8, 20, 18, 0, 0, tzinfo=timezone.utc)

    mock_rates = [
        {"timestamp": "2026-08-20T14:00:00Z", "open": 1.1000, "high": 1.1080, "low": 1.0990, "close": 1.1050},
    ]

    with patch("app.market_data.service.market_service.get_rates", AsyncMock(return_value=mock_rates)):
        res = await engine.resolve(
            symbol="EURUSD",
            timeframe="H4",
            direction="SELL",
            entry_price=1.1000,
            stop_loss=1.1050,
            take_profit=1.0900,
            signal_time=signal_time,
            expiry_time=expiry_time,
        )

        assert res.outcome == OUTCOME_SL_HIT
        assert res.exit_price == 1.1050
        assert res.net_pnl is not None
        assert res.net_pnl < 0


@pytest.mark.asyncio
async def test_outcome_ambiguous_same_candle(engine):
    """Both TP and SL are touched in the same candle bar -> AMBIGUOUS."""
    signal_time = datetime(2026, 8, 20, 10, 0, 0, tzinfo=timezone.utc)
    expiry_time = datetime(2026, 8, 20, 18, 0, 0, tzinfo=timezone.utc)

    # Wide range candle spanning both SL (67000) and TP (69000)
    mock_rates = [
        {"timestamp": "2026-08-20T14:00:00Z", "open": 68000.0, "high": 69500.0, "low": 66500.0, "close": 68000.0},
    ]

    with patch("app.market_data.service.market_service.get_rates", AsyncMock(return_value=mock_rates)):
        res = await engine.resolve(
            symbol="BTCUSD",
            timeframe="H4",
            direction="BUY",
            entry_price=68000.0,
            stop_loss=67000.0,
            take_profit=69000.0,
            signal_time=signal_time,
            expiry_time=expiry_time,
        )

        assert res.outcome == OUTCOME_AMBIGUOUS
        assert res.exit_price is None
        assert res.net_pnl is None
        assert res.resolution_method == "SAME_CANDLE_AMBIGUOUS"


@pytest.mark.asyncio
async def test_outcome_time_exit_at_expiry(engine):
    """Candle reaches expiry_time without hitting TP/SL -> TIME_EXIT at close."""
    signal_time = datetime(2026, 8, 20, 10, 0, 0, tzinfo=timezone.utc)
    expiry_time = datetime(2026, 8, 20, 14, 0, 0, tzinfo=timezone.utc)

    mock_rates = [
        {"timestamp": "2026-08-20T14:00:00Z", "open": 68000.0, "high": 68500.0, "low": 67800.0, "close": 68300.0},
    ]

    with patch("app.market_data.service.market_service.get_rates", AsyncMock(return_value=mock_rates)):
        res = await engine.resolve(
            symbol="BTCUSD",
            timeframe="H4",
            direction="BUY",
            entry_price=68000.0,
            stop_loss=67000.0,
            take_profit=70000.0,
            signal_time=signal_time,
            expiry_time=expiry_time,
        )

        assert res.outcome == OUTCOME_TIME_EXIT
        assert res.exit_price == 68300.0
        assert res.net_pnl is not None


@pytest.mark.asyncio
async def test_outcome_active_unresolved_before_expiry(engine):
    """Before expiry_time with no breach -> OUTCOME_UNRESOLVED."""
    signal_time = datetime.now(timezone.utc) - timedelta(hours=1)
    expiry_time = datetime.now(timezone.utc) + timedelta(hours=3)

    mock_rates = [
        {"timestamp": (signal_time + timedelta(minutes=30)).isoformat(), "open": 68000.0, "high": 68100.0, "low": 67950.0, "close": 68050.0},
    ]

    with patch("app.market_data.service.market_service.get_rates", AsyncMock(return_value=mock_rates)):
        res = await engine.resolve(
            symbol="BTCUSD",
            timeframe="H4",
            direction="BUY",
            entry_price=68000.0,
            stop_loss=67000.0,
            take_profit=70000.0,
            signal_time=signal_time,
            expiry_time=expiry_time,
        )

        assert res.outcome == OUTCOME_UNRESOLVED
        assert res.exit_price is None
        assert res.resolution_method == "ACTIVE_IN_PROGRESS"
