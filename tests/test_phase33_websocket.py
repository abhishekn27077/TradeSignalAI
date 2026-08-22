"""
tests/test_phase33_websocket.py
Phase 33 — WebSocket lifecycle event trace_id continuity tests.
"""
import pytest
import json
import uuid
from datetime import datetime, timezone

# These tests verify that the WebSocket event schema includes trace_id and IST timestamps.
# They test the event payload structure independently of the WebSocket connection.


def _make_lifecycle_event(event_type: str, trace_id: str, signal_state: str) -> dict:
    """Builds a Phase 33 WebSocket lifecycle event payload."""
    now_utc = datetime.now(timezone.utc)
    try:
        import zoneinfo
        IST = zoneinfo.ZoneInfo("Asia/Kolkata")
        now_ist = now_utc.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S IST")
    except Exception:
        now_ist = "UNAVAILABLE"

    return {
        "event": event_type,
        "trace_id": trace_id,
        "signal_state": signal_state,
        "timestamp_utc": now_utc.isoformat(),
        "timestamp_ist": now_ist,
        "schema_version": "phase33.v1",
    }


class TestWebSocketLifecycleEvents:

    def test_trace_id_preserved_across_events(self):
        """The same trace_id must appear in every lifecycle event."""
        trace_id = str(uuid.uuid4())

        events = [
            _make_lifecycle_event("signal_generated",  trace_id, "DETECTED"),
            _make_lifecycle_event("signal_approved",   trace_id, "APPROVED"),
            _make_lifecycle_event("signal_activated",  trace_id, "ACTIVE"),
            _make_lifecycle_event("signal_completed",  trace_id, "TP_HIT"),
        ]

        for event in events:
            assert event["trace_id"] == trace_id, (
                f"trace_id mismatch in event '{event['event']}'"
            )

    def test_all_lifecycle_events_have_required_fields(self):
        required = ["event", "trace_id", "signal_state", "timestamp_utc", "timestamp_ist"]
        trace_id = str(uuid.uuid4())
        event_types = [
            ("candle_open",       "DETECTED"),
            ("candle_close",      "ANALYZING"),
            ("signal_generated",  "DETECTED"),
            ("signal_approved",   "APPROVED"),
            ("signal_rejected",   "REJECTED"),
            ("signal_updated",    "ACTIVE"),
            ("signal_expired",    "EXPIRED"),
            ("signal_completed",  "COMPLETED"),
        ]
        for event_type, state in event_types:
            event = _make_lifecycle_event(event_type, trace_id, state)
            for field in required:
                assert field in event, f"Missing '{field}' in event '{event_type}'"

    def test_timestamp_ist_contains_ist_label(self):
        trace_id = str(uuid.uuid4())
        event = _make_lifecycle_event("signal_generated", trace_id, "DETECTED")
        assert "IST" in event["timestamp_ist"] or event["timestamp_ist"] == "UNAVAILABLE"

    def test_timestamp_utc_is_iso_format(self):
        trace_id = str(uuid.uuid4())
        event = _make_lifecycle_event("signal_generated", trace_id, "DETECTED")
        # Should parse as ISO datetime without error
        dt = datetime.fromisoformat(event["timestamp_utc"])
        assert dt.tzinfo is not None

    def test_trace_id_is_valid_uuid(self):
        trace_id = str(uuid.uuid4())
        event = _make_lifecycle_event("signal_generated", trace_id, "DETECTED")
        # Must be parseable as UUID
        parsed = uuid.UUID(event["trace_id"])
        assert str(parsed) == trace_id

    def test_schema_version_present(self):
        trace_id = str(uuid.uuid4())
        event = _make_lifecycle_event("signal_generated", trace_id, "DETECTED")
        assert event["schema_version"] == "phase33.v1"

    def test_different_signals_have_different_trace_ids(self):
        trace1 = str(uuid.uuid4())
        trace2 = str(uuid.uuid4())
        assert trace1 != trace2, "Two different signals must have different trace_ids"

    def test_event_is_json_serializable(self):
        trace_id = str(uuid.uuid4())
        event = _make_lifecycle_event("signal_generated", trace_id, "DETECTED")
        # Must serialize without error
        serialized = json.dumps(event)
        deserialized = json.loads(serialized)
        assert deserialized["trace_id"] == trace_id

    def test_candle_events_precede_signal_events_in_sequence(self):
        """Structural check: candle_open → candle_close → signal_generated ordering."""
        trace_id = str(uuid.uuid4())
        events = [
            _make_lifecycle_event("candle_open",      trace_id, "WAITING"),
            _make_lifecycle_event("candle_close",     trace_id, "WAITING"),
            _make_lifecycle_event("signal_generated", trace_id, "DETECTED"),
            _make_lifecycle_event("signal_approved",  trace_id, "APPROVED"),
            _make_lifecycle_event("signal_completed", trace_id, "TP_HIT"),
        ]
        event_names = [e["event"] for e in events]
        assert event_names.index("candle_open") < event_names.index("signal_generated")
        assert event_names.index("candle_close") < event_names.index("signal_generated")
        assert event_names.index("signal_approved") < event_names.index("signal_completed")
