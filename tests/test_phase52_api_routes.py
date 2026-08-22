import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_market_data_health():
    res = client.get("/api/v1/system-intelligence/market-data-health")
    assert res.status_code == 200
    data = res.json()
    assert "overall_status" in data
    assert "total_monitored_feeds" in data
    assert "feeds" in data


def test_api_portfolio_exposure():
    res = client.get("/api/v1/system-intelligence/portfolio-exposure")
    assert res.status_code == 200
    data = res.json()
    assert "currency_exposures" in data
    assert "max_currency" in data
    assert "is_exposure_limit_exceeded" in data


def test_api_ensemble_evaluate():
    payload = {
        "regime": "STRONG_TREND",
        "votes": [
            {
                "family": "MARKET_STRUCTURE",
                "direction": "BUY",
                "confidence": 0.85,
                "quality": 0.90,
                "regime_suitability": 1.0,
                "evidence": ["BOS confirmed"]
            },
            {
                "family": "SMART_MONEY",
                "direction": "BUY",
                "confidence": 0.80,
                "quality": 0.85,
                "regime_suitability": 1.0,
                "evidence": ["Bullish Order Block"]
            }
        ]
    }
    res = client.post("/api/v1/system-intelligence/ensemble/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["direction"] == "BUY"
    assert data["ensemble_confidence"] > 0.5


def test_api_signal_quality_evaluate():
    payload = {
        "asset": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.1000,
        "stop_loss": 1.0970,
        "take_profit": 1.1060,
        "confluence_score": 85.0,
        "data_quality_state": "DATA_QUALITY_GOOD",
        "htf_aligned": True,
        "is_event_risk": False,
        "current_spread_pips": 1.2
    }
    res = client.post("/api/v1/system-intelligence/signal-quality/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["grade"] in ["A+", "A"]
    assert data["is_actionable"] is True


def test_api_execution_simulate():
    payload = {
        "asset": "EURUSD",
        "side": "BUY",
        "order_type": "MARKET",
        "requested_price": 1.1000,
        "stop_loss": 1.0970,
        "take_profit": 1.1060,
        "requested_lots": 1.0,
        "mode": "PAPER"
    }
    res = client.post("/api/v1/system-intelligence/execution/simulate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["fill_status"] == "FILLED"
    assert data["fill_price"] > 1.1000


def test_api_pipeline_run():
    payload = {
        "asset": "EURUSD",
        "current_spread_pips": 1.0,
        "is_event_risk": False
    }
    res = client.post("/api/v1/system-intelligence/pipeline/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "trace_id" in data
    assert "status" in data
    assert len(data["stages"]) >= 9

