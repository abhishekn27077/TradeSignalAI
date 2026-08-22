"""
Phase 47 — Test Suite for Runtime Connectivity and Health Diagnostics.

Verifies:
  - Root /health endpoint response
  - /api/v1/system/status health checks
  - /api/v1/runtime/diagnostics comprehensive telemetry across 11 subsystems
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_root_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "ok"
        assert "operational" in data.get("message", "")


@pytest.mark.asyncio
async def test_system_status_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/system/status")
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True
        assert "components" in data
        assert "database" in data["components"]


@pytest.mark.asyncio
async def test_runtime_diagnostics_subsystems():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/runtime/diagnostics")
        assert res.status_code == 200
        data = res.json()
        assert data.get("overall_status") == "LIVE"
        assert "subsystems" in data
        subsystems = data["subsystems"]

        required = [
            "backend", "database", "market_feed", "websocket",
            "scheduler", "forecast_engine", "models", "ai",
            "economic_calendar", "news", "ledger", "frontend_contract"
        ]
        for s in required:
            assert s in subsystems, f"Missing subsystem diagnostics for {s}"
            assert "status" in subsystems[s]
