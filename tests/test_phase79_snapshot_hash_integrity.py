"""
tests/test_phase79_snapshot_hash_integrity.py
=============================================
Phase 79: Canonical Market Snapshot Hash Integrity & Empty Payload Defense.

Validates:
1. Deterministic canonical serialization (Part B1).
2. Independent reference hash verification (Part B2): H1 == H2.
3. Empty-payload hash defense (Part B3): Rejects empty payloads and 'e3b0c44298fc...'.
4. Tamper detection:
   - Price tamper
   - Timestamp tamper
   - Provider tamper
   - Asset tamper
   - Bid tamper
   - Ask tamper
   - Timeframe tamper
5. Snapshot immutability (Part B4): Conflicting writes to existing snapshot fail closed.
"""

import pytest
import hashlib
import json
from datetime import datetime, timezone

from app.core.canonical_snapshot_manager import (
    build_canonical_payload,
    compute_snapshot_hash,
    compute_independent_snapshot_hash,
    verify_independent_hash,
    EMPTY_PAYLOAD_SHA256,
    EmptyPayloadHashError,
    SnapshotMutationError,
    CanonicalSnapshotManager,
    LiveAssetMarketSnapshot,
)


def test_empty_payload_hash_defense():
    """Verify that empty payload digest is explicitly rejected."""
    # Digest of empty bytes
    assert hashlib.sha256(b"").hexdigest() == EMPTY_PAYLOAD_SHA256

    # 1. compute_snapshot_hash must reject empty string
    with pytest.raises(EmptyPayloadHashError):
        compute_snapshot_hash("")

    # 2. build_canonical_payload must reject empty dict
    with pytest.raises(EmptyPayloadHashError):
        build_canonical_payload({})

    # 3. compute_independent_snapshot_hash must reject empty dict
    with pytest.raises(EmptyPayloadHashError):
        compute_independent_snapshot_hash({})


def test_deterministic_serialization_and_hash():
    """Verify that canonical serialization is 100% deterministic regardless of dictionary order."""
    data1 = {
        "asset": "EURUSD",
        "provider": "MT5",
        "provider_symbol": "EURUSDm",
        "timestamp_utc": "2026-10-01T12:00:00+00:00",
        "mid_price": 1.085000,
        "bid": 1.084950,
        "ask": 1.085050,
        "spread": 0.000100,
        "volume": 125.0,
        "timeframe": "1H",
        "source_sequence": 42,
    }

    # Same data, reversed dictionary insertion order
    data2 = {
        "source_sequence": 42,
        "volume": 125.0,
        "timeframe": "1H",
        "spread": 0.000100,
        "ask": 1.085050,
        "bid": 1.084950,
        "mid_price": 1.085000,
        "timestamp_utc": "2026-10-01T12:00:00+00:00",
        "provider_symbol": "EURUSDm",
        "provider": "MT5",
        "asset": "EURUSD",
    }

    payload1 = build_canonical_payload(data1)
    payload2 = build_canonical_payload(data2)
    assert payload1 == payload2

    h1 = compute_snapshot_hash(payload1)
    h2 = compute_snapshot_hash(payload2)
    assert h1 == h2
    assert h1 != EMPTY_PAYLOAD_SHA256


def test_independent_hash_verification():
    """Verify production hash H1 equals independent reference hash H2."""
    data = {
        "asset": "BTCUSD",
        "provider": "BINANCE",
        "provider_symbol": "BTCUSDT",
        "timestamp_utc": "2026-10-01T14:07:21.943719+00:00",
        "mid_price": 83794.005,
        "bid": 83794.0,
        "ask": 83794.01,
        "spread": 0.01,
        "volume": 4.05305,
        "timeframe": "1H",
        "source_sequence": 1,
    }

    payload = build_canonical_payload(data)
    h_prod = compute_snapshot_hash(payload)
    h_indep = compute_independent_snapshot_hash(data)

    assert h_prod == h_indep

    snap = LiveAssetMarketSnapshot(
        snapshot_id="SNAP-TEST-BTCUSD",
        asset="BTCUSD",
        provider="BINANCE",
        provider_symbol="BTCUSDT",
        timestamp_utc=data["timestamp_utc"],
        timestamp_ist="2026-10-01T19:37:21.943719+05:30",
        price=data["mid_price"],
        mid_price=data["mid_price"],
        bid=data["bid"],
        ask=data["ask"],
        spread=data["spread"],
        volume=data["volume"],
        timeframe="1H",
        data_age_seconds=0.1,
        provider_status="LIVE",
        source_sequence=1,
        canonical_payload=payload,
        canonical_payload_hash=h_prod,
        market_snapshot_hash=h_prod,
        hash_algorithm="SHA-256",
        is_valid=True,
    )

    assert verify_independent_hash(snap) is True


