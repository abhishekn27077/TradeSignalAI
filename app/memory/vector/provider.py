from typing import Any

import numpy as np

from app.database.models.memory import MemoryRecord
from app.memory.interfaces import IMemoryProvider


class InMemoryVectorProvider(IMemoryProvider):
    """
    An in-memory vector database using numpy for cosine similarity.
    In production, this is swapped for Qdrant, Pinecone, or Milvus.
    """
    
    def __init__(self):
        self._store: dict[str, MemoryRecord] = {}

    def store(self, record: MemoryRecord) -> bool:
        self._store[record.id] = record
        return True
        
    def retrieve(self, record_id: str) -> MemoryRecord | None:
        return self._store.get(record_id)
        
    def delete(self, record_id: str) -> bool:
        if record_id in self._store:
            del self._store[record_id]
            return True
        return False
        
    def search(self, query_vector: list[float], top_k: int = 5, filters: dict[str, Any] = None) -> list[MemoryRecord]:
        if not self._store:
            return []
            
        q_vec = np.array(query_vector)
        results = []
        
        for record in self._store.values():
            # Apply metadata filters (support exact match and $lt operator for timestamps)
            if filters:
                match = True
                for k, v in filters.items():
                    record_val = record.metadata.get(k)
                    
                    if isinstance(v, dict) and "$lt" in v:
                        if record_val is None or not (record_val < v["$lt"]):
                            match = False
                            break
                    elif record_val != v:
                        match = False
                        break
                if not match:
                    continue
                    
            if record.embedding is None:
                continue
                
            r_vec = np.array(record.embedding)
            
            # Cosine similarity
            similarity = np.dot(q_vec, r_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(r_vec))
            results.append((similarity, record))
            
        # Sort by similarity descending
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:top_k]]
