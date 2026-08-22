"""
Phase 40 — News Intelligence Engine.

Normalizes, classifies, and scores market news for the forecasting pipeline.
Provides asset-level sentiment aggregation and macro context for multi-model fusion.

Categories: CENTRAL_BANK, INFLATION, EMPLOYMENT, GDP, GEOPOLITICAL,
            COMMODITY, BANKING, MARKET, RISK, EARNINGS, TRADE, HOUSING.
"""
import re
from datetime import datetime, timezone
from typing import Any, Optional

from app.logs.logger import get_logger

logger = get_logger(__name__)

# ── Asset–Keyword Mapping ───────────────────────────────────────────────────
ASSET_KEYWORDS: dict[str, list[str]] = {
    "EURUSD": ["euro", "eur", "ecb", "eurozone", "lagarde", "eu economy"],
    "GBPUSD": ["pound", "gbp", "boe", "bank of england", "uk economy", "bailey"],
    "USDJPY": ["yen", "jpy", "boj", "bank of japan", "ueda", "japan"],
    "AUDUSD": ["aussie", "aud", "rba", "australia", "bullock"],
    "XAUUSD": ["gold", "xau", "precious metal", "bullion", "safe haven"],
    "NAS100": ["nasdaq", "tech stocks", "big tech", "faang", "magnificent seven", "ai stocks"],
    "SPX500": ["s&p 500", "spx", "sp500", "wall street", "us stocks", "us equities"],
    "BTCUSD": ["bitcoin", "btc", "crypto", "cryptocurrency", "digital asset"],
    "ETHUSD": ["ethereum", "eth", "defi", "smart contract"],
}

# ── Category Classifiers ────────────────────────────────────────────────────
CATEGORY_PATTERNS: dict[str, list[str]] = {
    "CENTRAL_BANK": ["fed", "fomc", "ecb", "boe", "boj", "rba", "interest rate", "rate decision", "monetary policy", "rate hike", "rate cut", "dovish", "hawkish", "taper"],
    "INFLATION": ["cpi", "ppi", "inflation", "deflation", "price index", "pce", "core inflation", "consumer price"],
    "EMPLOYMENT": ["nfp", "payroll", "unemployment", "jobless", "jobs", "labor market", "hiring", "employment"],
    "GDP": ["gdp", "gross domestic", "economic growth", "recession", "expansion", "contraction"],
    "GEOPOLITICAL": ["war", "conflict", "sanction", "tariff", "trade war", "geopolitical", "tension", "military", "nato"],
    "COMMODITY": ["oil", "crude", "opec", "natural gas", "copper", "commodity"],
    "BANKING": ["bank", "credit", "lending", "deposit", "financial stability", "banking crisis", "svb"],
    "EARNINGS": ["earnings", "revenue", "profit", "eps", "quarterly results", "guidance"],
    "TRADE": ["trade balance", "export", "import", "trade deficit", "trade surplus", "tariff"],
    "HOUSING": ["housing", "home sales", "mortgage", "real estate", "building permits"],
    "RISK": ["risk off", "risk on", "volatility", "vix", "fear", "panic", "sell-off", "crash", "correction"],
    "MARKET": ["stock market", "bond market", "treasury", "yield", "equity", "index"],
}

# ── Sentiment Keyword Banks ─────────────────────────────────────────────────
POSITIVE_KEYWORDS = [
    "surge", "rally", "gain", "rise", "climb", "jump", "boost", "strong",
    "beat", "exceed", "outperform", "optimism", "bull", "recovery", "growth",
    "upbeat", "positive", "improve", "accelerat", "expan",
]
NEGATIVE_KEYWORDS = [
    "drop", "fall", "decline", "plunge", "crash", "slump", "weak", "miss",
    "disappoint", "fear", "concern", "bear", "recession", "contraction",
    "downgrade", "negative", "deteriorat", "slow", "worsen", "cut",
]


