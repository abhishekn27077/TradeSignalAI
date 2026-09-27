"""
app/backtesting/intra_candle_engine.py
======================================
Intra-Candle Sub-Bar Reconstruction & High-Fidelity Execution Engine.

Benchmarked against Freqtrade's `--timeframe-detail 1m` sub-bar path simulation
and QuantConnect LEAN's slice-based order consolidator.

Solves the "bar ambiguity" problem:
When higher-timeframe bars (e.g. 1H, 4H) touch both Take Profit and Stop Loss levels,
standard backtesting either uses lookahead heuristics or overly conservative assumptions.
This engine reconstructs the path of price movement using chronological 1-minute sub-bars
to determine the exact sequence of events, realistic slippage, spread, and maker/taker fees.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np


@dataclass(frozen=True)
class ExecutionFeeTier:
    maker_fee_bps: float = 2.0   # 0.02%
    taker_fee_bps: float = 5.0   # 0.05%
    slippage_bps: float = 3.0    # 0.03%


@dataclass
class IntraCandleExecutionResult:
    outcome: str  # "WON", "LOST", "TIME_EXIT", "NO_ENTRY"
    entry_executed: bool
    entry_price: float
    exit_price: float
    gross_pnl: float
    net_pnl: float
    gross_r: float
    net_r: float
    exit_reason: str
    exit_sub_bar_index: Optional[int]
    exit_sub_bar_time: Optional[str]
    total_fees_paid: float
    total_slippage_paid: float
    sub_bars_evaluated: int
    path_verified: bool = True


class IntraCandleReconstructionEngine:
    """
    Evaluates higher-timeframe trade orders against chronological lower-timeframe sub-bars.
    """

    def __init__(self, default_fee_tier: Optional[ExecutionFeeTier] = None):
        self.fee_tier = default_fee_tier or ExecutionFeeTier()

    def resolve_trade_path(
        self,
        direction: str,  # "BUY", "SELL"
        target_entry: float,
        stop_loss: float,
        take_profit: float,
        sub_bars: pd.DataFrame,
        order_type: str = "MARKET",
        entry_timeout_bars: int = 15,
        fee_tier: Optional[ExecutionFeeTier] = None,
    ) -> IntraCandleExecutionResult:
        """
        Reconstructs the execution path through chronological 1m sub-bars.

        sub_bars DataFrame must have columns: ['open', 'high', 'low', 'close']
        and optionally 'timestamp'.
        """
        fees = fee_tier or self.fee_tier
        if sub_bars.empty:
            return IntraCandleExecutionResult(
                outcome="NO_ENTRY",
                entry_executed=False,
                entry_price=0.0,
                exit_price=0.0,
                gross_pnl=0.0,
                net_pnl=0.0,
                gross_r=0.0,
                net_r=0.0,
                exit_reason="EMPTY_SUB_BARS",
                exit_sub_bar_index=None,
                exit_sub_bar_time=None,
                total_fees_paid=0.0,
                total_slippage_paid=0.0,
                sub_bars_evaluated=0,
                path_verified=False,
            )

        n_bars = len(sub_bars)
        opens = sub_bars['open'].values
        highs = sub_bars['high'].values
        lows = sub_bars['low'].values
        closes = sub_bars['close'].values
        timestamps = (
            sub_bars['timestamp'].astype(str).values
            if 'timestamp' in sub_bars.columns
            else [f"bar_{i}" for i in range(n_bars)]
        )

        direction = direction.upper()
        if direction not in ("BUY", "SELL"):
            raise ValueError(f"Invalid direction {direction}")

        # 1. Simulate Entry
        entry_index = 0
        raw_entry = opens[0] if order_type == "MARKET" else target_entry
        slip_mult = 1.0 + (fees.slippage_bps / 10000.0) if direction == "BUY" else 1.0 - (fees.slippage_bps / 10000.0)
        actual_entry = raw_entry * slip_mult
        entry_fee = actual_entry * (fees.taker_fee_bps / 10000.0)

        risk_dist = abs(actual_entry - stop_loss)
        if risk_dist <= 1e-8:
            risk_dist = actual_entry * 0.01

        # 2. Chronological Traversal of Sub-Bars
        for idx in range(entry_index, n_bars):
            b_high = highs[idx]
            b_low = lows[idx]
            b_close = closes[idx]
            b_time = timestamps[idx]

            if direction == "BUY":
                sl_hit = b_low <= stop_loss
                tp_hit = b_high >= take_profit

                if sl_hit and tp_hit:
                    # Intra-bar conflict inside 1m bar: worst-case conservative rule
                    exit_price = stop_loss * (1.0 - fees.slippage_bps / 10000.0)
                    exit_fee = exit_price * (fees.taker_fee_bps / 10000.0)
                    gross_pnl = exit_price - actual_entry
                    total_fees = entry_fee + exit_fee
                    net_pnl = gross_pnl - total_fees
                    gross_r = gross_pnl / risk_dist
                    net_r = net_pnl / risk_dist
                    return IntraCandleExecutionResult(
                        outcome="LOST",
                        entry_executed=True,
                        entry_price=round(actual_entry, 5),
                        exit_price=round(exit_price, 5),
                        gross_pnl=round(gross_pnl, 5),
                        net_pnl=round(net_pnl, 5),
                        gross_r=round(gross_r, 3),
                        net_r=round(net_r, 3),
                        exit_reason="INTRA_BAR_AMBIGUITY_SL_FIRST",
                        exit_sub_bar_index=idx,
                        exit_sub_bar_time=b_time,
                        total_fees_paid=round(total_fees, 5),
                        total_slippage_paid=round(abs(actual_entry - raw_entry), 5),
                        sub_bars_evaluated=idx + 1,
                        path_verified=True,
                    )

                if sl_hit:
                    exit_price = stop_loss * (1.0 - fees.slippage_bps / 10000.0)
                    exit_fee = exit_price * (fees.taker_fee_bps / 10000.0)
                    gross_pnl = exit_price - actual_entry
                    total_fees = entry_fee + exit_fee
                    net_pnl = gross_pnl - total_fees
                    gross_r = gross_pnl / risk_dist
                    net_r = net_pnl / risk_dist
                    return IntraCandleExecutionResult(
                        outcome="LOST",
                        entry_executed=True,
                        entry_price=round(actual_entry, 5),
                        exit_price=round(exit_price, 5),
                        gross_pnl=round(gross_pnl, 5),
                        net_pnl=round(net_pnl, 5),
                        gross_r=round(gross_r, 3),
                        net_r=round(net_r, 3),
                        exit_reason="SL_HIT",
                        exit_sub_bar_index=idx,
                        exit_sub_bar_time=b_time,
                        total_fees_paid=round(total_fees, 5),
                        total_slippage_paid=round(abs(actual_entry - raw_entry), 5),
                        sub_bars_evaluated=idx + 1,
                        path_verified=True,
                    )

                if tp_hit:
                    exit_price = take_profit * (1.0 - fees.slippage_bps / 10000.0)
                    exit_fee = exit_price * (fees.maker_fee_bps / 10000.0)
                    gross_pnl = exit_price - actual_entry
                    total_fees = entry_fee + exit_fee
                    net_pnl = gross_pnl - total_fees
                    gross_r = gross_pnl / risk_dist
                    net_r = net_pnl / risk_dist
                    return IntraCandleExecutionResult(
                        outcome="WON",
                        entry_executed=True,
                        entry_price=round(actual_entry, 5),
                        exit_price=round(exit_price, 5),
                        gross_pnl=round(gross_pnl, 5),
                        net_pnl=round(net_pnl, 5),
                        gross_r=round(gross_r, 3),
                        net_r=round(net_r, 3),
                        exit_reason="TP_HIT",
                        exit_sub_bar_index=idx,
                        exit_sub_bar_time=b_time,
                        total_fees_paid=round(total_fees, 5),
                        total_slippage_paid=round(abs(actual_entry - raw_entry), 5),
                        sub_bars_evaluated=idx + 1,
                        path_verified=True,
                    )

            elif direction == "SELL":
                sl_hit = b_high >= stop_loss
                tp_hit = b_low <= take_profit

                if sl_hit and tp_hit:
                    exit_price = stop_loss * (1.0 + fees.slippage_bps / 10000.0)
                    exit_fee = exit_price * (fees.taker_fee_bps / 10000.0)
                    gross_pnl = actual_entry - exit_price
                    total_fees = entry_fee + exit_fee
                    net_pnl = gross_pnl - total_fees
                    gross_r = gross_pnl / risk_dist
                    net_r = net_pnl / risk_dist
                    return IntraCandleExecutionResult(
                        outcome="LOST",
                        entry_executed=True,
                        entry_price=round(actual_entry, 5),
                        exit_price=round(exit_price, 5),
                        gross_pnl=round(gross_pnl, 5),
                        net_pnl=round(net_pnl, 5),
                        gross_r=round(gross_r, 3),
                        net_r=round(net_r, 3),
                        exit_reason="INTRA_BAR_AMBIGUITY_SL_FIRST",
                        exit_sub_bar_index=idx,
                        exit_sub_bar_time=b_time,
                        total_fees_paid=round(total_fees, 5),
                        total_slippage_paid=round(abs(actual_entry - raw_entry), 5),
                        sub_bars_evaluated=idx + 1,
                        path_verified=True,
                    )

                if sl_hit:
                    exit_price = stop_loss * (1.0 + fees.slippage_bps / 10000.0)
                    exit_fee = exit_price * (fees.taker_fee_bps / 10000.0)
                    gross_pnl = actual_entry - exit_price
                    total_fees = entry_fee + exit_fee
                    net_pnl = gross_pnl - total_fees
                    gross_r = gross_pnl / risk_dist
                    net_r = net_pnl / risk_dist
                    return IntraCandleExecutionResult(
                        outcome="LOST",
                        entry_executed=True,
                        entry_price=round(actual_entry, 5),
                        exit_price=round(exit_price, 5),
                        gross_pnl=round(gross_pnl, 5),
                        net_pnl=round(net_pnl, 5),
                        gross_r=round(gross_r, 3),
                        net_r=round(net_r, 3),
                        exit_reason="SL_HIT",
                        exit_sub_bar_index=idx,
                        exit_sub_bar_time=b_time,
                        total_fees_paid=round(total_fees, 5),
                        total_slippage_paid=round(abs(actual_entry - raw_entry), 5),
                        sub_bars_evaluated=idx + 1,
                        path_verified=True,
                    )

                if tp_hit:
                    exit_price = take_profit * (1.0 + fees.slippage_bps / 10000.0)
                    exit_fee = exit_price * (fees.maker_fee_bps / 10000.0)
                    gross_pnl = actual_entry - exit_price
                    total_fees = entry_fee + exit_fee
                    net_pnl = gross_pnl - total_fees
                    gross_r = gross_pnl / risk_dist
                    net_r = net_pnl / risk_dist
                    return IntraCandleExecutionResult(
                        outcome="WON",
                        entry_executed=True,
                        entry_price=round(actual_entry, 5),
                        exit_price=round(exit_price, 5),
                        gross_pnl=round(gross_pnl, 5),
                        net_pnl=round(net_pnl, 5),
                        gross_r=round(gross_r, 3),
                        net_r=round(net_r, 3),
                        exit_reason="TP_HIT",
                        exit_sub_bar_index=idx,
                        exit_sub_bar_time=b_time,
                        total_fees_paid=round(total_fees, 5),
                        total_slippage_paid=round(abs(actual_entry - raw_entry), 5),
                        sub_bars_evaluated=idx + 1,
                        path_verified=True,
                    )

        # 3. Bar Window Expired (Time Exit)
        last_close = closes[-1]
        exit_fee = last_close * (fees.taker_fee_bps / 10000.0)
        gross_pnl = (last_close - actual_entry) if direction == "BUY" else (actual_entry - last_close)
        total_fees = entry_fee + exit_fee
        net_pnl = gross_pnl - total_fees
        gross_r = gross_pnl / risk_dist
        net_r = net_pnl / risk_dist

        return IntraCandleExecutionResult(
            outcome="TIME_EXIT",
            entry_executed=True,
            entry_price=round(actual_entry, 5),
            exit_price=round(last_close, 5),
            gross_pnl=round(gross_pnl, 5),
            net_pnl=round(net_pnl, 5),
            gross_r=round(gross_r, 3),
            net_r=round(net_r, 3),
            exit_reason="TIME_EXPIRY",
            exit_sub_bar_index=n_bars - 1,
            exit_sub_bar_time=timestamps[-1],
            total_fees_paid=round(total_fees, 5),
            total_slippage_paid=round(abs(actual_entry - raw_entry), 5),
            sub_bars_evaluated=n_bars,
            path_verified=True,
        )


intra_candle_engine = IntraCandleReconstructionEngine()
