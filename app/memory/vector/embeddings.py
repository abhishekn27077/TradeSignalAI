
from app.logs.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    def __init__(self):
        self._dimension = 384
        self._provider = None
        try:
            from sentence_transformers import SentenceTransformer
            self._provider = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Embedding service initialized with sentence-transformers")
        except ImportError:
            logger.info("sentence-transformers not available, using fallback embedding")

    async def embed(self, text: str) -> list[float] | None:
        if self._provider:
            try:
                result = self._provider.encode(text)
                return result.tolist()
            except Exception as e:
                logger.warning(f"Embedding failed: {e}")
        return self._fallback_embed(text)

    def embed_text(self, text: str) -> list[float]:
        return self._fallback_embed(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self._provider:
            try:
                results = self._provider.encode(texts)
                return [r.tolist() for r in results]
            except Exception as e:
                logger.warning(f"Batch embedding failed: {e}")
        return [self._fallback_embed(t) for t in texts]

    def _fallback_embed(self, text: str) -> list[float]:
        import hashlib
        h = hashlib.sha256(text.encode()).hexdigest()
        seed = int(h[:8], 16)
        import random
        rng = random.Random(seed)
        return [rng.random() for _ in range(self._dimension)]

    @property
    def dimension(self) -> int:
        return self._dimension


embedding_service = EmbeddingService()