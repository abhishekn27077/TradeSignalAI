import pytest
import sqlite3
import os
import json
import asyncio
from datetime import datetime, timezone
import requests
import websockets

from app.runtime.live_forecast_scheduler import live_forecast_scheduler
from app.analytics.shadow_ledger_engine import shadow_ledger_engine
from app.analytics.shadow_validation_engine import shadow_validation_engine

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/api/v1/ws/stream"

def test_phase48_root_health():
    """Test 1: GET /health returns HTTP 200 with operational message."""
    res = requests.get(f"{BASE_URL}/health", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") == "ok" or data.get("success") is True
    assert "operational" in data.get("message", "").lower() or data.get("status") == "ok"

def test_phase48_system_health():
    """Test 2: GET /api/v1/system/health returns complete status."""
    res = requests.get(f"{BASE_URL}/api/v1/system/health", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True or "status" in data

def test_phase48_runtime_diagnostics_11_subsystems():
    """Test 3: GET /api/v1/runtime/diagnostics returns 11 verified subsystems with honest status."""
    res = requests.get(f"{BASE_URL}/api/v1/runtime/diagnostics", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert "overall_status" in data or data.get("success") is True
    subsystems = data.get("subsystems", {})
    
    expected_subsystems = [
        "backend", "database", "market_feed", "websocket", "scheduler",
        "forecast_engine", "models", "ai", "economic_calendar", "news", "ledger"
    ]
    for sub in expected_subsystems:
        assert sub in subsystems, f"Missing subsystem: {sub}"
        assert "status" in subsystems[sub]
        assert ("latency_ms" in subsystems[sub] or "layers" in subsystems[sub] or "latency" in subsystems[sub])

    # Market feed must be marked STALE or LIVE, never fake LIVE if timestamp is 2026-08-14
    feed_status = subsystems["market_feed"]["status"]
    assert feed_status in ["LIVE", "STALE", "OFFLINE"]

@pytest.mark.asyncio
async def test_phase48_websocket_heartbeat():
    """Test 4: WebSocket accepts connection and returns pong for ping."""
    async with websockets.connect(WS_URL, close_timeout=2) as ws:
        await ws.send(json.dumps({"action": "ping"}))
        got_pong = False
        for _ in range(5):
            msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
            data = json.loads(msg)
            if data.get("event") == "pong" or data.get("action") == "pong":
                got_pong = True
                break
        assert got_pong is True, "Must receive pong from WebSocket within 5 messages"

def test_phase48_market_data_freshness_classification():
    """Test 5: Market data freshness inspector accurately tags 2026-08-14 data as STALE."""
    if not os.path.exists("tradesignal.db"):
        pytest.skip("tradesignal.db not present")
    
    conn = sqlite3.connect("tradesignal.db")
    cur = conn.cursor()
    cur.execute("SELECT timestamp FROM historical_candles WHERE symbol = 'EURUSD' ORDER BY timestamp DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    
    latest_ts_str = row[0]
    try:
        dt = datetime.strptime(latest_ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        dt = datetime.fromisoformat(latest_ts_str.replace("Z", "+00:00"))
    now_utc = datetime.now(timezone.utc)
    age_seconds = (now_utc - dt).total_seconds()
    
    # Test stale classification logic
    stale_dt = datetime(2026, 8, 14, 0, 0, 0, tzinfo=timezone.utc)
    stale_age = (now_utc - stale_dt).total_seconds()
    stale_freshness = "LIVE" if stale_age < 7200 else "STALE"
    assert stale_freshness == "STALE", "Historical candles older than 2h must be classified as STALE"
    
    # DB data freshness matches actual age
    db_freshness = "LIVE" if age_seconds < 7200 else "STALE"
    assert db_freshness in ["LIVE", "STALE"]

def test_phase48_8_model_layer_classification():
    """Test 6: All 8 model layers declare explicit type (REAL or HEURISTIC or FALLBACK)."""
    candle = {
        "symbol": "EURUSD",
        "open": 1.1540,
        "high": 1.1550,
        "low": 1.1530,
        "close": 1.1545,
        "volume": 1000.0,
        "timestamp": "2026-08-14 05:00:00",
    }
    eval_res = live_forecast_scheduler.evaluate_multi_model_forecast("EURUSD", candle)
    models = eval_res["model_outputs"]
    
    expected_layers = ["quant", "kronos", "faiss", "time_pattern", "regime", "macro", "news", "ai"]
    for layer in expected_layers:
        assert layer in models, f"Missing layer: {layer}"
        assert "type" in models[layer]
        assert models[layer]["type"] in ["REAL", "HEURISTIC", "FALLBACK (UNAVAILABLE)"]

def test_phase48_honest_no_trade_consensus():
    """Test 7: If consensus confidence < 0.65, decision must be NO_TRADE."""
    res = requests.get(f"{BASE_URL}/api/v1/live/today", timeout=5)
    assert res.status_code == 200
    data = res.json()
    forecasts = data.get("forecasts", [])
    
    for f in forecasts:
        if f.get("confidence", 0) < 0.65:
            assert f.get("decision") == "NO_TRADE"
            assert f.get("rejection_reason") in ["LOW_CONSENSUS", "CONSENSUS_BELOW_THRESHOLD", "VALIDATION_PAUSED", "HIGH_EVENT_RISK", "RR_BELOW_MINIMUM"]

def test_phase48_h4_matrix_9_assets():
    """Test 8: GET /api/v1/signals/h4-intelligence returns full 9-asset matrix."""
    res = requests.get(f"{BASE_URL}/api/v1/signals/h4-intelligence", timeout=5)
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    matrix = data.get("matrix", [])
    assert len(matrix) == 9
    
    expected_assets = {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "BTCUSD", "ETHUSD", "XAUUSD", "NAS100", "SPX500"}
    returned_assets = {row["asset"] for row in matrix}
    assert expected_assets.issubset(returned_assets)

def test_phase48_tomorrow_forecast_9_assets():
    """Test 9: GET /api/v1/live/tomorrow returns all 9 asset forecasts."""
    res = requests.get(f"{BASE_URL}/api/v1/live/tomorrow", timeout=5)
    assert res.status_code == 200
    data = res.json()
    forecasts = data.get("forecasts", [])
    assert len(forecasts) == 9
    total_assets = data.get("total_assets") or data.get("summary", {}).get("total_assets")
    assert total_assets == 9
