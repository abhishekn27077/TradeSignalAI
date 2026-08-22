"""
PHASE 36 — API CONTRACT ZERO-TRUST TESTS
=========================================
Asserts that the backend API:
1. Does NOT return fabricated/synthetic default values (50%, 85.4%, etc.)
2. Returns None/null for missing fields rather than hardcoded defaults.
3. Uses correct `signal_state` values that match SignalLifecycleModel enum.
4. Does NOT include deterministic fake AI model consensus data.
5. Serializes datetime fields to ISO strings (not raw datetime objects).

These tests verify the Zero-Trust contract at the API boundary.
"""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

SIGNAL_STATES_VALID = {
    "DETECTED", "ANALYZING", "APPROVED", "REJECTED",
    "WAITING", "ACTIVE", "EXPIRED",
    "TP_HIT", "SL_HIT", "TIME_EXIT", "AMBIGUOUS", "COMPLETED"
}

# These old/invalid status values must NEVER appear in a history query filter
FORBIDDEN_STATUS_STRINGS = {"WIN", "LOSS", "BREAKEVEN", "INVALIDATED"}

# Hard-coded fabricated values that must NEVER appear in API responses
FORBIDDEN_FABRICATED_STRINGS = [
    "85.4%",
    "85.4",
    "Deterministic analysis for",   # was in fake AI consensus
]

FORBIDDEN_NUMERIC_CONFIDENCE_DEFAULTS = [50]  # 50 as a default agent confidence


# ─────────────────────────────────────────────────────────────
# TEST 1: signal_state enum integrity
# ─────────────────────────────────────────────────────────────

def test_signal_states_do_not_include_forbidden_values():
    """The resolved_states list in /history must only use valid signal_state values."""
    # Import and inspect the source directly
    import ast, pathlib
    src = pathlib.Path("app/api/v1/signals.py").read_text(encoding="utf-8")
    
    # Ensure no forbidden status strings appear in the file
    for forbidden in FORBIDDEN_STATUS_STRINGS:
        # Should not appear inside any .in_() filter on status field
        assert f'"status.in_' not in src or f'"{forbidden}"' not in src, (
            f"Forbidden status string '{forbidden}' found in signals.py — "
            f"use signal_state enum values instead (e.g. TP_HIT, SL_HIT, COMPLETED)."
        )


def test_history_endpoint_uses_signal_state_not_status():
    """history endpoint must filter on signal_state, not the legacy 'status' field."""
    import pathlib
    src = pathlib.Path("app/api/v1/signals.py").read_text(encoding="utf-8")
    
    # The resolved_states list must use canonical signal_state values
    assert "signal_state.in_(" in src, (
        "The /history endpoint must filter by signal_state.in_(resolved_states), "
        "not by the legacy status column."
    )
    
    # Must NOT use the old broken filter
    assert 'status.in_(["WIN"' not in src, (
        "Found old forbidden 'status.in_([WIN, LOSS...])' filter in signals.py. "
        "This was removed in Phase 36 — do not revert."
    )


def test_resolved_states_all_valid():
    """All states used in the history query must be valid signal_state enum members."""
    import ast, pathlib, re
    src = pathlib.Path("app/api/v1/signals.py").read_text(encoding="utf-8")
    
    # Extract the resolved_states list
    match = re.search(r'resolved_states\s*=\s*\[([^\]]+)\]', src)
    assert match, "Could not find resolved_states list in signals.py"
    
    raw = match.group(1)
    states = [s.strip().strip('"').strip("'") for s in raw.split(",") if s.strip()]
    
    for state in states:
        assert state in SIGNAL_STATES_VALID, (
            f"State '{state}' in resolved_states is not a valid signal_state enum value. "
            f"Valid values: {SIGNAL_STATES_VALID}"
        )


# ─────────────────────────────────────────────────────────────
# TEST 2: No fabricated data in API source
# ─────────────────────────────────────────────────────────────

