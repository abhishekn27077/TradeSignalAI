from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class RiskModel:
    """Represents a global or asset-specific risk limit."""
    id: str
    limit_type: str  # e.g., "MAX_DAILY_LOSS", "MAX_DRAWDOWN", "MAX_CORRELATION"
    threshold: float
    current_value: float = 0.0
    active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    
@dataclass
class StressTestResult:
    """Records the outcome of a synthetic portfolio shock."""
    id: str
    scenario_name: str
    simulated_drawdown: float
    margin_called: bool
    portfolio_var: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: dict[str, Any] = field(default_factory=dict)
