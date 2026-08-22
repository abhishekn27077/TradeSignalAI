import sys
sys.path.insert(0, ".")
from app.execution.outcome_engine import OutcomeEngine, OUTCOME_TP_HIT, OUTCOME_SL_HIT
from datetime import datetime, timezone


def validate_pnl_math():
    print("=== STARTING PHASE 38 MATHEMATICAL P&L VALIDATION ===")
    engine = OutcomeEngine(
        spread_pips=2.0,
        slippage_pips=0.5,
        fees_per_lot=2.5,
        lot_size=0.1,
        pip_value=10.0,
    )

    # 1. BUY Win scenario
    res_buy = engine._build_result(
        outcome=OUTCOME_TP_HIT,
        exit_price=1.1000,
        exit_time=datetime.now(timezone.utc),
        entry=1.0900,  # +100 pips
        direction="BUY",
        risk=0.0050,   # 50 pips risk
        candles_evaluated=4,
        method="TEST_VALIDATION",
    )

    gross_buy = (1.1000 - 1.0900) * 0.1 * 10.0  # 0.0100
    spread_buy = 2.0 * 0.1 * 10.0                # 2.0
    slip_buy = 0.5 * 0.1 * 10.0                  # 0.5
    fees_buy = 2.5 * 0.1                         # 0.25
    net_buy = round(gross_buy - spread_buy - slip_buy - fees_buy, 4)

    assert res_buy.gross_pnl == round(gross_buy, 4), f"Gross Buy mismatch: {res_buy.gross_pnl} vs {gross_buy}"
    assert res_buy.net_pnl == net_buy, f"Net Buy mismatch: {res_buy.net_pnl} vs {net_buy}"
    print(f"[PASS] BUY Win Calculation: Gross={res_buy.gross_pnl}, Net={res_buy.net_pnl}, R={res_buy.r_multiple}")

    # 2. SELL Loss scenario
    res_sell = engine._build_result(
        outcome=OUTCOME_SL_HIT,
        exit_price=1.1050,
        exit_time=datetime.now(timezone.utc),
        entry=1.1000,  # -50 pips loss
        direction="SELL",
        risk=0.0050,
        candles_evaluated=2,
        method="TEST_VALIDATION",
    )

    gross_sell = (1.1000 - 1.1050) * 0.1 * 10.0
    spread_sell = 2.0 * 0.1 * 10.0
    slip_sell = 0.5 * 0.1 * 10.0
    fees_sell = 2.5 * 0.1
    net_sell = round(gross_sell - spread_sell - slip_sell - fees_sell, 4)

    assert res_sell.gross_pnl == round(gross_sell, 4), f"Gross Sell mismatch: {res_sell.gross_pnl} vs {gross_sell}"
    assert res_sell.net_pnl == net_sell, f"Net Sell mismatch: {res_sell.net_pnl} vs {net_sell}"
    print(f"[PASS] SELL Loss Calculation: Gross={res_sell.gross_pnl}, Net={res_sell.net_pnl}, R={res_sell.r_multiple}")

    print("=== ALL P&L MATHEMATICAL FORMULAS VALIDATED PERFECTLY ===")


if __name__ == "__main__":
    validate_pnl_math()