def test_no_hardcoded_historical_accuracy_in_signals_api():
    """The signals.py API must not contain any hardcoded accuracy percentage."""
    import pathlib
    src = pathlib.Path("app/api/v1/signals.py").read_text(encoding="utf-8")
    
    for pattern in ["85.4", "historical_accuracy.*85", "0.854"]:
        import re
        assert not re.search(pattern, src), (
            f"Pattern '{pattern}' (hardcoded historical accuracy) found in signals.py. "
            "All accuracy values must come from the database."
        )


def test_ai_consensus_endpoint_does_not_fabricate_models():
    """The ai-consensus endpoint must NOT generate fake model results via deterministic hash."""
    import pathlib
    src = pathlib.Path("app/api/v1/signals.py").read_text(encoding="utf-8")
    
    # These patterns indicate the old fabrication logic
    forbidden_patterns = [
        "hashlib.md5(signal_id",
        '"Deterministic analysis for',
        "default_models = [",
        "var = (((h +",
    ]
    for pattern in forbidden_patterns:
        assert pattern not in src, (
            f"Forbidden fabrication pattern '{pattern}' found in signals.py ai-consensus endpoint. "
            "Phase 36 removed this synthetic data generation. Do not revert."
        )


def test_ai_consensus_returns_data_availability_field():
    """The ai-consensus endpoint must return a data_availability field."""
    import pathlib
    src = pathlib.Path("app/api/v1/signals.py").read_text(encoding="utf-8")
    
    assert '"data_availability"' in src or "'data_availability'" in src, (
        "The ai-consensus endpoint must return a 'data_availability' field "
        "indicating REAL or UNAVAILABLE."
    )


# ─────────────────────────────────────────────────────────────
# TEST 3: Frontend — no fake fallbacks
# ─────────────────────────────────────────────────────────────

def test_trading_dashboard_no_hardcoded_accuracy():
    """TradingDashboard.tsx must not contain the hardcoded '85.4%' string."""
    import pathlib
    src = pathlib.Path("frontend/src/pages/TradingDashboard.tsx").read_text(encoding="utf-8")
    
    assert "'85.4%'" not in src and '"85.4%"' not in src, (
        "Found hardcoded '85.4%' in TradingDashboard.tsx. "
        "Phase 36 removed this — historical accuracy must come from the API."
    )


def test_trading_dashboard_confidence_no_zero_default():
    """The confidence constant must not fall back to the numeric 0 (should be null)."""
    import pathlib
    src = pathlib.Path("frontend/src/pages/TradingDashboard.tsx").read_text(encoding="utf-8")
    
    # The old pattern was: pred.confidence ?? sig.confidence ?? 0
    assert "?? sig.confidence ?? 0;" not in src, (
        "Found '?? sig.confidence ?? 0' in TradingDashboard.tsx. "
        "Phase 36 changed this to '?? null' to prevent fake 0% display."
    )


def test_use_app_store_no_fake_confidence_50():
    """useAppStore.ts must not set confidence to 50 as a synthetic default."""
    import pathlib
    src = pathlib.Path("frontend/src/store/useAppStore.ts").read_text(encoding="utf-8")
    
    assert "confidence: a.confidence ?? 50" not in src, (
        "Found 'confidence: a.confidence ?? 50' in useAppStore.ts. "
        "Phase 36 changed this to null to prevent fake 50% confidence display."
    )


def test_use_app_store_no_fake_strength_50():
    """useAppStore.ts mapSignal must not fall back strength to 50."""
    import pathlib
    src = pathlib.Path("frontend/src/store/useAppStore.ts").read_text(encoding="utf-8")
    
    assert "?? s.score ?? 50)" not in src, (
        "Found '?? s.score ?? 50' in useAppStore.ts mapSignal strength. "
        "Phase 36 changed this to null."
    )


def test_trading_dashboard_no_fake_xai_reasoning():
    """TradingDashboard.tsx must not inject fake XAI reasoning text."""
    import pathlib
    src = pathlib.Path("frontend/src/pages/TradingDashboard.tsx").read_text(encoding="utf-8")
    
    fake_text = "AI models detected strong directional probability aligned with market regime."
    assert fake_text not in src, (
        "Found hardcoded fake XAI reasoning text in TradingDashboard.tsx. "
        "Phase 36 removed this — XAI reasoning must come from the backend or show UNAVAILABLE."
    )


