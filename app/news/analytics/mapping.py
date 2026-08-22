from app.news.types import AssetClass


class AssetMappingEngine:
    """
    Detects which assets are affected by a news item.
    """
    ASSET_MAP = {
        AssetClass.CRYPTO: ["bitcoin", "btc", "ethereum", "eth", "crypto", "blockchain"],
        AssetClass.FOREX: ["usd", "eur", "jpy", "gbp", "forex", "fiat"],
        AssetClass.STOCKS: ["stock", "equity", "sp500", "nasdaq", "dow", "earnings"],
        AssetClass.COMMODITIES: ["gold", "oil", "silver", "commodity"],
        AssetClass.BONDS: ["bond", "yield", "treasury"]
    }

    @staticmethod
    def map_assets(text: str) -> list:
        text_lower = text.lower()
        affected = set()
        
        for asset_class, keywords in AssetMappingEngine.ASSET_MAP.items():
            for kw in keywords:
                if kw in text_lower:
                    affected.add(asset_class.value)
                    
        return list(affected)

class MarketCorrelation:
    """
    Finds specific ticker correlations (e.g., BTC-USD, EUR-USD).
    """
    @staticmethod
    def extract_tickers(text: str) -> list:
        # Stub for extracting specific symbols like AAPL, BTC
        # In a real system, this cross-references the Market Data Registry
        return []
