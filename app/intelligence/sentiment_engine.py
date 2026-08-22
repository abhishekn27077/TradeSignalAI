from typing import Dict, Any, Optional
from app.intelligence.news_engine import news_engine

class SentimentEngine:
    """
    Phase 7: Sentiment Engine
    Analyzes verified news, financial headlines, and macro reports.
    Aggregates sentiment by asset.
    """
    
    async def get_asset_sentiment(self, asset: str) -> Dict[str, Any]:
        news_assessment = await news_engine.get_aggregated_news_sentiment(asset)
        
        # Default neutral response if no news
        if not news_assessment:
            return {
                "bullish_score": 0.0,
                "bearish_score": 0.0,
                "neutral_score": 1.0,
                "sentiment_strength": 0.0,
                "asset": asset,
                "overall": "NEUTRAL"
            }
            
        # Map assessment to scores
        bullish = 0.0
        bearish = 0.0
        neutral = 0.0
        
        confidence = news_assessment.confidence
        if news_assessment.sentiment == "BULLISH":
            bullish = confidence
            neutral = 1.0 - confidence
        elif news_assessment.sentiment == "BEARISH":
            bearish = confidence
            neutral = 1.0 - confidence
        else:
            neutral = 1.0
            
        return {
            "bullish_score": round(bullish, 2),
            "bearish_score": round(bearish, 2),
            "neutral_score": round(neutral, 2),
            "sentiment_strength": round(max(bullish, bearish), 2),
            "asset": asset,
            "overall": news_assessment.sentiment
        }

sentiment_engine = SentimentEngine()
