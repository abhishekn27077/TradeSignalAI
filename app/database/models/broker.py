from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class BrokerAccount:
    """Represents a configured broker API connection."""
    id: str
    name: str # e.g., "Binance Main", "Alpaca Paper"
    adapter_type: str # "BINANCE", "ALPACA", "MT5", "DUMMY"
    api_key: str # In production this MUST be encrypted
    api_secret: str # In production this MUST be encrypted
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    
@dataclass
class BrokerMetric:
    """Stores health metrics like latency for a specific broker."""
    broker_id: str
    status: str = "CONNECTED" # "CONNECTED", "DISCONNECTED", "ERROR"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    latency_ms: float = 0.0