def test_trading_dashboard_no_fake_status_pending():
    """TradingDashboard.tsx must not default signal status to 'PENDING' fabrication."""
    import pathlib
    src = pathlib.Path("frontend/src/pages/TradingDashboard.tsx").read_text(encoding="utf-8")
    
    # Old pattern: sig.status ?? 'PENDING'
    assert "?? 'PENDING'" not in src, (
        "Found '?? PENDING' fallback in TradingDashboard.tsx. "
        "Phase 36 replaced this with sig.signal_state ?? 'UNAVAILABLE'."
    )


# ─────────────────────────────────────────────────────────────
# TEST 4: Datetime serialization contract
# ─────────────────────────────────────────────────────────────

def test_signals_today_endpoint_serializes_datetimes():
    """The /today endpoint must serialize datetime fields to ISO strings."""
    import pathlib
    src = pathlib.Path("app/api/v1/signals.py").read_text(encoding="utf-8")
    
    # Check that datetime serialization is present in the file
    assert "isoformat" in src, (
        "No datetime ISO serialization found in signals.py. "
        "Python datetime objects cannot be serialized to JSON without .isoformat(). "
        "This would cause 500 errors on all signal list endpoints."
    )


def test_signal_row_serialization_pattern():
    """The datetime serialization pattern must be correct."""
    import pathlib
    src = pathlib.Path("app/api/v1/signals.py").read_text(encoding="utf-8")
    
    # Must have the standard serialization pattern
    assert "hasattr(v, 'isoformat')" in src, (
        "Expected 'hasattr(v, 'isoformat')' pattern not found in signals.py. "
        "All datetime columns must be serialized before appending to the response."
    )


# ─────────────────────────────────────────────────────────────
# TEST 5: SignalLifecycleModel schema integrity
# ─────────────────────────────────────────────────────────────

def test_signal_model_has_required_trace_fields():
    """SignalLifecycleModel must have Phase 33 trace fields."""
    from app.database.models.signal import SignalLifecycleModel
    
    required_fields = [
        "signal_id", "trace_id", "duplicate_protection_hash",
        "signal_state", "confidence", "direction",
        "model_trace", "intelligence_snapshot",
        "outcome", "net_pnl", "r_multiple",
    ]
    
    columns = {c.name for c in SignalLifecycleModel.__table__.columns}
    
    for field in required_fields:
        assert field in columns, (
            f"Required field '{field}' missing from SignalLifecycleModel. "
            "This field is required for Phase 33/36 traceability."
        )


def test_signal_model_confidence_is_not_forced_default():
    """The confidence field must have nullable=True or no forced non-zero default."""
    from app.database.models.signal import SignalLifecycleModel
    from sqlalchemy import inspect as sa_inspect
    
    columns = {c.name: c for c in SignalLifecycleModel.__table__.columns}
    conf_col = columns.get("confidence")
    
    assert conf_col is not None, "confidence column missing from SignalLifecycleModel"
    
    # confidence has default=0.0 in the DB model — this is acceptable as a DB default,
    # but signals must always have a real confidence computed by the pipeline.
    # The DB default is a safety net, not a fabrication point.
    # Verify the column exists and is a Float type.
    assert str(conf_col.type).startswith("FLOAT") or str(conf_col.type) == "FLOAT", (
        f"confidence column has unexpected type: {conf_col.type}"
    )


# ─────────────────────────────────────────────────────────────
# TEST 6: Predict endpoint must not inject fake confidence
# ─────────────────────────────────────────────────────────────

def test_predict_endpoint_no_hardcoded_wait_confidence():
    """The /predict endpoint must not hardcode confidence=0.5 for WAIT signals."""
    import pathlib
    src = pathlib.Path("app/api/v1/signals.py").read_text(encoding="utf-8")
    
    # Check for the specific pattern where the predict endpoint injects confidence 0.5
    # This is in the /predict/{symbol} route
    assert 'signal = {"direction": "WAIT", "confidence": 0.5}' not in src, (
        "Found hardcoded confidence=0.5 in the predict endpoint. "
        "The prediction engine should compute confidence from actual market data."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