class NewsIntelligenceEngine:
    """
    Classifies, scores, and maps news to affected assets
    for the forecasting pipeline.
    """

    def __init__(self):
        self._initialized = False

    async def initialize(self):
        self._initialized = True
        logger.info("NewsIntelligenceEngine initialized")

    def process_article(self, article: dict) -> dict:
        """
        Process a raw news article and return enriched intelligence.
        """
        title = (article.get("title") or "").lower()
        body = (article.get("body") or article.get("description") or "").lower()
        combined_text = f"{title} {body}"

        return {
            "original_title": article.get("title", ""),
            "source": article.get("source", "unknown"),
            "published_at": article.get("published_at", datetime.now(timezone.utc).isoformat()),
            "url": article.get("url", ""),
            "category": self._classify_category(combined_text),
            "sentiment_score": self._compute_sentiment(combined_text),
            "sentiment_label": self._sentiment_label(self._compute_sentiment(combined_text)),
            "affected_assets": self._map_affected_assets(combined_text),
            "importance": self._assess_importance(combined_text, article),
            "topics": self._extract_topics(combined_text),
            "is_market_moving": self._is_market_moving(combined_text),
        }

    def process_batch(self, articles: list[dict]) -> list[dict]:
        """Process a batch of articles and return enriched intelligence."""
        seen_titles = set()
        results = []

        for article in articles:
            title = (article.get("title") or "").strip()
            # Deduplicate by title similarity
            title_key = re.sub(r"\s+", " ", title.lower().strip())
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            results.append(self.process_article(article))

        return results

    def get_asset_sentiment(self, articles: list[dict], asset: str) -> dict:
        """
        Aggregate sentiment for a specific asset across processed articles.
        Returns sentiment score, article count, and directional bias.
        """
        relevant = [a for a in articles if asset in a.get("affected_assets", [])]

        if not relevant:
            return {
                "asset": asset,
                "sentiment_score": 0.0,
                "sentiment_label": "NEUTRAL",
                "article_count": 0,
                "directional_bias": "NEUTRAL",
                "confidence": 0.0,
            }

        scores = [a.get("sentiment_score", 0.0) for a in relevant]
        avg_score = sum(scores) / len(scores)

        if avg_score > 0.2:
            bias = "BULLISH"
        elif avg_score < -0.2:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"

        return {
            "asset": asset,
            "sentiment_score": round(avg_score, 3),
            "sentiment_label": self._sentiment_label(avg_score),
            "article_count": len(relevant),
            "directional_bias": bias,
            "confidence": min(abs(avg_score) * 2, 1.0),
        }

    def get_macro_context(self, articles: list[dict]) -> dict:
        """
        Build macro context summary from processed news for forecasting.
        """
        categories = {}
        for article in articles:
            cat = article.get("category", "MARKET")
            if cat not in categories:
                categories[cat] = {"count": 0, "avg_sentiment": 0.0, "articles": []}
            categories[cat]["count"] += 1
            categories[cat]["avg_sentiment"] += article.get("sentiment_score", 0.0)

        for cat in categories:
            if categories[cat]["count"] > 0:
                categories[cat]["avg_sentiment"] /= categories[cat]["count"]
                categories[cat]["avg_sentiment"] = round(categories[cat]["avg_sentiment"], 3)

        # Overall market mood
        all_scores = [a.get("sentiment_score", 0.0) for a in articles]
        overall = sum(all_scores) / len(all_scores) if all_scores else 0.0

        return {
            "overall_sentiment": round(overall, 3),
            "overall_mood": "RISK_ON" if overall > 0.1 else "RISK_OFF" if overall < -0.1 else "MIXED",
            "category_breakdown": categories,
            "market_moving_count": sum(1 for a in articles if a.get("is_market_moving")),
            "total_articles": len(articles),
        }

    # ── Private Classifiers ─────────────────────────────────────────────────

    def _classify_category(self, text: str) -> str:
        """Classify text into a news category."""
        scores = {}
        for category, patterns in CATEGORY_PATTERNS.items():
            score = sum(1 for p in patterns if p in text)
            if score > 0:
                scores[category] = score

        if not scores:
            return "MARKET"

        return max(scores, key=scores.get)

    def _compute_sentiment(self, text: str) -> float:
        """
        Compute sentiment score from -1.0 (very negative) to +1.0 (very positive).
        Uses keyword-based scoring as a lightweight approach.
        """
        pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
        neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
        total = pos_count + neg_count

        if total == 0:
            return 0.0

        score = (pos_count - neg_count) / total
        return round(max(-1.0, min(1.0, score)), 3)

    @staticmethod
    def _sentiment_label(score: float) -> str:
        """Convert numeric sentiment to label."""
        if score > 0.3:
            return "VERY_POSITIVE"
        elif score > 0.1:
            return "POSITIVE"
        elif score > -0.1:
            return "NEUTRAL"
        elif score > -0.3:
            return "NEGATIVE"
        else:
            return "VERY_NEGATIVE"

    def _map_affected_assets(self, text: str) -> list[str]:
        """Map text to affected assets based on keyword matching."""
        affected = []
        for asset, keywords in ASSET_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                affected.append(asset)

        # General USD news affects all USD pairs
        usd_keywords = ["fed", "fomc", "us economy", "powell", "treasury", "dollar"]
        if any(kw in text for kw in usd_keywords):
            for asset in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"]:
                if asset not in affected:
                    affected.append(asset)

        return affected

    def _assess_importance(self, text: str, article: dict) -> str:
        """Assess the importance level of a news article."""
        high_keywords = ["breaking", "emergency", "crisis", "central bank", "rate decision",
                         "fomc", "recession", "crash", "war"]
        medium_keywords = ["report", "data", "inflation", "employment", "gdp",
                           "earnings", "forecast", "outlook"]

        if any(kw in text for kw in high_keywords):
            return "HIGH"
        elif any(kw in text for kw in medium_keywords):
            return "MEDIUM"
        return "LOW"

    def _extract_topics(self, text: str) -> list[str]:
        """Extract key topics from the text."""
        topics = []
        for category, patterns in CATEGORY_PATTERNS.items():
            if any(p in text for p in patterns):
                topics.append(category)
        return topics[:5]  # Limit to top 5 topics

    def _is_market_moving(self, text: str) -> bool:
        """Determine if news is likely to move markets."""
        market_movers = [
            "breaking", "emergency", "rate decision", "fomc", "ecb", "boe",
            "nfp", "cpi", "gdp", "recession", "crisis", "war", "crash",
            "surge", "plunge", "unexpected",
        ]
        return any(kw in text for kw in market_movers)


# ── Singleton ───────────────────────────────────────────────────────────────
news_intelligence_engine = NewsIntelligenceEngine()