@pytest.mark.parametrize(
    "tampered_field,tampered_val",
    [
        ("mid_price", 83800.0),
        ("bid", 83790.0),
        ("ask", 83805.0),
        ("timestamp_utc", "2026-10-01T14:07:22.000000+00:00"),
        ("provider", "MT5"),
        ("asset", "ETHUSD"),
        ("timeframe", "15m"),
        ("source_sequence", 2),
    ],
)
def test_snapshot_tamper_detection(tampered_field, tampered_val):
    """Verify that tampering with any field invalidates the cryptographic hash."""
    base_data = {
        "asset": "BTCUSD",
        "provider": "BINANCE",
        "provider_symbol": "BTCUSDT",
        "timestamp_utc": "2026-10-01T14:07:21.943719+00:00",
        "mid_price": 83794.005,
        "bid": 83794.0,
        "ask": 83794.01,
        "spread": 0.01,
        "volume": 4.05305,
        "timeframe": "1H",
        "source_sequence": 1,
    }

    orig_payload = build_canonical_payload(base_data)
    orig_hash = compute_snapshot_hash(orig_payload)

    # Tamper with single field
    tampered_data = dict(base_data)
    tampered_data[tampered_field] = tampered_val

    tampered_payload = build_canonical_payload(tampered_data)
    tampered_hash = compute_snapshot_hash(tampered_payload)

    assert orig_hash != tampered_hash, f"Hash collision or lack of sensitivity on field {tampered_field}"


def test_snapshot_immutability(tmp_path):
    """Verify that attempting to mutate an existing snapshot in the ledger raises SnapshotMutationError."""
    db_file = str(tmp_path / "test_immutability.db")
    mgr = CanonicalSnapshotManager(db_path=db_file)

    data = {
        "asset": "EURUSD",
        "provider": "MT5",
        "provider_symbol": "EURUSD",
        "timestamp_utc": "2026-10-01T12:00:00+00:00",
        "mid_price": 1.085000,
        "bid": 1.084950,
        "ask": 1.085050,
        "spread": 0.000100,
        "volume": 100.0,
        "timeframe": "1H",
        "source_sequence": 1,
    }
    payload = build_canonical_payload(data)
    h = compute_snapshot_hash(payload)

    snap = LiveAssetMarketSnapshot(
        snapshot_id="SNAP-IMMUTABLE-001",
        asset="EURUSD",
        provider="MT5",
        provider_symbol="EURUSD",
        timestamp_utc=data["timestamp_utc"],
        timestamp_ist="2026-10-01T17:30:00+05:30",
        price=1.085,
        mid_price=1.085,
        bid=1.08495,
        ask=1.08505,
        spread=0.0001,
        volume=100.0,
        timeframe="1H",
        data_age_seconds=0.5,
        provider_status="LIVE",
        source_sequence=1,
        canonical_payload=payload,
        canonical_payload_hash=h,
        market_snapshot_hash=h,
        hash_algorithm="SHA-256",
        is_valid=True,
    )

    # Initial write
    mgr._persist_live_snapshot(snap)

    # Idempotent write with exact same fields succeeds
    mgr._persist_live_snapshot(snap)

    # Illegal mutation attempt (different price)
    mutated_snap = LiveAssetMarketSnapshot(
        snapshot_id="SNAP-IMMUTABLE-001",
        asset="EURUSD",
        provider="MT5",
        provider_symbol="EURUSD",
        timestamp_utc=data["timestamp_utc"],
        timestamp_ist="2026-10-01T17:30:00+05:30",
        price=1.095,  # Mutated price
        mid_price=1.095,
        bid=1.08495,
        ask=1.08505,
        spread=0.0001,
        volume=100.0,
        timeframe="1H",
        data_age_seconds=0.5,
        provider_status="LIVE",
        source_sequence=1,
        canonical_payload=payload,
        canonical_payload_hash=h,
        market_snapshot_hash=h,
        hash_algorithm="SHA-256",
        is_valid=True,
    )

    with pytest.raises(SnapshotMutationError):
        mgr._persist_live_snapshot(mutated_snap)
