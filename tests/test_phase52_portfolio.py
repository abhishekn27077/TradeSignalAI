import pytest
from app.portfolio.currency_exposure_engine import CurrencyExposureEngine
from app.portfolio.risk_budget_engine import RiskBudgetEngine


def test_currency_exposure_engine():
    engine = CurrencyExposureEngine(max_single_currency_lots=2.5)

    # 2.0 lots EURUSD BUY -> +2.0 EUR, -2.0 USD
    # 1.0 lot GBPUSD BUY  -> +1.0 GBP, -1.0 USD
    # Total USD Exposure: -3.0 USD (exceeds 2.5 lot threshold!)
    open_positions = [
        {"asset": "EURUSD", "direction": "BUY", "lots": 2.0},
        {"asset": "GBPUSD", "direction": "BUY", "lots": 1.0},
    ]

    report = engine.evaluate_exposure(open_positions)
    assert report.is_exposure_limit_exceeded is True
    assert "USD" in report.blocked_currencies
    assert report.currency_exposures["USD"] == -3.0
    assert report.currency_exposures["EUR"] == 2.0
    assert report.currency_exposures["GBP"] == 1.0

    # Test can_open_new_position: attempting another USD-short BUY on AUDUSD must be blocked!
    can_open, reason = engine.can_open_new_position("AUDUSD", "BUY", 0.5, open_positions)
    assert can_open is False
    assert "exceeds max correlated exposure" in reason


def test_risk_budget_engine_dynamic_sizing():
    engine = RiskBudgetEngine(default_risk_pct=0.01, max_daily_drawdown_pct=0.05)

    # Equity $10,000, Risk 1% = $100. Stop 20 pips -> Lots = 0.50
    result = engine.calculate_position_size(
        account_equity=10000.0,
        entry_price=1.1000,
        stop_loss=1.0980,
        asset="EURUSD",
        direction="BUY"
    )

    assert result.is_trade_allowed is True
    assert result.recommended_lots == 0.50
    assert result.risk_amount_usd == 100.0


def test_risk_budget_engine_drawdown_halting():
    engine = RiskBudgetEngine(default_risk_pct=0.01, max_daily_drawdown_pct=0.05)

    # Daily drawdown at 6% (exceeds 5% halt)
    result = engine.calculate_position_size(
        account_equity=9400.0,
        entry_price=1.1000,
        stop_loss=1.0980,
        current_daily_drawdown_pct=0.06
    )

    assert result.is_trade_allowed is False
    assert "Trading halted" in result.rejection_reason
