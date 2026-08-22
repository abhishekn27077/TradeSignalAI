import hashlib
import json
import time
from typing import Dict, Any, List, Optional
import logging

from app.agents.providers.router import model_router
from app.intelligence.schemas import NewsAssessment
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

class NewsEngine:
    def __init__(self):
        self.cache: Dict[str, dict] = {}
        self.ttl = 3600 * 24  # 24 hours cache TTL
        self.settings = get_settings()

    def _hash_article(self, headline: str, published_at: str) -> str:
        return hashlib.md5(f"{headline}_{published_at}".encode('utf-8')).hexdigest()

    async def fetch_news_for_asset(self, asset: str) -> List[Dict[str, Any]]:
        # In a real implementation, this would call an API like NewsAPI or AlphaVantage
        # For now, we return mock recent news based on the asset to allow testing.
        return [
            {
                "headline": f"Major developments in {asset} markets as central banks hold rates.",
                "source": "MockFinancialNews",
                "url": "http://mock.url",
                "published_at": str(time.time() - 3600),
                "asset_relevance": asset,
                "country": "US",
                "topic": "monetary policy",
                "raw_text_or_summary": f"Central banks have indicated a steady hold on rates, which could be seen as a neutral to slightly bullish signal for {asset}. Volatility expected to drop.",
                "timestamp_fetched": time.time()
            }
        ]

    async def analyze_article(self, article: Dict[str, Any]) -> Optional[NewsAssessment]:
        article_hash = self._hash_article(article['headline'], article['published_at'])
        
        # Phase 18: Cache check
        if article_hash in self.cache:
            cached_data = self.cache[article_hash]
            if time.time() - cached_data['timestamp'] < self.ttl:
                logger.info(f"Using cached news analysis for article: {article['headline']}")
                return cached_data['analysis']

        prompt = f"""
        Analyze the following financial news article and determine its market impact.
        
        Headline: {article['headline']}
        Source: {article['source']}
        Summary: {article['raw_text_or_summary']}
        Target Asset: {article['asset_relevance']}
        
        Provide a structured assessment of the sentiment, impact severity, affected assets, and expected time horizon.
        """

        try:
            response_text = await model_router.generate(
                prompt=prompt,
                target="NEWS_ANALYST",
                response_format={"type": "json_schema", "json_schema": {"name": "NewsAssessment", "schema": NewsAssessment.model_json_schema()}}
            )

            if response_text:
                # LLM should return valid JSON string matching the schema
                analysis_dict = json.loads(response_text)
                assessment = NewsAssessment(**analysis_dict)
                
                # Update Cache
                self.cache[article_hash] = {
                    "timestamp": time.time(),
                    "analysis": assessment
                }
                return assessment
            else:
                logger.warning("NEWS_ANALYST returned no response.")
                return None
        except Exception as e:
            logger.error(f"Error analyzing news article: {e}")
            return None

    async def get_aggregated_news_sentiment(self, asset: str) -> Optional[NewsAssessment]:
        # Phase 19: Cost Control - We only analyze if there's new news.
        articles = await self.fetch_news_for_asset(asset)
        if not articles:
            return None
            
        # For simplicity in this engine, we just analyze the most recent/relevant article.
        # A more complex engine would aggregate multiple NewsAssessments.
        return await self.analyze_article(articles[0])

news_engine = NewsEngine()
