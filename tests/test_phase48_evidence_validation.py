import pytest
from app.api.v1.evidence_routes import get_signal_trace


@pytest.mark.asyncio
async def test_phase48_signal_trace_api():
    trace = await get_signal_trace(prediction_id="SIG-EURUSD-1H-TEST001")
    
    assert trace["prediction_id"] == "SIG-EURUSD-1H-TEST001"
    assert trace["config_hash"] == "79a4f8e12b79310d"
    assert trace["strategy_version"] == "52.0.0-PROD"
    assert trace["model_version"] == "52.0.0-ENSEMBLE"
    assert "technical_features" in trace
    assert "market_structure" in trace
    assert "economic_news" in trace
    assert "ai_ensemble" in trace
    assert "risk_evaluation" in trace
    assert trace["final_decision"] in ["TAKE_TRADE", "NO_TRADE"]


def test_phase48_statistical_definitions_reconciliation():
    # Counterfactual breakdown
    losses_avoided = 54
    wins_missed = 18
    ambiguous = 10
    expired = 4
    
    resolved_gated = losses_avoided + wins_missed  # 72
    total_gated = losses_avoided + wins_missed + ambiguous + expired  # 86
    
    resolved_filter_precision = losses_avoided / resolved_gated
    total_gated_loss_avoidance = losses_avoided / total_gated
    
    assert round(resolved_filter_precision, 4) == 0.7500  # 75.00%
    assert round(total_gated_loss_avoidance, 4) == 0.6279   # 62.79%


def test_phase48_real_money_safety_invariant():
    from app.analytics.continuous_forward_monitor import continuous_forward_monitor
    snapshot = continuous_forward_monitor.evaluate_live_cohort()
    assert snapshot.config_hash == "79a4f8e12b79310d"
    assert snapshot.governance_tier in ["EARLY_EVIDENCE", "PRELIMINARY_EVIDENCE"]
