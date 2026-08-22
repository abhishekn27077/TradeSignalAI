import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.main import app

client = TestClient(app)

def test_forward_status():
    response = client.get("/api/v1/forward-validation/status")
    assert response.status_code == 200
    data = response.json()
    assert "experiment_status" in data
    assert data["experiment_status"] == "FORWARD PAPER VALIDATION CONTINUES"

def test_forward_ablation():
    response = client.get("/api/v1/forward-validation/ablation")
    assert response.status_code == 200
    data = response.json()
    assert "QUANT_ONLY" in data
    assert data["QUANT_ONLY"]["status"] == "INSUFFICIENT_DATA"
    assert data["FULL_STACK"]["status"] == "INSUFFICIENT_DATA"

def test_forward_assets():
    response = client.get("/api/v1/forward-validation/assets")
    assert response.status_code == 200
    data = response.json()
    assert "BTCUSD" in data
    assert data["BTCUSD"]["H4"]["status"] == "INSUFFICIENT_DATA"

def test_forward_calibration():
    response = client.get("/api/v1/forward-validation/calibration")
    assert response.status_code == 200
    data = response.json()
    assert "80-85" in data
    assert data["80-85"]["status"] == "INSUFFICIENT_DATA"

def test_forward_kronos():
    response = client.get("/api/v1/forward-validation/kronos")
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "INSUFFICIENT_DATA"

def test_forward_context():
    response = client.get("/api/v1/forward-validation/context")
    assert response.status_code == 200
    data = response.json()
    assert "NEWS" in data
    assert data["NEWS"]["status"] == "INSUFFICIENT_DATA"

def test_forward_friday_monday():
    response = client.get("/api/v1/forward-validation/friday-monday")
    assert response.status_code == 200
    data = response.json()
    assert "FOREX" in data
    assert data["FOREX"]["verdict"] == "INSUFFICIENT DATA"

def test_forward_latest_signals():
    response = client.get("/api/v1/forward-validation/signals/latest")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

if __name__ == "__main__":
    print("Running Phase 29.3 Integrity Tests...")
    pytest.main([__file__, "-v"])
