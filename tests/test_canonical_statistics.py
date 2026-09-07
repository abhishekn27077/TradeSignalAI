"""
tests/test_canonical_statistics.py
==================================
Verifies the Single Source of Truth (SSOT) Canonical Statistics Service,
Wilson 95% Confidence Intervals, Profit Factor, and Drawdown calculations (Phase 70).
"""

import pytest
from app.analytics.canonical_statistics_service import canonical_statistics_service
from app.strategies.indicators.indicator_registry import indicator_registry


def test_wilson_ci_calculation():
    # 0 wins in 0 trades
    l0, u0 = canonical_statistics_service.calculate_wilson_ci(0, 0)
    assert l0 == 0.0 and u0 == 0.0

    # 10 wins in 10 trades (100% win rate)
    # Wilson interval must reflect uncertainty of small sample (upper 100%, lower around ~72%)
    l10, u10 = canonical_statistics_service.calculate_wilson_ci(10, 10)
    assert l10 < 100.0
    assert l10 > 65.0
    assert u10 == 100.0

    # 70 wins in 100 trades (70% win rate)
    l100, u100 = canonical_statistics_service.calculate_wilson_ci(70, 100)
    assert 60.0 < l100 < 70.0
    assert 70.0 < u100 < 80.0


def test_canonical_performance_summary_execution():
    stats = canonical_statistics_service.get_canonical_performance_summary(date_filter="ALL")
    assert stats["success"] is True
    assert "win_rate_pct" in stats
    assert "wilson_95_ci" in stats
    assert "profit_factor" in stats
    assert "total_net_r" in stats
    assert "max_drawdown_r" in stats
    assert isinstance(stats["equity_curve"], list)


def test_indicator_collinearity_attenuation():
    # When 3 momentum indicators are active, their weights must be attenuated
    active = ["squeeze_momentum", "macd_custom", "ut_bot_alerts", "supertrend", "smc_order_blocks"]
    
    # 1. Unnormalized attenuation test: effective weight must be less than base weight
    unnorm_weights = indicator_registry.compute_collinearity_attenuated_weights(active, normalize=False)
    assert unnorm_weights["squeeze_momentum"] < indicator_registry.get_indicator("squeeze_momentum").base_weight
    assert unnorm_weights["macd_custom"] < indicator_registry.get_indicator("macd_custom").base_weight

    # 2. Normalized test: weights must sum to 1.0
    norm_weights = indicator_registry.compute_collinearity_attenuated_weights(active, normalize=True)
    assert len(norm_weights) == len(active)
    assert round(sum(norm_weights.values()), 2) == 1.00
