
from fastapi import APIRouter, Query

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/latest", summary="Get Latest News")
async def get_latest_news(limit: int = Query(default=20, le=100)):
    try:
        from app.news.providers.manager import news_provider_manager
        news = await news_provider_manager.fetch_all(limit=limit)
        return {"success": True, "news": news, "count": len(news)}
    except Exception as e:
        logger.warning(f"News fetch error: {e}")
        return {"success": True, "news": [], "count": 0}


@router.get("/symbol/{symbol}", summary="Get News by Symbol")
async def get_news_by_symbol(symbol: str, limit: int = Query(default=10, le=50)):
    try:
        from app.news.providers.manager import news_provider_manager
        news = await news_provider_manager.fetch_by_symbol(symbol, limit=limit)
        return {"success": True, "symbol": symbol, "news": news, "count": len(news)}
    except Exception as e:
        logger.warning(f"News by symbol error: {e}")
        return {"success": True, "news": [], "count": 0}


@router.get("/sentiment/{symbol}", summary="Get News Sentiment")
async def get_news_sentiment(symbol: str):
    try:
        from app.news.nlp.sentiment import sentiment_analyzer
        sentiment = await sentiment_analyzer.analyze_symbol(symbol) if hasattr(sentiment_analyzer, "analyze_symbol") else {}
        return {"success": True, "symbol": symbol, "sentiment": sentiment}
    except Exception as e:
        logger.warning(f"Sentiment error: {e}")
        return {"success": True, "symbol": symbol, "sentiment": {}}


@router.get("/intelligence", summary="News Intelligence Feed")
async def get_news_intelligence(
    limit: int = Query(default=30, le=100),
    category: str = Query(default=None, description="Filter: CENTRAL_BANK, INFLATION, EMPLOYMENT, GDP, etc."),
):
    """
    Phase 40: Returns categorized news feed with:
    - Sentiment scores (-1.0 to +1.0)
    - Topic classification (12 categories)
    - Importance level (HIGH / MEDIUM / LOW)
    - Affected asset badges
    - Overall macro context
    """
    try:
        from app.news.intelligence import news_intelligence_engine

        # Try to fetch raw news from provider
        raw_articles = []
        try:
            from app.news.providers.manager import news_provider_manager
            raw_articles = await news_provider_manager.fetch_all(limit=limit)
        except Exception:
            pass

        if not raw_articles:
            # Return empty intelligence feed
            return {
                "success": True,
                "articles": [],
                "macro_context": {
                    "overall_sentiment": 0.0,
                    "overall_mood": "UNKNOWN",
                    "category_breakdown": {},
                    "market_moving_count": 0,
                    "total_articles": 0,
                },
                "count": 0,
            }

        # Process through intelligence engine
        processed = news_intelligence_engine.process_batch(raw_articles)

        # Apply category filter
        if category:
            processed = [a for a in processed if a.get("category") == category]

        # Build macro context
        macro_context = news_intelligence_engine.get_macro_context(processed)

        return {
            "success": True,
            "articles": processed[:limit],
            "macro_context": macro_context,
            "count": len(processed),
        }
    except Exception as e:
        logger.warning(f"News intelligence error: {e}")
        return {"success": True, "articles": [], "count": 0, "macro_context": {}}