"""
tests/test_phase33_outcome.py
Phase 33 — OutcomeEngine tests.
"""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from app.execution.outcome_engine import (
    OutcomeEngine,
    OUTCOME_TP_HIT, OUTCOME_SL_HIT, OUTCOME_TIME_EXIT,
    OUTCOME_AMBIGUOUS, OUTCOME_UNRESOLVED, OUTCOME_EXPIRED,
)


def _utc(*args) -> datetime:
    return datetime(*args, tzinfo=timezone.utc)


def _make_candle(ts: datetime, high: float, low: float, close: float) -> dict:
    return {
        "timestamp": ts.isoformat(),
        "open": (high + low) / 2,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1000,
    }


class TestOutcomeEngine:
    engine = OutcomeEngine()

    def _signal_active_window(self):
        """Signal generated in the past, already expired."""
        now = datetime.now(timezone.utc)
        signal_time = now - timedelta(hours=8)
        expiry_time = now - timedelta(hours=1)
        return signal_time, expiry_time

    @pytest.mark.asyncio
    async def test_tp_hit(self):
        signal_time, expiry_time = self._signal_active_window()
        candle_time = signal_time + timedelta(hours=2)
        # SL=95.0 is well below candle low (99.0) — only TP (101.0) is touched
        candles = [_make_candle(candle_time, high=102.0, low=99.0, close=101.0)]

        with patch(
            "app.execution.outcome_engine.market_service.get_rates",
            new_callable=AsyncMock,
            return_value=candles,
        ):
            result = await self.engine.resolve(
                symbol="BTCUSD",
                timeframe="H4",
                direction="BUY",
                entry_price=100.0,
                stop_loss=95.0,   # far below candle low
                take_profit=101.0,
                signal_time=signal_time,
                expiry_time=expiry_time,
            )
        assert result.outcome == OUTCOME_TP_HIT
        assert result.exit_price == 101.0
        assert result.gross_pnl is not None

    @pytest.mark.asyncio
    async def test_sl_hit(self):
        signal_time, expiry_time = self._signal_active_window()
        candle_time = signal_time + timedelta(hours=1)
        candles = [_make_candle(candle_time, high=100.5, low=97.5, close=98.0)]

        with patch(
            "app.execution.outcome_engine.market_service.get_rates",
            new_callable=AsyncMock,
            return_value=candles,
        ):
            result = await self.engine.resolve(
                symbol="BTCUSD",
                timeframe="H4",
                direction="BUY",
                entry_price=100.0,
                stop_loss=98.0,
                take_profit=104.0,
                signal_time=signal_time,
                expiry_time=expiry_time,
            )
        assert result.outcome == OUTCOME_SL_HIT
        assert result.exit_price == 98.0
        assert result.net_pnl is not None

    @pytest.mark.asyncio
    async def test_ambiguous_same_candle(self):
        """Both TP and SL appear inside the same candle → AMBIGUOUS."""
        signal_time, expiry_time = self._signal_active_window()
        candle_time = signal_time + timedelta(hours=1)
        # Very wide candle covers both TP (101) and SL (98)
        candles = [_make_candle(candle_time, high=102.0, low=97.0, close=100.0)]

        with patch(
            "app.execution.outcome_engine.market_service.get_rates",
            new_callable=AsyncMock,
            return_value=candles,
        ):
            result = await self.engine.resolve(
                symbol="BTCUSD",
                timeframe="H4",
                direction="BUY",
                entry_price=100.0,
                stop_loss=98.0,
                take_profit=101.0,
                signal_time=signal_time,
                expiry_time=expiry_time,
            )
        assert result.outcome == OUTCOME_AMBIGUOUS
        assert result.exit_price is None
        assert result.net_pnl is None

    @pytest.mark.asyncio
    async def test_time_exit(self):
        signal_time, expiry_time = self._signal_active_window()
        # Candle at expiry time
        candles = [_make_candle(expiry_time + timedelta(seconds=1), high=100.5, low=99.5, close=100.2)]

        with patch(
            "app.execution.outcome_engine.market_service.get_rates",
            new_callable=AsyncMock,
            return_value=candles,
        ):
            result = await self.engine.resolve(
                symbol="BTCUSD",
                timeframe="H4",
                direction="BUY",
                entry_price=100.0,
                stop_loss=95.0,
                take_profit=110.0,
                signal_time=signal_time,
                expiry_time=expiry_time,
            )
        assert result.outcome == OUTCOME_TIME_EXIT

    @pytest.mark.asyncio
    async def test_unresolved_when_not_expired(self):
        now = datetime.now(timezone.utc)
        future_expiry = now + timedelta(hours=2)
        result = await self.engine.resolve(
            symbol="BTCUSD",
            timeframe="H4",
            direction="BUY",
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
            signal_time=now - timedelta(hours=1),
            expiry_time=future_expiry,
        )
        assert result.outcome == OUTCOME_UNRESOLVED

    @pytest.mark.asyncio
    async def test_data_unavailable(self):
        signal_time, expiry_time = self._signal_active_window()
        with patch(
            "app.execution.outcome_engine.market_service.get_rates",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await self.engine.resolve(
                symbol="BTCUSD",
                timeframe="H4",
                direction="BUY",
                entry_price=100.0,
                stop_loss=95.0,
                take_profit=110.0,
                signal_time=signal_time,
                expiry_time=expiry_time,
            )
        assert result.outcome == OUTCOME_UNRESOLVED
        assert result.resolution_method == "DATA_UNAVAILABLE"

    def test_result_to_dict_complete(self):
        from app.execution.outcome_engine import OutcomeResult
        r = OutcomeResult(
            outcome=OUTCOME_TP_HIT,
            exit_price=101.0,
            exit_time=_utc(2026, 8, 19, 16, 0, 0),
            exit_time_ist="2026-08-19 21:30:00 IST",
            gross_pnl=1.0,
            spread_cost=0.2,
            slippage_cost=0.05,
            fees_cost=0.0,
            net_pnl=0.75,
            r_multiple=0.375,
            resolution_method="CANDLE_TP_BREACH",
            candles_evaluated=3,
        )
        d = r.to_dict()
        assert d["outcome"] == OUTCOME_TP_HIT
        assert d["net_pnl"] == 0.75
        assert d["r_multiple"] == 0.375
        assert "exit_time_ist" in d
