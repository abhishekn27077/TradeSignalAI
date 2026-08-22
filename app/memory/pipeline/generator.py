import logging
import uuid
from typing import Any

from app.database.models.memory import Lesson, MemoryRecord
from app.memory.vector.embeddings import embedding_service
from app.utils.event_bus import event_bus

logger = logging.getLogger(__name__)

class LessonGenerator:
    """Generates and stores Lessons into the Memory system."""
    
    def __init__(self, memory_registry):
        self.registry = memory_registry

    async def generate_lesson(self, payload: dict[str, Any]):
        """Generates a Lesson object, creates a MemoryRecord, and embeds it."""
        try:
            # 1. Create Lesson object
            lesson_id = str(uuid.uuid4())
            lesson = Lesson(
                id=lesson_id,
                source_trade_id=payload.get("trade_id"),
                summary=f"[{payload['type']}] Strategy: {payload['strategy']} on {payload['symbol']}. {payload['insight']}",
                actionable_rule=payload.get("actionable", ""),
                confidence=0.85
            )
            
            # 2. Create MemoryRecord
            text_content = f"Lesson: {lesson.summary}. Rule: {lesson.actionable_rule}"
            vector = embedding_service.embed_text(text_content)
            
            record = MemoryRecord(
                id=lesson_id,
                type="LESSON",
                content=text_content,
                metadata={
                    "trade_id": payload.get("trade_id"),
                    "symbol": payload.get("symbol"),
                    "strategy": payload.get("strategy"),
                    "lesson_type": payload.get("type")
                },
                embedding=vector
            )
            
            # 3. Store in Vector DB (Long Term Memory)
            long_term_provider = self.registry.get("long_term")
            long_term_provider.store(record)
            
            logger.info(f"Generated and stored new Lesson: {lesson_id}")
            
            # 4. Broadcast Event
            await event_bus.publish("LessonGenerated", {"lesson_id": lesson_id, "summary": lesson.summary})
            
        except Exception as e:
            logger.error(f"Failed to generate lesson: {e!s}")
