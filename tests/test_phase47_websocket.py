"""
Phase 47 — Test Suite for WebSocket Connection, Handshake & Heartbeat.

Verifies:
  - Connection to /api/v1/ws/stream
  - Initial system health broadcast on connect
  - Ping / Pong heartbeat response
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_websocket_stream_handshake_and_heartbeat():
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/stream") as websocket:
        # Message 1: Connected event
        msg1 = websocket.receive_json()
        assert msg1.get("event") == "connected"

        # Message 2: Initial system health broadcast
        msg2 = websocket.receive_json()
        assert msg2.get("event") == "system_health"

        # Send ping heartbeat
        websocket.send_json({"action": "ping"})
        response = websocket.receive_json()
        assert response.get("event") == "pong"
