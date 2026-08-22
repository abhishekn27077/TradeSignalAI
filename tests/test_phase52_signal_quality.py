import pytest
from app.strategies.SignalQuality.models import SignalGrade, NoTradeReason
from app.strategies.SignalQuality.engine import SignalQualityEngine
from app.market_data.quality.models import DataQualityState


def test_signal_quality_a_plus():
    engine = SignalQualityEngine(min_rr_ratio=1.2, min_confluence_score=50.0)

    # High quality setup: Confluence 88, R:R = (1.1060 - 1.1000) / (1.1000 - 1.0970) = 0.0060 / 0.0030 = 2.0
    eval_res = engine.evaluate_signal_quality(
        asset="EURUSD",
        direction="BUY",
        entry_price=1.1000,
        stop_loss=1.0970,
        take_profit=1.1060,
        confluence_score=88.0,
        data_quality_state=DataQualityState.DATA_QUALITY_GOOD,
        htf_aligned=True,
        is_event_risk=False,
        current_spread_pips=1.2
    )

    assert eval_res.grade == SignalGrade.A_PLUS
    assert eval_res.is_actionable is True
    assert len(eval_res.rejection_reasons) == 0
    assert eval_res.risk_reward_ratio >= 1.5


def test_signal_quality_no_trade_stale_and_poor_rr():
    engine = SignalQualityEngine(min_rr_ratio=1.2, min_confluence_score=50.0)

    # Poor R:R = 0.5 (Risk 40 pips, Reward 20 pips) + Stale Data
    eval_res = engine.evaluate_signal_quality(
        asset="EURUSD",
        direction="BUY",
        entry_price=1.1000,
        stop_loss=1.0960,
        take_profit=1.1020,
        confluence_score=70.0,
        data_quality_state=DataQualityState.DATA_STALE,
        htf_aligned=True,
        is_event_risk=False,
        current_spread_pips=1.2
    )

    assert eval_res.grade == SignalGrade.NO_TRADE
    assert eval_res.is_actionable is False
    assert NoTradeReason.DATA_STALE in eval_res.rejection_reasons
    assert NoTradeReason.POOR_RR in eval_res.rejection_reasons


def test_signal_quality_event_risk_and_spread_blocking():
    engine = SignalQualityEngine(min_rr_ratio=1.2, max_allowed_spread_pips=4.0)

    eval_res = engine.evaluate_signal_quality(
        asset="EURUSD",
        direction="BUY",
        entry_price=1.1000,
        stop_loss=1.0970,
        take_profit=1.1060,
        confluence_score=85.0,
        data_quality_state=DataQualityState.DATA_QUALITY_GOOD,
        htf_aligned=True,
        is_event_risk=True,        # Event risk!
        current_spread_pips=6.5   # Wide spread!
    )

    assert eval_res.grade == SignalGrade.NO_TRADE
    assert eval_res.is_actionable is False
    assert NoTradeReason.EVENT_RISK in eval_res.rejection_reasons
    assert NoTradeReason.HIGH_SPREAD in eval_res.rejection_reasons
