from typing import List

class AssetImpactEngine:
    """
    Phase 4: Deterministic asset-event mapping layer.
    Do not rely solely on LLM guesses.
    """
    
    EVENT_MAPPINGS = {
        "US CPI": ["USD", "EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "NAS100", "SPX500"],
        "Fed rate decision": ["USD", "XAUUSD", "NAS100", "SPX500"],
        "Oil shock": ["USOIL", "USDCAD"],
        "NFP": ["USD", "EURUSD", "GBPUSD", "USDJPY", "XAUUSD"],
        "ECB rate decision": ["EUR", "EURUSD", "EURGBP", "EURJPY"],
    }
    
    @classmethod
    def get_affected_assets(cls, event_name: str) -> List[str]:
        # Simple substring matching for mapping
        affected = set()
        for key, assets in cls.EVENT_MAPPINGS.items():
            if key.lower() in event_name.lower():
                affected.update(assets)
        return list(affected)

asset_impact_engine = AssetImpactEngine()
