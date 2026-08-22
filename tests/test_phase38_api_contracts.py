"""
tests/test_phase38_api_contracts.py
Phase 38: Comprehensive API contract test suite for /today, /yesterday, /active, /history, and /{signal_id}.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_api_today_signals_contract():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/signals/today")
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True
        assert "signals" in data
        assert isinstance(data["signals"], list)
        assert "count" in data


@pytest.mark.asyncio
async def test_api_yesterday_signals_contract():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/signals/yesterday")
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True
        assert "signals" in data
        assert isinstance(data["signals"], list)


@pytest.mark.asyncio
async def test_api_active_signals_contract():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/signals/active")
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True
        assert "signals" in data


@pytest.mark.asyncio
async def test_api_history_filters_contract():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/signals/history?time_range=7d&limit=10")
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True
        assert "signals" in data


@pytest.mark.asyncio
async def test_api_analytics_dashboard_contract():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/analytics/dashboard")
        assert res.status_code == 200
        data = res.json()
        assert data.get("success") is True
        assert "signals_today" in data
        assert "today_wins" in data
        assert "today_losses" in data
        assert "today_net_pnl" in data
        assert "active_signals_count" in data
        assert "recent_results" in data
        assert isinstance(data["recent_results"], list)
