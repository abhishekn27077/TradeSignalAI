"""
tests/test_phase37_system_health.py
===================================
Tests system health endpoints and background services status.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_system_health():
    res = client.get("/api/v1/system/health")
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True or "status" in data
