from datetime import datetime
from enum import Enum

from pydantic import BaseModel


# ==========================================
# ENUMERATIONS
# ==========================================
class Timeframe(str, Enum):
    TICK = "TICK"
    M1 = "1m"
    M3 = "3m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1H"
    H4 = "4H"
    D1 = "1D"
    W1 = "1W"
    MN1 = "1M"

class AssetClass(str, Enum):
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"
    STOCK = "STOCK"
    COMMODITY = "COMMODITY"
    INDEX = "INDEX"

class ProviderStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"

class MarketSession(str, Enum):
    NEW_YORK = "NEW_YORK"
    LONDON = "LONDON"
    TOKYO = "TOKYO"
    SYDNEY = "SYDNEY"
    CRYPTO_24_7 = "CRYPTO_24_7"

# ==========================================
# CORE DATA MODELS
# ==========================================
class Tick(BaseModel):
    symbol: str
    price: float
    timestamp: datetime
    volume: float = 0.0

class BidAsk(BaseModel):
    symbol: str
    bid_price: float
    ask_price: float
    bid_volume: float = 0.0
    ask_volume: float = 0.0
    timestamp: datetime

    @property
    def spread(self) -> float:
        return self.ask_price - self.bid_price

class Candle(BaseModel):
    symbol: str
    timeframe: Timeframe
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class OrderBookLevel(BaseModel):
    price: float
    quantity: float

class OrderBook(BaseModel):
    symbol: str
    timestamp: datetime
    bids: list[OrderBookLevel]
    asks: list[OrderBookLevel]

# ==========================================
# METADATA MODELS
# ==========================================
class SymbolInfo(BaseModel):
    symbol: str
    asset_class: AssetClass
    base_currency: str
    quote_currency: str
    exchange: str
    price_precision: int
    quantity_precision: int
    pip_size: float | None = None
    market_session: MarketSession = MarketSession.CRYPTO_24_7
    is_active: bool = True

class ProviderMetrics(BaseModel):
    provider_name: str
    status: ProviderStatus
    latency_ms: float
    error_count: int
    last_health_check: datetime

class ReplayConfig(BaseModel):
    symbol: str
    start_time: datetime
    end_time: datetime
    speed_multiplier: float = 1.0 # 1.0 = real-time simulation
