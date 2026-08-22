import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)

class AgentMemoryInterface(ABC):
    """
    Abstract interface for Agent Memory.
    Implementations could be Redis, Postgres (pgvector), Pinecone, etc.
    """
    @abstractmethod
    async def add_memory(self, agent_id: str, key: str, value: Any, tags: list[str] = []):
        pass

    @abstractmethod
    async def get_memory(self, agent_id: str, key: str) -> Any | None:
        pass
        
    @abstractmethod
    async def search_memory(self, query: str, tags: list[str] = []) -> list[Any]:
        """Semantic search over past trade memories or market events."""

class InMemoryAgentStore(AgentMemoryInterface):
    """
    Temporary in-memory implementation for Phase 4.
    Will be replaced by a Vector DB / Postgres implementation in production.
    """
    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    async def add_memory(self, agent_id: str, key: str, value: Any, tags: list[str] = []):
        if agent_id not in self._store:
            self._store[agent_id] = {}
        self._store[agent_id][key] = {"value": value, "tags": tags}
        logger.debug(f"Memory added for {agent_id}: {key}")

    async def get_memory(self, agent_id: str, key: str) -> Any | None:
        agent_mem = self._store.get(agent_id, {})
        data = agent_mem.get(key)
        return data["value"] if data else None
        
    async def search_memory(self, query: str, tags: list[str] = []) -> list[Any]:
        # Naive stub implementation
        results = []
        for agent_id, mems in self._store.items():
            for k, data in mems.items():
                if any(tag in data["tags"] for tag in tags):
                    results.append(data["value"])
        return results

# Global shared knowledge base interface
shared_knowledge = InMemoryAgentStore()
