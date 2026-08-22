from typing import Any

from app.database.models.memory import MemoryRecord
from app.memory.interfaces import IMemoryProvider
from app.memory.vector.embeddings import embedding_service


class HybridSearchEngine:
    """Orchestrates embedding and semantic search across providers."""
    
    def __init__(self, provider: IMemoryProvider):
        self.provider = provider
        
    def search_similar(self, query_text: str, top_k: int = 5, filters: dict[str, Any] = None) -> list[MemoryRecord]:
        """
        Embeds the query text and performs a vector search with optional metadata filters.
        """
        query_vector = embedding_service.embed_text(query_text)
        return self.provider.search(query_vector=query_vector, top_k=top_k, filters=filters)
