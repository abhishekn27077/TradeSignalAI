import asyncio
from collections.abc import Callable

from app.logs.logger import get_logger

logger = get_logger(__name__)


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def publish(self, event_type: str, *args, **kwargs):
        handlers = self._subscribers.get(event_type)
        if not handlers:
            return
        tasks = []
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(asyncio.create_task(handler(*args, **kwargs)))
                else:
                    result = handler(*args, **kwargs)
                    # Handle lambdas that wrap async functions — they return coroutines
                    if asyncio.iscoroutine(result):
                        tasks.append(asyncio.create_task(result))
            except Exception as e:
                logger.warning(f"Event handler error for {event_type}: {e}")
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Event handler exception for {event_type}: {result}")


event_bus = EventBus()