import pytest
import math
from app.analytics.statistical_validation_engine import StatisticalValidationEngine, statistical_validation_engine


def test_wilson_confidence_interval_math():
    engine = StatisticalValidationEngine()
    # 64 successes out of 100 trials
    lower, upper = engine.calculate_wilson_ci(k=64, n=100, confidence=0.95)
    
    assert 0.53 < lower < 0.55
    assert 0.72 < upper < 0.74
    assert lower < 0.64 < upper


def test_bootstrap_metric_ci():
    engine = StatisticalValidationEngine()
    # Realized returns with 26 wins and 16 losses (N=42)
    trade_rs = [1.82] * 26 + [-0.98] * 16
    lower, upper = engine.bootstrap_metric_ci(
        values=trade_rs,
        metric_fn=lambda s: float(sum(s) / len(s)),
        iterations=1000,
        ci_pct=0.95,
        seed=42,
    )
    
    assert lower < upper
    assert lower > 0.0  # Positive expectancy lower bound for N=42 sample


def test_statistical_validation_engine_evaluation():
    report = statistical_validation_engine.evaluate_live_shadow_sample(
        realized_trade_rs=[1.82] * 26 + [-0.98] * 16,
        predictions=[{"direction_correct": True}] * 82 + [{"direction_correct": False}] * 46,
    )

    assert report.sample_size_signals == 128
    assert report.sample_size_trades == 42
    assert report.directional_accuracy > 0.60
    assert report.win_rate > 0.60
    assert report.profit_factor > 1.50
    assert report.classification == "EDGE_SUPPORTED"
    assert report.config_hash == "79a4f8e12b79310d"


def test_insufficient_sample_classification():
    engine = StatisticalValidationEngine()
    # Small sample size (< 30 trades)
    report = engine.evaluate_live_shadow_sample(
        realized_trade_rs=[2.0, -1.0, 2.0],
        predictions=[{"direction_correct": True}] * 5,
    )
    assert report.classification == "INSUFFICIENT_SAMPLE"
