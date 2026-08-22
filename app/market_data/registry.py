from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

from app.logs.logger import get_logger

logger = get_logger(__name__)


class AssetClass(str, Enum):
    CRYPTO = "CRYPTO"
    FX = "FX"
    METALS = "METALS"
    INDEX = "INDEX"


class MarketSession(BaseModel):
    open_time_utc: str  # Format "HH:MM"
    close_time_utc: str # Format "HH:MM"
    days_open: List[int] # 0 = Monday, 6 = Sunday


class AssetConfig(BaseModel):
    symbol: str
    asset_class: AssetClass
    provider_symbol: str
    timeframe_support: List[str] = Field(default_factory=lambda: ["M5", "M15", "H1", "H4", "D1", "W1"])
    trading_sessions: MarketSession
    timezone: str = "UTC"
    spread_model: float = 0.0001
    enabled: bool = True


class AssetRegistry:
    def __init__(self):
        self._assets: Dict[str, AssetConfig] = {}
        self._initialize_defaults()

    def _initialize_defaults(self):
        # 24/7 Crypto
        crypto_session = MarketSession(open_time_utc="00:00", close_time_utc="23:59", days_open=[0, 1, 2, 3, 4, 5, 6])
        
        # FX typically open Sun 17:00 EST to Fri 16:00 EST (roughly Sun 22:00 UTC to Fri 21:00 UTC)
        fx_session = MarketSession(open_time_utc="00:00", close_time_utc="23:59", days_open=[0, 1, 2, 3, 4]) 

        # Index typically follows specific exchange hours, approximated here to standard CME Globex
        index_session = MarketSession(open_time_utc="23:00", close_time_utc="22:00", days_open=[0, 1, 2, 3, 4])

        default_assets = [
            AssetConfig(symbol="BTCUSD", asset_class=AssetClass.CRYPTO, provider_symbol="BTC-USD", trading_sessions=crypto_session, spread_model=10.0),
            AssetConfig(symbol="ETHUSD", asset_class=AssetClass.CRYPTO, provider_symbol="ETH-USD", trading_sessions=crypto_session, spread_model=1.0),
            AssetConfig(symbol="EURUSD", asset_class=AssetClass.FX, provider_symbol="EURUSD=X", trading_sessions=fx_session, spread_model=0.0001),
            AssetConfig(symbol="GBPUSD", asset_class=AssetClass.FX, provider_symbol="GBPUSD=X", trading_sessions=fx_session, spread_model=0.00015),
            AssetConfig(symbol="USDJPY", asset_class=AssetClass.FX, provider_symbol="JPY=X", trading_sessions=fx_session, spread_model=0.015),
            AssetConfig(symbol="AUDUSD", asset_class=AssetClass.FX, provider_symbol="AUDUSD=X", trading_sessions=fx_session, spread_model=0.00015),
            AssetConfig(symbol="XAUUSD", asset_class=AssetClass.METALS, provider_symbol="GC=F", trading_sessions=fx_session, spread_model=0.3),
            AssetConfig(symbol="NAS100", asset_class=AssetClass.INDEX, provider_symbol="NQ=F", trading_sessions=index_session, spread_model=2.0),
            AssetConfig(symbol="SPX500", asset_class=AssetClass.INDEX, provider_symbol="ES=F", trading_sessions=index_session, spread_model=0.5),
        ]

        for asset in default_assets:
            self.register(asset)

    def register(self, config: AssetConfig):
        self._assets[config.symbol] = config
        logger.debug(f"Asset registered: {config.symbol}")

    def get(self, symbol: str) -> Optional[AssetConfig]:
        return self._assets.get(symbol)

    def list_symbols(self) -> List[str]:
        return [sym for sym, config in self._assets.items() if config.enabled]

    def get_by_class(self, asset_class: AssetClass) -> List[AssetConfig]:
        return [config for config in self._assets.values() if config.asset_class == asset_class and config.enabled]

    def get_validation_universe(self) -> List[str]:
        """
        Phase 32: Controlled Validation Universe
        Returns only symbols that are actively supported for real-data certification to avoid API rate limits.
        """
        validation_symbols = ["BTCUSD", "ETHUSD", "EURUSD", "USDJPY"]
        # Ensure they actually exist in the registry and are enabled
        return [sym for sym in validation_symbols if sym in self._assets and self._assets[sym].enabled]


asset_registry = AssetRegistry()

# For backwards compatibility during refactor
class SymbolRegistry:
    def __init__(self, asset_reg: AssetRegistry):
        self.reg = asset_reg
        
    def register(self, symbol: str, metadata: dict | None = None):
        # Dummy pass-through for legacy code
        pass

    def get(self, symbol: str) -> dict | None:
        asset = self.reg.get(symbol)
        if asset:
            return {"type": asset.asset_class.value.lower()}
        return None

    def list_symbols(self) -> list[str]:
        return self.reg.list_symbols()

    def search(self, query: str) -> list[dict]:
        q = query.upper()
        return [
            {"symbol": s, "type": config.asset_class.value.lower()}
            for s, config in self.reg._assets.items()
            if q in s.upper() and config.enabled
        ]

symbol_registry = SymbolRegistry(asset_registry)