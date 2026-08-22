import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_market_structure():
    response = client.get("/api/v1/analysis/structure/EURUSD")
    assert response.status_code == 200
    data = response.json()
    assert data["asset"] == "EURUSD"
    assert "strength" in data
    assert "recent_swings" in data


def test_api_smart_money():
    response = client.get("/api/v1/analysis/smart-money/EURUSD")
    assert response.status_code == 200
    data = response.json()
    assert "dealing_range" in data
    assert "order_blocks" in data
    assert "fair_value_gaps" in data


def test_api_liquidity():
    response = client.get("/api/v1/analysis/liquidity/EURUSD")
    assert response.status_code == 200
    data = response.json()
    assert "liquidity_pools" in data
    assert "liquidity_sweeps" in data


def test_api_sessions():
    response = client.get("/api/v1/analysis/sessions/EURUSD")
    assert response.status_code == 200
    data = response.json()
    assert "session_name" in data
    assert "is_killzone" in data


def test_api_technical():
    response = client.get("/api/v1/analysis/technical/EURUSD")
    assert response.status_code == 200
    data = response.json()
    assert "SUPERTREND" in data
    assert "UT_BOT" in data


def test_api_regime():
    response = client.get("/api/v1/analysis/regime/EURUSD")
    assert response.status_code == 200
    data = response.json()
    assert "regime" in data


def test_api_confluence():
    response = client.get("/api/v1/analysis/confluence/EURUSD")
    assert response.status_code == 200
    data = response.json()
    assert "total_score" in data
    assert "layer_scores" in data


def test_api_summary():
    response = client.get("/api/v1/analysis/summary/EURUSD")
    assert response.status_code == 200
    data = response.json()
    assert "confluence" in data
    assert "regime" in data
    assert "strategy" in data
    assert "timestamp_ist" in data
