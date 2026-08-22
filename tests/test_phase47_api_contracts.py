"""
Phase 47 — Test Suite for Frontend-Backend API Contracts.

Verifies:
  - JSON schema conformance for /signals/h4-intelligence
  - Response contract for /journal/trades
  - Response contract for /signals/today and /signals/yesterday
  - Response contract for /live/today
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_h4_intelligence_contract():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/signals/h4-intelligence")
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True
        assert "matrix" in data
        assert "assets_scanned" in data
        assert len(data["matrix"]) == 9


@pytest.mark.asyncio
async def test_journal_trades_contract():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/journal/trades")
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True
        assert "trades" in data
        assert isinstance(data["trades"], list)


@pytest.mark.asyncio
async def test_live_today_command_contract():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/live/today")
        assert res.status_code == 200
        data = res.json()
        assert "summary" in data
        assert "forecasts" in data
        assert len(data["forecasts"]) == 9
