from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ExecutionOrder:
    """Represents a live order dispatched to a broker."""
    id: str
    broker_id: str
    symbol: str
    direction: str # "BUY" or "SELL"
    order_type: str # "MARKET", "LIMIT", etc.
    quantity: float
    status: str # "PENDING", "SUBMITTED", "PARTIAL_FILL", "FILLED", "REJECTED", "CANCELLED"
    requested_price: float | None = None
    filled_price: float | None = None
    slippage: float | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    error_message: str | None = None
    broker_order_id: str | None = None

@dataclass
class ReconciliationLog:
    """Records the outcome of a reconciliation check."""
    id: str
    status: str # "OK", "MISMATCH"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    mismatches_found: dict[str, Any] = field(default_factory=dict)
