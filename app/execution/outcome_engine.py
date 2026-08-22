"""
app/execution/outcome_engine.py  — Phase 33
============================================
OutcomeEngine: resolves signal outcomes from subsequent real candles.

Zero-Trust Rules:
- ONLY uses real OHLCV data fetched after signal expiry
- If TP and SL both appear in the same candle → AMBIGUOUS
- Never assumes which intrabar move happened first
- PnL = net (gross - spread - slippage - fees)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.market_data.service import market_service
from typing import Any, Optional

from app.core.timing import ISTConverter
from app.logs.logger import get_logger

logger = get_logger(__name__)

# Standard spread/fee assumptions for paper trading
DEFAULT_SPREAD_PIPS    = 2.0    # pips
DEFAULT_SLIPPAGE_PIPS  = 0.5    # pips
DEFAULT_FEES_PER_LOT   = 0.0    # $ (spread-only model)
DEFAULT_LOT_SIZE       = 0.01   # lots
DEFAULT_PIP_VALUE      = 10.0   # $ per lot per pip (for FX majors)

OUTCOME_TP_HIT    = "TP_HIT"
OUTCOME_SL_HIT    = "SL_HIT"
OUTCOME_TIME_EXIT = "TIME_EXIT"
OUTCOME_EXPIRED   = "EXPIRED"
OUTCOME_AMBIGUOUS = "AMBIGUOUS"
OUTCOME_UNRESOLVED = "OUTCOME_UNRESOLVED"


class OutcomeResult:
    def __init__(
        self,
        outcome: str,
        exit_price: float | None,
        exit_time: datetime | None,
        exit_time_ist: str | None,
        gross_pnl: float | None,
        spread_cost: float | None,
        slippage_cost: float | None,
        fees_cost: float | None,
        net_pnl: float | None,
        r_multiple: float | None,
        resolution_method: str,
        candles_evaluated: int,
    ):
        self.outcome = outcome
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.exit_time_ist = exit_time_ist
        self.gross_pnl = gross_pnl
        self.spread_cost = spread_cost
        self.slippage_cost = slippage_cost
        self.fees_cost = fees_cost
        self.net_pnl = net_pnl
        self.r_multiple = r_multiple
        self.resolution_method = resolution_method
        self.candles_evaluated = candles_evaluated

    def to_dict(self) -> dict:
        return {
            "outcome": self.outcome,
            "exit_price": self.exit_price,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_time_ist": self.exit_time_ist,
            "gross_pnl": self.gross_pnl,
            "spread_cost": self.spread_cost,
            "slippage_cost": self.slippage_cost,
            "fees_cost": self.fees_cost,
            "net_pnl": self.net_pnl,
            "r_multiple": self.r_multiple,
            "resolution_method": self.resolution_method,
            "candles_evaluated": self.candles_evaluated,
        }


class OutcomeEngine:
    """
    Phase 33: Resolves signal outcomes from real subsequent candles.

    Usage:
        result = await outcome_engine.resolve(
            symbol="BTCUSD", timeframe="H4",
            direction="BUY", entry_price=68000.0,
            stop_loss=67500.0, take_profit=69000.0,
            signal_time=datetime(..., tzinfo=utc),
            expiry_time=datetime(..., tzinfo=utc),
        )
    """

    def __init__(
        self,
        spread_pips: float = DEFAULT_SPREAD_PIPS,
        slippage_pips: float = DEFAULT_SLIPPAGE_PIPS,
        fees_per_lot: float = DEFAULT_FEES_PER_LOT,
        lot_size: float = DEFAULT_LOT_SIZE,
        pip_value: float = DEFAULT_PIP_VALUE,
    ):
        self.spread_pips = spread_pips
        self.slippage_pips = slippage_pips
        self.fees_per_lot = fees_per_lot
        self.lot_size = lot_size
        self.pip_value = pip_value

    async def resolve(
        self,
        symbol: str,
        timeframe: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        signal_time: datetime,
        expiry_time: datetime,
    ) -> OutcomeResult:
        """
        Fetches real candles AFTER signal_time and resolves the outcome.
        Evaluates TP/SL breaches on intermediate closed candles even before expiry_time.
        """
        from app.market_data.service import market_service
        import pandas as pd

        now = datetime.now(timezone.utc)
        rates = await market_service.get_rates(symbol, timeframe, count=50)
        if not rates:
            return OutcomeResult(
                outcome=OUTCOME_UNRESOLVED if now < expiry_time else OUTCOME_EXPIRED,
                exit_price=None,
                exit_time=None if now < expiry_time else expiry_time,
                exit_time_ist=None if now < expiry_time else ISTConverter.to_ist_string(expiry_time),
                gross_pnl=None,
                spread_cost=None,
                slippage_cost=None,
                fees_cost=None,
                net_pnl=None,
                r_multiple=None,
                resolution_method="DATA_UNAVAILABLE",
                candles_evaluated=0,
            )

        df = pd.DataFrame(rates)
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

        # Use only candles AFTER signal_time
        signal_ts = pd.Timestamp(signal_time)
        if signal_ts.tzinfo is None:
            signal_ts = signal_ts.tz_localize("UTC")
        df = df[df['timestamp'] > signal_ts].copy()

        if df.empty:
            return OutcomeResult(
                outcome=OUTCOME_UNRESOLVED if now < expiry_time else OUTCOME_EXPIRED,
                exit_price=None,
                exit_time=None if now < expiry_time else expiry_time,
                exit_time_ist=None if now < expiry_time else ISTConverter.to_ist_string(expiry_time),
                gross_pnl=None,
                spread_cost=None,
                slippage_cost=None,
                fees_cost=None,
                net_pnl=None,
                r_multiple=None,
                resolution_method="NO_CANDLES_AFTER_SIGNAL",
                candles_evaluated=0,
            )

        candles_evaluated = len(df)
        risk = abs(entry_price - stop_loss)

        for _, row in df.iterrows():
            high = float(row['high'])
            low = float(row['low'])
            candle_ts = row['timestamp'].to_pydatetime()

            # Zero-trust breach conditions
            if direction == "BUY":
                tp_touched = high >= take_profit
                sl_touched = low <= stop_loss
            else:
                tp_touched = low <= take_profit
                sl_touched = high >= stop_loss

            if tp_touched and sl_touched:
                # AMBIGUOUS — both levels breached inside same candle
                return self._build_result(
                    outcome=OUTCOME_AMBIGUOUS,
                    exit_price=None,
                    exit_time=candle_ts,
                    entry=entry_price,
                    direction=direction,
                    risk=risk,
                    candles_evaluated=candles_evaluated,
                    method="SAME_CANDLE_AMBIGUOUS",
                )

            if tp_touched:
                return self._build_result(
                    outcome=OUTCOME_TP_HIT,
                    exit_price=take_profit,
                    exit_time=candle_ts,
                    entry=entry_price,
                    direction=direction,
                    risk=risk,
                    candles_evaluated=candles_evaluated,
                    method="CANDLE_TP_BREACH",
                )

            if sl_touched:
                return self._build_result(
                    outcome=OUTCOME_SL_HIT,
                    exit_price=stop_loss,
                    exit_time=candle_ts,
                    entry=entry_price,
                    direction=direction,
                    risk=risk,
                    candles_evaluated=candles_evaluated,
                    method="CANDLE_SL_BREACH",
                )

            # Check expiry
            if candle_ts >= expiry_time:
                close_price = float(row['close'])
                return self._build_result(
                    outcome=OUTCOME_TIME_EXIT,
                    exit_price=close_price,
                    exit_time=candle_ts,
                    entry=entry_price,
                    direction=direction,
                    risk=risk,
                    candles_evaluated=candles_evaluated,
                    method="TIME_EXPIRY",
                )

        # If candles were evaluated but neither TP/SL was hit and not yet expired:
        if now < expiry_time:
            return OutcomeResult(
                outcome=OUTCOME_UNRESOLVED,
                exit_price=None,
                exit_time=None,
                exit_time_ist=None,
                gross_pnl=None,
                spread_cost=None,
                slippage_cost=None,
                fees_cost=None,
                net_pnl=None,
                r_multiple=None,
                resolution_method="ACTIVE_IN_PROGRESS",
                candles_evaluated=candles_evaluated,
            )

        # If now >= expiry_time and no subsequent candle triggered TP/SL
        last_close = float(df.iloc[-1]['close'])
        last_ts = df.iloc[-1]['timestamp'].to_pydatetime()
        return self._build_result(
            outcome=OUTCOME_TIME_EXIT,
            exit_price=last_close,
            exit_time=last_ts,
            entry=entry_price,
            direction=direction,
            risk=risk,
            candles_evaluated=candles_evaluated,
            method="TIME_EXPIRY_AFTER_CANDLES",
        )

    def _build_result(
        self,
        outcome: str,
        exit_price: float | None,
        exit_time: datetime,
        entry: float,
        direction: str,
        risk: float,
        candles_evaluated: int,
        method: str,
    ) -> OutcomeResult:
        """Calculates gross/net PnL and R multiple."""
        if exit_price is None or outcome == OUTCOME_AMBIGUOUS:
            return OutcomeResult(
                outcome=outcome,
                exit_price=None,
                exit_time=exit_time,
                exit_time_ist=ISTConverter.to_ist_string(exit_time),
                gross_pnl=None,
                spread_cost=None,
                slippage_cost=None,
                fees_cost=None,
                net_pnl=None,
                r_multiple=None,
                resolution_method=method,
                candles_evaluated=candles_evaluated,
            )

        # Gross PnL in price units
        if direction == "BUY":
            gross_move = exit_price - entry
        else:
            gross_move = entry - exit_price

        # Convert to $ using lot_size × pip_value (simplified for paper trading)
        # Treat 1 unit of price move = 1 pip for non-FX; FX adjusts separately
        gross_pnl = round(gross_move * self.lot_size * self.pip_value, 4)
        spread_cost = round(self.spread_pips * self.lot_size * self.pip_value, 4)
        slippage_cost = round(self.slippage_pips * self.lot_size * self.pip_value, 4)
        fees_cost = round(self.fees_per_lot * self.lot_size, 4)
        net_pnl = round(gross_pnl - spread_cost - slippage_cost - fees_cost, 4)

        r_multiple = round(net_pnl / (risk * self.lot_size * self.pip_value), 4) if risk > 0 else None

        return OutcomeResult(
            outcome=outcome,
            exit_price=round(exit_price, 5),
            exit_time=exit_time,
            exit_time_ist=ISTConverter.to_ist_string(exit_time),
            gross_pnl=gross_pnl,
            spread_cost=spread_cost,
            slippage_cost=slippage_cost,
            fees_cost=fees_cost,
            net_pnl=net_pnl,
            r_multiple=r_multiple,
            resolution_method=method,
            candles_evaluated=candles_evaluated,
        )


outcome_engine = OutcomeEngine()
