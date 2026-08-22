from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class SentimentCategory(str, Enum):
    VERY_BULLISH = "VERY_BULLISH"
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    VERY_BEARISH = "VERY_BEARISH"

class AssetClass(str, Enum):
    FOREX = "FOREX"
    CRYPTO = "CRYPTO"
    STOCKS = "STOCKS"
    INDICES = "INDICES"
    COMMODITIES = "COMMODITIES"
    BONDS = "BONDS"

class ImpactScore(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"

class ProcessedNewsItem(BaseModel):
    """
    Standardized format required by the Phase 6 instructions.
    Every processed news item MUST follow this schema.
    """
    id: str
    title: str
    summary: str
    source: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    category: str
    affected_assets: list[str] = []
    
    sentiment: SentimentCategory
    impact_score: ImpactScore
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    keywords: list[str] = []
    named_entities: list[str] = []
    
    economic_event: str | None = None
    reasoning: str
