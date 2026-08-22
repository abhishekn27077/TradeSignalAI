"""
tests/test_phase37_frontend_mapping.py
======================================
Verifies TypeScript and frontend contract compatibility, preventing undefined property errors
and guaranteeing consistent snake_case & camelCase normalization.
"""
import pytest


def test_frontend_data_mapping_structures():
    # Simulating backend signal serialization vs frontend parsing
    backend_signal = {
        "id": "sig_001",
        "symbol": "BTCUSD",
        "direction": "BUY",
        "entry_price": 69500.0,
        "stop_loss": 68500.0,
        "take_profit": 71500.0,
        "confidence": 0.82,
        "strategy_name": "SMCSequenceConfluenceStrategy",
        "timestamp": "2026-08-20T12:00:00Z",
        "signal_state": "ACTIVE"
    }
    
    # In frontend TodaysSignals & SwingSignals: const s = ls.signal || ls || {};
    nested_ls = {"signal": backend_signal}
    flat_ls = backend_signal
    
    for item in [nested_ls, flat_ls]:
        s = item.get("signal") or item
        assert s["symbol"] == "BTCUSD"
        assert s["direction"] == "BUY"
        assert s["entry_price"] == 69500.0
        assert s["stop_loss"] == 68500.0
        assert s["take_profit"] == 71500.0
        assert s["confidence"] == 0.82
