"""
tests/test_phase37_api_contract.py
==================================
Tests FastAPI endpoints for Phase 37 compliance, verifying schema accuracy,
empty state handling, and proper field definitions.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_h4_intelligence_endpoint():
    response = client.get("/api/v1/signals/h4-intelligence")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["assets_scanned"] == 9
    assert isinstance(data["matrix"], list)
    assert len(data["matrix"]) == 9
    assert "candle_boundary" in data
    
    first = data["matrix"][0]
    for required_key in ["asset", "price", "regime", "quant", "kronos", "faiss", "time_pattern", "consensus", "risk", "final"]:
        assert required_key in first, f"Missing {required_key} in H4 matrix"


def test_live_signals_contract():
    response = client.get("/api/v1/signals/live")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) or data.get("success") is True


def test_today_signals_contract():
    response = client.get("/api/v1/signals/today")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) or data.get("success") is True


def test_signal_history_contract():
    response = client.get("/api/v1/signals/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) or data.get("success") is True


def test_dashboard_analytics_contract():
    response = client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "signals_today" in data
    assert "avg_confidence" in data
    assert "avg_grade" in data
