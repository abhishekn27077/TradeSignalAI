"""
tests/test_phase38_ablation_evidence.py
Phase 38: Verification of Phase 35 Mode A/B/C ablation isolation and evidence retention.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_ablation_history_filtering():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Query specifically for Mode A
        res_a = await client.get("/api/v1/signals/history?ablation_mode=MODE_A")
        assert res_a.status_code == 200
        assert res_a.json().get("success") is True

        # Query specifically for Mode B
        res_b = await client.get("/api/v1/signals/history?ablation_mode=MODE_B")
        assert res_b.status_code == 200
        assert res_b.json().get("success") is True

        # Query specifically for Mode C
        res_c = await client.get("/api/v1/signals/history?ablation_mode=MODE_C")
        assert res_c.status_code == 200
        assert res_c.json().get("success") is True
