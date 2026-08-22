from abc import ABC, abstractmethod
from typing import Any

from app.database.models.memory import MemoryRecord


class IMemoryProvider(ABC):
    """Abstract interface for memory storage providers."""
    
    @abstractmethod
    def store(self, record: MemoryRecord) -> bool:
        pass
        
    @abstractmethod
    def retrieve(self, record_id: str) -> MemoryRecord | None:
        pass
        
    @abstractmethod
    def delete(self, record_id: str) -> bool:
        pass
        
    @abstractmethod
    def search(self, query_vector: list[float], top_k: int = 5, filters: dict[str, Any] = None) -> list[MemoryRecord]:
        pass

class IEmbeddingService(ABC):
    """Abstract interface for embedding text."""
    
    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        pass
