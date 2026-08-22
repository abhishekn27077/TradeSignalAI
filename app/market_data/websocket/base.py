from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any


class BaseWebsocketClient(ABC):
    """
    Abstract base class for all WebSocket data stream clients.
    """

    def __init__(self):
        self._callbacks = []

    def register_callback(self, callback: Callable[[Any], Awaitable[None]]):
        """
        Register an async callback function to handle incoming websocket messages.
        """
        self._callbacks.append(callback)

    @abstractmethod
    async def connect(self):
        """
        Establish the websocket connection.
        """

    @abstractmethod
    async def disconnect(self):
        """
        Close the websocket connection safely.
        """

    @abstractmethod
    async def subscribe(self, channels: list[str]):
        """
        Subscribe to specific channels (e.g., 'ticker.BTCUSD', 'trades.ETHUSD').
        """

    @abstractmethod
    async def unsubscribe(self, channels: list[str]):
        """
        Unsubscribe from specific channels.
        """
