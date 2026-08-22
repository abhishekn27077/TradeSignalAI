from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MemoryRecord:
    """A generic record stored in the memory system (e.g., historical event, user note)."""
    id: str
    type: str  # "TRADE", "NEWS", "STRATEGY", "LESSON"
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None

@dataclass
class KnowledgeNode:
    """A node in the Knowledge Graph (e.g., Asset: BTC-USD)."""
    id: str
    label: str  # "Asset", "Strategy", "Agent", "NewsEvent"
    properties: dict[str, Any] = field(default_factory=dict)

@dataclass
class KnowledgeEdge:
    """A directional relationship between two KnowledgeNodes."""
    id: str
    source_id: str
    target_id: str
    relation_type: str  # "USED_STRATEGY", "CAUSED_BY"
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)

@dataclass
class Lesson:
    """A specific actionable rule or insight learned by the system."""
    id: str
    source_trade_id: str | None
    summary: str
    actionable_rule: str
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)
