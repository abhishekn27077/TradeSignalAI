from abc import ABC, abstractmethod
from typing import Any

from app.database.models.execution import ExecutionOrder


class IBrokerAdapter(ABC):
    """Universal interface that all physical broker integrations must implement."""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection / authenticate."""

    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection."""
        
    @abstractmethod
    async def check_health(self) -> dict[str, Any]:
        """Return latency and connection status."""
        
    @abstractmethod
    async def submit_order(self, order: ExecutionOrder) -> dict[str, Any]:
        """Submit a live order to the exchange. Returns broker response dict."""
        
    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> bool:
        """Cancel an open order."""
        
    @abstractmethod
    async def get_open_positions(self) -> list[dict[str, Any]]:
        """Return normalized open positions from the broker."""
        
    @abstractmethod
    async def get_account_balance(self) -> dict[str, Any]:
        """Return normalized account balances (equity, free cash, margin)."""
