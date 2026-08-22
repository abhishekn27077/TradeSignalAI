from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PortfolioSnapshot:
    """A point-in-time record of the portfolio state."""
    id: str
    account_id: str
    equity: float
    cash: float
    gross_exposure: float
    net_exposure: float
    margin_used: float
    leverage: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    allocations: dict[str, float] = field(default_factory=dict)  # Asset to Exposure % mapping
