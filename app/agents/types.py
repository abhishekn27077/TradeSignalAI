from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"

class AgentRole(str, Enum):
    CHIEF_TRADER = "CHIEF_TRADER"
    MARKET_ANALYST = "MARKET_ANALYST"
    TECHNICAL_ANALYST = "TECHNICAL_ANALYST"
    NEWS_ANALYST = "NEWS_ANALYST"
    RISK_MANAGER = "RISK_MANAGER"

class ConsensusStatus(str, Enum):
    PENDING = "PENDING"
    DEBATING = "DEBATING"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"

class ToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, Any]

class DecisionOutput(BaseModel):
    agent_id: str
    role: AgentRole
    signal: Signal
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    supporting_agents: list[str] = []
    rejected_opinions: list[str] = []
    risk_score: float = Field(0.0, ge=0.0, le=1.0)
    market_summary: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConsensusResult(BaseModel):
    symbol: str
    final_signal: Signal
    overall_confidence: float
    chief_decision: DecisionOutput
    individual_decisions: list[DecisionOutput]
    status: ConsensusStatus
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
