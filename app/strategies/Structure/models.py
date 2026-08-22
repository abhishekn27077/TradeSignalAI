from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any


class SwingType(str, Enum):
    SWING_HIGH = "SWING_HIGH"
    SWING_LOW = "SWING_LOW"


class StructureType(str, Enum):
    HIGHER_HIGH = "HH"
    HIGHER_LOW = "HL"
    LOWER_HIGH = "LH"
    LOWER_LOW = "LL"
    BULLISH_BOS = "BULLISH_BOS"
    BEARISH_BOS = "BEARISH_BOS"
    BULLISH_CHOCH = "BULLISH_CHOCH"
    BEARISH_CHOCH = "BEARISH_CHOCH"
    BULLISH_MSB = "BULLISH_MSB"
    BEARISH_MSB = "BEARISH_MSB"


class Direction(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


@dataclass
class SwingPoint:
    asset: str
    timeframe: str
    index: int
    timestamp_utc: datetime
    timestamp_ist: str
    price: float
    swing_type: SwingType
    confirmed: bool = True
    volume: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "timeframe": self.timeframe,
            "index": self.index,
            "timestamp_utc": self.timestamp_utc.isoformat() if isinstance(self.timestamp_utc, datetime) else str(self.timestamp_utc),
            "timestamp_ist": self.timestamp_ist,
            "price": float(self.price),
            "swing_type": self.swing_type.value if hasattr(self.swing_type, 'value') else str(self.swing_type),
            "confirmed": self.confirmed,
            "volume": float(self.volume),
        }


@dataclass
class StructureEvent:
    asset: str
    timeframe: str
    event_type: StructureType
    direction: Direction
    price: float
    timestamp_utc: datetime
    timestamp_ist: str
    source_candle: int
    confirmation_candle: int
    strength: float
    invalidation_price: float
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "timeframe": self.timeframe,
            "event_type": self.event_type.value if hasattr(self.event_type, 'value') else str(self.event_type),
            "direction": self.direction.value if hasattr(self.direction, 'value') else str(self.direction),
            "price": float(self.price),
            "timestamp_utc": self.timestamp_utc.isoformat() if isinstance(self.timestamp_utc, datetime) else str(self.timestamp_utc),
            "timestamp_ist": self.timestamp_ist,
            "source_candle": self.source_candle,
            "confirmation_candle": self.confirmation_candle,
            "strength": float(self.strength),
            "invalidation_price": float(self.invalidation_price),
            "details": self.details,
        }
