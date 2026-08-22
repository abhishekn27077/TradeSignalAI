"""
tests/test_phase38_pnl_math.py
Phase 38: Rigorous mathematical verification of Gross and Net P&L deductions.
Formula:
  gross_move = (exit - entry) for BUY, (entry - exit) for SELL
  gross_pnl  = gross_move * lot_size * pip_value
  spread_cost = spread_pips * lot_size * pip_value
  slippage_cost = slippage_pips * lot_size * pip_value
  fees_cost  = fees_per_lot * lot_size
  net_pnl    = gross_pnl - spread_cost - slippage_cost - fees_cost
"""
import pytest
from datetime import datetime, timezone
from app.execution.outcome_engine import OutcomeEngine, OUTCOME_TP_HIT, OUTCOME_SL_HIT


def test_pnl_math_buy_win():
    engine = OutcomeEngine(
        spread_pips=2.0,
        slippage_pips=0.5,
        fees_per_lot=1.0,
        lot_size=0.1,
        pip_value=10.0,
    )

    # Entry = 100, Exit = 110 (10 points gain)
    entry = 100.0
    exit_price = 110.0
    risk = 5.0  # SL = 95

    res = engine._build_result(
        outcome=OUTCOME_TP_HIT,
        exit_price=exit_price,
        exit_time=datetime.now(timezone.utc),
        entry=entry,
        direction="BUY",
        risk=risk,
        candles_evaluated=3,
        method="TEST",
    )

    expected_gross = round((110.0 - 100.0) * 0.1 * 10.0, 4)  # 10 * 1.0 = 10.0
    expected_spread = round(2.0 * 0.1 * 10.0, 4)             # 2.0
    expected_slippage = round(0.5 * 0.1 * 10.0, 4)           # 0.5
    expected_fees = round(1.0 * 0.1, 4)                      # 0.1
    expected_net = round(expected_gross - expected_spread - expected_slippage - expected_fees, 4) # 10.0 - 2.6 = 7.4

    assert res.gross_pnl == expected_gross
    assert res.spread_cost == expected_spread
    assert res.slippage_cost == expected_slippage
    assert res.fees_cost == expected_fees
    assert res.net_pnl == expected_net
    assert res.r_multiple == round(expected_net / (risk * 0.1 * 10.0), 4)


def test_pnl_math_sell_loss():
    engine = OutcomeEngine(
        spread_pips=2.0,
        slippage_pips=0.5,
        fees_per_lot=0.0,
        lot_size=0.01,
        pip_value=10.0,
    )

    entry = 1.1000
    exit_price = 1.1050  # Hit SL
    risk = 0.0050

    res = engine._build_result(
        outcome=OUTCOME_SL_HIT,
        exit_price=exit_price,
        exit_time=datetime.now(timezone.utc),
        entry=entry,
        direction="SELL",
        risk=risk,
        candles_evaluated=2,
        method="TEST",
    )

    gross_move = entry - exit_price  # -0.0050
    expected_gross = round(gross_move * 0.01 * 10.0, 4)  # -0.0005
    expected_spread = round(2.0 * 0.01 * 10.0, 4)        # 0.2
    expected_slippage = round(0.5 * 0.01 * 10.0, 4)      # 0.05
    expected_fees = 0.0
    expected_net = round(expected_gross - expected_spread - expected_slippage - expected_fees, 4)

    assert res.gross_pnl == expected_gross
    assert res.net_pnl == expected_net
    assert res.net_pnl < res.gross_pnl  # Net is always strictly worse than gross due to friction
