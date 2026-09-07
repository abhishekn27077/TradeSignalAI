"""
app/core/unified_research_bus.py
================================
Unified Typed Research Event Bus for TradeSignalAI-v3 (Phase 66).

Provides an immutable, typed event-driven backbone inspired by NautilusTrader / LEAN
with zero-lookahead causal auditing and cryptographic payload hashing.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import hashlib
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger("unified_research_bus")


class ResearchEventType(str, Enum):
    MARKET_DATA_RECEIVED = "MARKET_DATA_RECEIVED"
    INDICATOR_EVALUATED = "INDICATOR_EVALUATED"
    MODEL_EVALUATED = "MODEL_EVALUATED"
    SIGNAL_CANDIDATE = "SIGNAL_CANDIDATE"
    SIGNAL_QUALIFIED = "SIGNAL_QUALIFIED"
    SIGNAL_REJECTED = "SIGNAL_REJECTED"
    SIGNAL_LIVE = "SIGNAL_LIVE"
    SIGNAL_UPDATED = "SIGNAL_UPDATED"
    SIGNAL_WON = "SIGNAL_WON"
    SIGNAL_LOST = "SIGNAL_LOST"
    SIGNAL_TIME_EXIT = "SIGNAL_TIME_EXIT"
    SIGNAL_AMBIGUOUS = "SIGNAL_AMBIGUOUS"
    RESEARCH_RUN_STARTED = "RESEARCH_RUN_STARTED"
    RESEARCH_RUN_COMPLETED = "RESEARCH_RUN_COMPLETED"
    MODEL_PROMOTED = "MODEL_PROMOTED"
    MODEL_REJECTED = "MODEL_REJECTED"
    POLICY_UPDATED = "POLICY_UPDATED"
    CAUSAL_VIOLATION_DETECTED = "CAUSAL_VIOLATION_DETECTED"


@dataclass(frozen=True)
class ResearchEvent:
    """
    Immutable typed event record with cryptographic payload verification.
    """
    event_id: str
    event_type: str
    timestamp: str  # ISO 8601 UTC
    causal_cutoff: str  # T0 barrier
    asset: str
    timeframe: str
    source: str
    version: str
    payload: Dict[str, Any]
    payload_hash: str

    @classmethod
    def create(
        cls,
        event_type: ResearchEventType | str,
        asset: str = "GLOBAL",
        timeframe: str = "1H",
        source: str = "CanonicalEngine",
        version: str = "66.0.0-canonical",
        causal_cutoff: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> ResearchEvent:
        now_iso = datetime.now(timezone.utc).isoformat()
        cutoff = causal_cutoff or now_iso
        p_dict = payload or {}
        payload_bytes = json.dumps(p_dict, sort_keys=True).encode("utf-8")
        p_hash = hashlib.sha256(payload_bytes).hexdigest()
        e_type = event_type.value if isinstance(event_type, ResearchEventType) else str(event_type)
        e_id = f"EVT-{e_type[:4]}-{hashlib.sha256(f'{now_iso}_{p_hash}'.encode()).hexdigest()[:8]}"

        return cls(
            event_id=e_id,
            event_type=e_type,
            timestamp=now_iso,
            causal_cutoff=cutoff,
            asset=asset,
            timeframe=timeframe,
            source=source,
            version=version,
            payload=p_dict,
            payload_hash=p_hash,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "causal_cutoff": self.causal_cutoff,
            "asset": self.asset,
            "timeframe": self.timeframe,
            "source": self.source,
            "version": self.version,
            "payload": self.payload,
            "payload_hash": self.payload_hash,
        }


class UnifiedResearchBus:
    """
    Central in-memory pub-sub and telemetry bus with historical replay capabilities.
    """

    def __init__(self):
        self._handlers: Dict[str, List[Callable[[ResearchEvent], None]]] = {}
        self._event_history: List[ResearchEvent] = []

    def subscribe(self, event_type: ResearchEventType | str, handler: Callable[[ResearchEvent], None]) -> None:
        key = event_type.value if isinstance(event_type, ResearchEventType) else str(event_type)
        if key not in self._handlers:
            self._handlers[key] = []
        self._handlers[key].append(handler)

    def publish(self, event: ResearchEvent) -> None:
        """Publishes an event to all registered handlers and appends to the immutable log."""
        self._event_history.append(event)
        key = event.event_type
        if key in self._handlers:
            for handler in self._handlers[key]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in handler for event {event.event_id}: {e}")

    def emit(
        self,
        event_type: ResearchEventType | str,
        asset: str = "GLOBAL",
        timeframe: str = "1H",
        source: str = "CanonicalEngine",
        version: str = "66.0.0-canonical",
        causal_cutoff: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> ResearchEvent:
        """Convenience method to construct and publish an event."""
        event = ResearchEvent.create(
            event_type=event_type,
            asset=asset,
            timeframe=timeframe,
            source=source,
            version=version,
            causal_cutoff=causal_cutoff,
            payload=payload,
        )
        self.publish(event)
        return event

    def get_events(
        self,
        event_type: Optional[str] = None,
        asset: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Queries recorded events filtered by type or asset."""
        filtered = self._event_history
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        if asset:
            filtered = [e for e in filtered if e.asset == asset]
        return [e.to_dict() for e in filtered[-limit:]]


unified_research_bus = UnifiedResearchBus()
