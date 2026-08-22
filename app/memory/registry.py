from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)


class MemoryRegistry:
    def __init__(self):
        self._providers: dict[str, Any] = {}

    def register(self, name: str, provider: Any):
        self._providers[name] = provider
        logger.debug(f"Memory provider registered: {name}")

    def get(self, name: str) -> Any | None:
        provider = self._providers.get(name)
        if provider is None:
            logger.warning(f"Memory provider {name} not found")
        return provider

    def list_providers(self) -> dict[str, Any]:
        return dict(self._providers)


memory_registry = MemoryRegistry()