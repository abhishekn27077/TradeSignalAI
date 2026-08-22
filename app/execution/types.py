from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"

class Order(BaseModel):
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float | None = None
    status: OrderStatus
    timestamp: datetime

class Trade(BaseModel):
    id: str
    order_id: str
    symbol: str
    side: OrderSide
    price: float
    quantity: float
    timestamp: datetime
    fee: float = 0.0

class Position(BaseModel):
    symbol: str
    quantity: float
    average_entry_price: float
    unrealized_pnl: float = 0.0
