from abc import ABC, abstractmethod

from .types import Order, OrderSide, OrderType, Position


class BaseExecutor(ABC):
    """
    Abstract base class for all execution brokers.
    Handles the submission and tracking of orders, and account positions.
    """

    @abstractmethod
    async def submit_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float | None = None
    ) -> Order:
        """
        Submit a new order.
        """

    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Cancel an existing open order.
        """

    @abstractmethod
    async def get_open_orders(self, symbol: str | None = None) -> list[Order]:
        """
        Fetch all open orders, optionally filtered by symbol.
        """

    @abstractmethod
    async def get_position(self, symbol: str) -> Position:
        """
        Get the current position for a symbol.
        """
