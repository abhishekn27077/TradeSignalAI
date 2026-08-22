from app.news.types import ImpactScore


class ImpactScoring:
    """
    Scores the expected market impact of a news event.
    """
    HIGH_IMPACT_KEYWORDS = {"war", "crash", "rate cut", "hike", "bankruptcy", "nfp", "fomc"}
    
    @staticmethod
    def calculate(text: str, category: str) -> ImpactScore:
        text_lower = text.lower()
        
        # Check high impact words
        if any(kw in text_lower for kw in ImpactScoring.HIGH_IMPACT_KEYWORDS):
            return ImpactScore.HIGH
            
        if category in ["Macroeconomics", "Monetary Policy"]:
            return ImpactScore.HIGH
            
        return ImpactScore.MEDIUM

class NewsRanking:
    """
    Ranks news by importance (Time + Impact).
    """
    @staticmethod
    def score(impact: ImpactScore, age_minutes: float) -> float:
        base_score = {
            ImpactScore.HIGH: 100,
            ImpactScore.MEDIUM: 50,
            ImpactScore.LOW: 10,
            ImpactScore.NONE: 0
        }.get(impact, 0)
        
        # Time decay
        decay = max(0, 1 - (age_minutes / 1440)) # Decay over 24h
        return base_score * decay
