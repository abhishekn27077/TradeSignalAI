"""
app/core/signal_event_logger.py
===============================
Structured Observability & Lifecycle Event Logger for TradeSignalAI-v3 (Phase 65).

Emits immutable structured event telemetry for:
- SIGNAL_GENERATED
- SIGNAL_REJECTED
- SIGNAL_LIVE
- SIGNAL_RESOLVING
- SIGNAL_WON
- SIGNAL_LOST
- SIGNAL_TIME_EXIT
- SIGNAL_AMBIGUOUS
- CAUSAL_VIOLATION
- STALE_DATA_BLOCKED
- DUPLICATE_SIGNAL_BLOCKED
"""

from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger("signal_lifecycle_telemetry")


class SignalEventLogger:
    """
    Records immutable structured lifecycle and causal validation events.
    """

    def __init__(self):
        self._event_log: List[Dict[str, Any]] = []

    def emit_event(
        self,
        event_type: str,
        signal_id: Optional[str] = None,
        asset: Optional[str] = None,
        timeframe: Optional[str] = None,
        snapshot_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Emits and records a structured lifecycle event.
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "signal_id": signal_id or "N/A",
            "asset": asset or "N/A",
            "timeframe": timeframe or "N/A",
            "snapshot_id": snapshot_id or "SNAP-CANONICAL-LIVE",
            "git_commit": "94d5efa",
            "engine_version": "65.0.0-canonical",
            "payload": payload or {},
        }
        self._event_log.append(event)
        logger.info(f"[{event_type}] {signal_id or asset}: {json.dumps(event.get('payload', {}))}")
        return event

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Returns recent structured lifecycle events."""
        return self._event_log[-limit:]


signal_event_logger = SignalEventLogger()
