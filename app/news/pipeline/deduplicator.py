import hashlib
from typing import Any


class DuplicateDetector:
    """
    Prevents reprocessing of the same news item.
    Utilizes an in-memory dictionary acting as a simple LRU cache or Bloom Filter proxy.
    In production, this would be backed by Redis.
    """
    def __init__(self, max_size: int = 10000):
        self._seen_hashes = {}
        self.max_size = max_size
        
    def _generate_hash(self, item: dict[str, Any]) -> str:
        """Hash based on title and source timestamp to detect duplicates."""
        title = item.get("title", "").strip().lower()
        source = item.get("source", "").strip().lower()
        raw_str = f"{source}:{title}"
        return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

    def is_duplicate(self, item: dict[str, Any]) -> bool:
        item_hash = self._generate_hash(item)
        if item_hash in self._seen_hashes:
            return True
            
        # Manage size
        if len(self._seen_hashes) >= self.max_size:
            # Pop oldest (In Python 3.7+, dicts maintain insertion order)
            oldest_key = next(iter(self._seen_hashes))
            del self._seen_hashes[oldest_key]
            
        self._seen_hashes[item_hash] = True
        return False

duplicate_detector = DuplicateDetector()
