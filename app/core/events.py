"""
app/core/events.py
==================
Typed Domain Event Model for TradeSignalAI-v3.

Benchmarked against NautilusTrader and QuantConnect LEAN event-sourcing architectures.
Provides strongly-typed, immutable event structures with unique event IDs, UTC timestamps,
causation tracing, and dictionary serialization.

Events:
- MarketDataReceived
- CandleClosed
- SignalGenerated
- SignalRejected
- OrderCreated
- OrderSubmitted
- OrderAccepted
- OrderRejected
- OrderFilled
- PositionOpened
- PositionChanged
- PositionClosed
- ReconciliationMismatch
- RiskLock
- DriftDetected
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import uuid
from typing import Dict, Any, Optional


def _generate_event_id() -> str:
    return f"EVT-{uuid.uuid4().hex[:12]}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class BaseEvent:
    event_id: str = field(default_factory=_generate_event_id)
    timestamp_utc: str = field(default_factory=_utc_now_iso)
    causation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── Market Data Events ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MarketDataReceived(BaseEvent):
    event_type: str = "MarketDataReceived"
    symbol: str = ""
    timeframe: str = ""
    price: float = 0.0
    volume: float = 0.0
    quote_time: str = ""


@dataclass(frozen=True)
class CandleClosed(BaseEvent):
    event_type: str = "CandleClosed"
    symbol: str = ""
    timeframe: str = ""
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    candle_time: str = ""


# ── Signal Events ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SignalGenerated(BaseEvent):
    event_type: str = "SignalGenerated"
    signal_id: str = ""
    asset: str = ""
    timeframe: str = ""
    direction: str = ""  # "BUY", "SELL", "WAIT"
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    confidence: float = 0.0
    strategy_name: str = ""
    snapshot_hash: str = ""


@dataclass(frozen=True)
class SignalRejected(BaseEvent):
    event_type: str = "SignalRejected"
    signal_id: str = ""
    asset: str = ""
    reason: str = ""
    filter_name: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


# ── Order Lifecycle Events ────────────────────────────────────────────────────

@dataclass(frozen=True)
class OrderCreated(BaseEvent):
    event_type: str = "OrderCreated"
    order_id: str = ""
    signal_id: str = ""
    symbol: str = ""
    side: str = ""  # "BUY", "SELL"
    order_type: str = "MARKET"  # "MARKET", "LIMIT", "STOP"
    quantity: float = 0.0
    requested_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0


@dataclass(frozen=True)
class OrderSubmitted(BaseEvent):
    event_type: str = "OrderSubmitted"
    order_id: str = ""
    symbol: str = ""
    side: str = ""
    order_type: str = "MARKET"
    quantity: float = 0.0
    price: Optional[float] = None
    broker: str = "PAPER"


@dataclass(frozen=True)
class OrderAccepted(BaseEvent):
    event_type: str = "OrderAccepted"
    order_id: str = ""
    broker_order_id: str = ""
    symbol: str = ""
    side: str = ""
    quantity: float = 0.0
    price: Optional[float] = None


@dataclass(frozen=True)
class OrderRejected(BaseEvent):
    event_type: str = "OrderRejected"
    order_id: str = ""
    symbol: str = ""
    reason: str = ""
    code: str = "REJECTED"


@dataclass(frozen=True)
class OrderFilled(BaseEvent):
    event_type: str = "OrderFilled"
    order_id: str = ""
    broker_order_id: str = ""
    symbol: str = ""
    side: str = ""
    fill_price: float = 0.0
    fill_quantity: float = 0.0
    cumulative_quantity: float = 0.0
    remaining_quantity: float = 0.0
    fee: float = 0.0
    slippage: float = 0.0
    is_partial: bool = False


# ── Position Events ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PositionOpened(BaseEvent):
    event_type: str = "PositionOpened"
    position_id: str = ""
    symbol: str = ""
    side: str = ""
    quantity: float = 0.0
    entry_price: float = 0.0


@dataclass(frozen=True)
class PositionChanged(BaseEvent):
    event_type: str = "PositionChanged"
    position_id: str = ""
    symbol: str = ""
    side: str = ""
    new_quantity: float = 0.0
    old_quantity: float = 0.0
    average_price: float = 0.0
    realized_pnl: float = 0.0


@dataclass(frozen=True)
class PositionClosed(BaseEvent):
    event_type: str = "PositionClosed"
    position_id: str = ""
    symbol: str = ""
    side: str = ""
    exit_price: float = 0.0
    exit_quantity: float = 0.0
    realized_pnl: float = 0.0
    reason: str = ""  # "TP_HIT", "SL_HIT", "TIME_EXIT", "MANUAL"


# ── Governance & Risk Events ──────────────────────────────────────────────────

@dataclass(frozen=True)
class ReconciliationMismatch(BaseEvent):
    event_type: str = "ReconciliationMismatch"
    symbol: str = ""
    mismatch_type: str = ""  # "QUANTITY_MISMATCH", "MISSING_INTERNAL", "MISSING_EXTERNAL", "LEDGER_DESYNC"
    internal_qty: Optional[float] = None
    external_qty: Optional[float] = None
    ledger_qty: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskLock(BaseEvent):
    event_type: str = "RiskLock"
    reason: str = ""
    triggered_by: str = ""
    current_metric: float = 0.0
    threshold_metric: float = 0.0
    lock_level: str = "HALT_NEW_TRADES"  # "HALT_NEW_TRADES", "EMERGENCY_FLATTEN"


@dataclass(frozen=True)
class DriftDetected(BaseEvent):
    event_type: str = "DriftDetected"
    model_id: str = ""
    drift_metric: str = ""
    statistic: float = 0.0
    p_value: float = 0.0
    threshold: float = 0.0
    feature_name: Optional[str] = None
