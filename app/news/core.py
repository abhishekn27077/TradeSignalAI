import logging
import uuid
from typing import Any

from app.news.analytics.mapping import AssetMappingEngine
from app.news.analytics.scoring import ImpactScoring
from app.news.nlp.classifier import EventClassifier, TopicDetection
from app.news.nlp.extraction import KeywordExtraction, NamedEntityRecognition
from app.news.nlp.sentiment import sentiment_analyzer
from app.news.pipeline.deduplicator import duplicate_detector
from app.news.pipeline.parser import news_parser
from app.news.pipeline.translation import LanguageDetector, TranslationInterface
from app.news.types import ProcessedNewsItem
from app.utils.event_bus import event_bus

logger = logging.getLogger(__name__)

class NewsManager:
    """
    Central orchestration engine for the News module.
    Takes raw provider data and pushes it through the pipeline.
    """
    def __init__(self):
        self._cache: list[ProcessedNewsItem] = []
        
    async def process_raw_item(self, raw_item: dict[str, Any]) -> ProcessedNewsItem:
        """
        Runs the full NLP pipeline on a single raw news item.
        """
        # 1. Deduplicate
        if duplicate_detector.is_duplicate(raw_item):
            logger.debug("Duplicate news item dropped.")
            return None
            
        # 2. Extract Base Data
        title = raw_item.get("title", "")
        summary = raw_item.get("summary", "")
        source = raw_item.get("source", "Unknown")
        
        full_text = f"{title}. {summary}"
        
        # 3. Clean & Parse
        clean_text = news_parser.clean_text(full_text)
        
        # 4. Translation
        lang = LanguageDetector.detect(clean_text)
        if lang != "en":
            clean_text = TranslationInterface.translate(clean_text, lang)
            
        # 5. NLP Analysis
        sentiment_res = sentiment_analyzer.analyze(clean_text)
        topics = TopicDetection.detect(clean_text)
        event = EventClassifier.classify(clean_text)
        keywords = KeywordExtraction.extract(clean_text)
        entities = NamedEntityRecognition.extract(clean_text)
        
        # 6. Analytics
        primary_category = topics[0] if topics else "General Market News"
        impact = ImpactScoring.calculate(clean_text, primary_category)
        affected_assets = AssetMappingEngine.map_assets(clean_text)
        
        # 7. Construct Final Item
        item = ProcessedNewsItem(
            id=str(uuid.uuid4()),
            title=title,
            summary=summary,
            source=source,
            category=primary_category,
            affected_assets=affected_assets,
            sentiment=sentiment_res["sentiment"],
            confidence=sentiment_res["confidence"],
            reasoning=sentiment_res["reasoning"],
            impact_score=impact,
            keywords=keywords,
            named_entities=entities,
            economic_event=event
        )
        
        # Cache memory
        self._cache.append(item)
        if len(self._cache) > 1000:
            self._cache.pop(0)
            
        # 8. Publish Events
        await event_bus.publish("NewsProcessed", payload=item.model_dump())
        if impact == "HIGH":
            await event_bus.publish("HighImpactNews", payload=item.model_dump())
            
        return item
        
    def get_recent_news(self) -> list[ProcessedNewsItem]:
        return list(reversed(self._cache))

news_manager = NewsManager()
