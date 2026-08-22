from app.news.types import SentimentCategory


class SentimentAnalyzer:
    """
    Analyzes text to determine sentiment category and confidence.
    Uses heuristic keyword matching as a fallback/fast-path.
    In production, this could route to an LLM or local model like FinBERT.
    """
    
    # Simple heuristic dictionaries
    BULLISH_WORDS = {"soar", "jump", "beat", "up", "bull", "growth", "positive", "exceed", "record"}
    BEARISH_WORDS = {"plunge", "drop", "miss", "down", "bear", "decline", "negative", "fail", "crash"}

    @staticmethod
    def analyze(text: str) -> dict:
        text_lower = text.lower()
        words = set(text_lower.split())
        
        bull_score = len(words.intersection(SentimentAnalyzer.BULLISH_WORDS))
        bear_score = len(words.intersection(SentimentAnalyzer.BEARISH_WORDS))
        
        total = bull_score + bear_score
        if total == 0:
            return {
                "sentiment": SentimentCategory.NEUTRAL,
                "confidence": 1.0,
                "reasoning": "No strong directional keywords found."
            }
            
        bull_ratio = bull_score / total
        
        if bull_ratio > 0.8:
            sentiment = SentimentCategory.VERY_BULLISH
        elif bull_ratio > 0.55:
            sentiment = SentimentCategory.BULLISH
        elif bull_ratio < 0.2:
            sentiment = SentimentCategory.VERY_BEARISH
        elif bull_ratio < 0.45:
            sentiment = SentimentCategory.BEARISH
        else:
            sentiment = SentimentCategory.NEUTRAL
            
        confidence = abs(bull_ratio - 0.5) * 2  # Scale 0 to 1
        # Prevent 0 confidence on neutral
        if sentiment == SentimentCategory.NEUTRAL:
            confidence = 0.5
            
        return {
            "sentiment": sentiment,
            "confidence": round(confidence, 2),
            "reasoning": f"Found {bull_score} bullish and {bear_score} bearish indicators."
        }

sentiment_analyzer = SentimentAnalyzer()
