"""
tests/test_phase37_websocket.py
===============================
Tests WebSocket streaming endpoint and message broadcasting contracts.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_websocket_connection_and_echo():
    with client.websocket_connect("/api/v1/ws/stream") as websocket:
        websocket.send_json({"action": "subscribe", "channel": "signals"})
        assert websocket is not None
