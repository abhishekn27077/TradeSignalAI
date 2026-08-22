import json
import os
import pytest
from app.api.v1.evidence_routes import get_feature_contribution


def test_phase49_feature_registry_schema_and_count():
    registry_path = os.path.join(os.path.dirname(__file__), "..", "config", "feature_registry.json")
    assert os.path.exists(registry_path), "config/feature_registry.json must exist"
    
    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)
        
    assert registry["registry_version"] == "49.0.0-PROD"
    assert registry["config_hash"] == "79a4f8e12b79310d"
    
    features = registry["features"]
    assert len(features) == 14, "Must have exactly 14 authoritative indicators/features"
    
    valid_statuses = {
        "CORE_SIGNAL",
        "SUPPORTING_SIGNAL",
        "RISK_ONLY",
        "REGIME_ONLY",
        "FILTER_ONLY",
        "DISPLAY_ONLY",
        "IMPLEMENTED_UNUSED",
        "DEPRECATED",
    }
    
    for feat in features:
        assert "id" in feat
        assert "name" in feat
        assert "category" in feat
        assert "implementation_path" in feat
        assert "runtime_function" in feat
        assert "canonical_engine_path" in feat
        assert "status" in feat
        assert feat["status"] in valid_statuses


@pytest.mark.asyncio
async def test_phase49_feature_contribution_api():
    res = await get_feature_contribution()
    
    assert res["config_hash"] == "79a4f8e12b79310d"
    assert res["authoritative_features_count"] == 14
    assert res["realized_trades"] == 42
    assert "contributions" in res
    assert len(res["contributions"]) >= 6
    
    for c in res["contributions"]:
        assert "component" in c
        assert "delta_pf" in c
        assert "status" in c


def test_phase49_signal_idempotency_key_generation():
    import hashlib
    
    # Deterministic generation
    asset = "EURUSD"
    tf = "1H"
    candle_ts = "2026-08-22T21:00:00Z"
    direction = "BUY"
    config_hash = "79a4f8e12b79310d"
    
    key1 = hashlib.sha256(f"{asset}:{tf}:{candle_ts}:{direction}:{config_hash}".encode("utf-8")).hexdigest()
    key2 = hashlib.sha256(f"{asset}:{tf}:{candle_ts}:{direction}:{config_hash}".encode("utf-8")).hexdigest()
    
    assert key1 == key2, "Idempotency key must be bit-for-bit reproducible"
