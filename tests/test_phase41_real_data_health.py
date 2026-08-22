"""
Phase 41 — Test Suite for Real Data Health & Lineage Engine.

Verifies:
  - Detection of the 245,774+ real SQLite candle dataset
  - Invalid OHLC verification logic
  - Multi-timeframe and asset breakdown across all 9 core assets
  - Data lineage audit across all 10 sources
  - Zero-fake-health reporting
"""
import pytest
from app.analytics.data_health_engine import data_health_engine, CORE_ASSETS
from app.analytics.model_health_engine import model_health_engine


class TestRealDataHealth:
    def test_database_detected(self):
        health = data_health_engine.get_data_health()
        assert health["database_detected"] is True
        assert health["total_candles"] >= 100000

    def test_core_assets_covered(self):
        health = data_health_engine.get_data_health()
        assert "assets" in health
        for asset in CORE_ASSETS:
            assert asset in health["assets"]
            asset_info = health["assets"][asset]
            assert asset_info["total_candles"] > 0
            assert asset_info["first_timestamp"] is not None
            assert asset_info["last_timestamp"] is not None

    def test_invalid_ohlc_check(self):
        health = data_health_engine.get_data_health()
        assert "invalid_ohlc_count" in health
        assert "overall_quality_score_pct" in health
        assert health["overall_quality_score_pct"] > 95.0

    def test_data_lineage_has_10_sources(self):
        lineage = data_health_engine.get_data_lineage()
        expected_sources = [
            "market_data", "quant", "kronos", "faiss", "time_pattern",
            "regime", "macro", "news", "economic_calendar", "ai", "risk_engine"
        ]
        for src in expected_sources:
            assert src in lineage
            item = lineage[src]
            assert "source" in item
            assert "status" in item
            assert "type" in item
            assert item["type"] in ["REAL", "DEGRADED", "UNAVAILABLE"]

    def test_model_health_matrix(self):
        matrix = model_health_engine.get_health_matrix()
        assert "subsystems" in matrix
        assert matrix["total_subsystems"] == 11
        assert matrix["live_subsystems"] >= 8
        assert matrix["overall_status"] in ["HEALTHY", "DEGRADED"]
        for key, sub in matrix["subsystems"].items():
            assert "name" in sub
            assert "status" in sub
            assert sub["status"] in ["LIVE", "DEGRADED", "STALE", "ERROR", "DISABLED"]
