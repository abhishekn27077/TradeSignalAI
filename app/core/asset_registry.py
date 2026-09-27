"""
app/core/asset_registry.py
===========================
Phase 1: Canonical Asset Registry for TradeSignalAI-v3.

Every tradable instrument has an explicit, authoritative specification:
- canonical_symbol
- provider_symbol
- venue
- asset_class
- quote_currency
- primary_provider
- secondary_providers
- supported_timeframes
- market_session
- price_precision
- quantity_precision
- status

Explicit Mapping Rules:
- Ambiguous symbols like generic BTCUSD are explicitly resolved to BINANCE:BTCUSDT with recorded transformation.
- Forex symbols (USDJPY, EURUSD, GBPUSD, AUDUSD) route to primary MT5 broker feed.
- Crypto symbols (BTCUSDT, ETHUSDT) route to native Binance exchange feed.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger("asset_registry")


class AssetClass(str, Enum):
    FOREX = "FOREX"
    CRYPTO = "CRYPTO"
    METALS = "METALS"
    INDEX = "INDEX"


class ProviderType(str, Enum):
    MT5 = "MT5"
    BINANCE = "BINANCE"
    TRADINGVIEW = "TRADINGVIEW"
    YFINANCE = "YFINANCE"
    SQLITE = "SQLITE"


@dataclass(frozen=True)
class CanonicalAsset:
    canonical_symbol: str
    provider_symbol: str
    venue: str
    asset_class: AssetClass
    quote_currency: str
    primary_provider: ProviderType
    secondary_providers: Tuple[ProviderType, ...]
    supported_timeframes: Tuple[str, ...]
    market_session: str
    price_precision: int
    quantity_precision: int
    status: str = "ACTIVE"
    min_trade_size: float = 0.01
    pip_size: float = 0.0001
    notes: str = ""


# Immutable Canonical Asset Registry Definitions
CANONICAL_REGISTRY: Dict[str, CanonicalAsset] = {
    # Forex Assets -> Primary Provider: MT5
    "EURUSD": CanonicalAsset(
        canonical_symbol="EURUSD",
        provider_symbol="EURUSD",
        venue="MT5_BROKER",
        asset_class=AssetClass.FOREX,
        quote_currency="USD",
        primary_provider=ProviderType.MT5,
        secondary_providers=(ProviderType.TRADINGVIEW, ProviderType.YFINANCE),
        supported_timeframes=("M5", "M15", "M30", "H1", "H4", "D1"),
        market_session="FOREX_WEEKDAY",
        price_precision=5,
        quantity_precision=2,
        pip_size=0.0001,
        notes="Primary live feed via MT5 broker terminal.",
    ),
    "GBPUSD": CanonicalAsset(
        canonical_symbol="GBPUSD",
        provider_symbol="GBPUSD",
        venue="MT5_BROKER",
        asset_class=AssetClass.FOREX,
        quote_currency="USD",
        primary_provider=ProviderType.MT5,
        secondary_providers=(ProviderType.TRADINGVIEW, ProviderType.YFINANCE),
        supported_timeframes=("M5", "M15", "M30", "H1", "H4", "D1"),
        market_session="FOREX_WEEKDAY",
        price_precision=5,
        quantity_precision=2,
        pip_size=0.0001,
        notes="Primary live feed via MT5 broker terminal.",
    ),
    "USDJPY": CanonicalAsset(
        canonical_symbol="USDJPY",
        provider_symbol="USDJPY",
        venue="MT5_BROKER",
        asset_class=AssetClass.FOREX,
        quote_currency="JPY",
        primary_provider=ProviderType.MT5,
        secondary_providers=(ProviderType.TRADINGVIEW, ProviderType.YFINANCE),
        supported_timeframes=("M5", "M15", "M30", "H1", "H4", "D1"),
        market_session="FOREX_WEEKDAY",
        price_precision=3,
        quantity_precision=2,
        pip_size=0.01,
        notes="Primary live feed via MT5 broker terminal.",
    ),
    "AUDUSD": CanonicalAsset(
        canonical_symbol="AUDUSD",
        provider_symbol="AUDUSD",
        venue="MT5_BROKER",
        asset_class=AssetClass.FOREX,
        quote_currency="USD",
        primary_provider=ProviderType.MT5,
        secondary_providers=(ProviderType.TRADINGVIEW, ProviderType.YFINANCE),
        supported_timeframes=("M5", "M15", "M30", "H1", "H4", "D1"),
        market_session="FOREX_WEEKDAY",
        price_precision=5,
        quantity_precision=2,
        pip_size=0.0001,
        notes="Primary live feed via MT5 broker terminal.",
    ),
    # Crypto Assets -> Primary Provider: Native Binance
    "BTCUSDT": CanonicalAsset(
        canonical_symbol="BTCUSDT",
        provider_symbol="BTCUSDT",
        venue="BINANCE",
        asset_class=AssetClass.CRYPTO,
        quote_currency="USDT",
        primary_provider=ProviderType.BINANCE,
        secondary_providers=(ProviderType.TRADINGVIEW, ProviderType.YFINANCE),
        supported_timeframes=("M5", "M15", "M30", "H1", "H4", "D1"),
        market_session="CRYPTO_24_7",
        price_precision=2,
        quantity_precision=5,
        pip_size=0.01,
        notes="Primary live feed via Binance Native Spot API/WebSocket.",
    ),
    "ETHUSDT": CanonicalAsset(
        canonical_symbol="ETHUSDT",
        provider_symbol="ETHUSDT",
        venue="BINANCE",
        asset_class=AssetClass.CRYPTO,
        quote_currency="USDT",
        primary_provider=ProviderType.BINANCE,
        secondary_providers=(ProviderType.TRADINGVIEW, ProviderType.YFINANCE),
        supported_timeframes=("M5", "M15", "M30", "H1", "H4", "D1"),
        market_session="CRYPTO_24_7",
        price_precision=2,
        quantity_precision=4,
        pip_size=0.01,
        notes="Primary live feed via Binance Native Spot API/WebSocket.",
    ),
    # Commodities / Metals
    "XAUUSD": CanonicalAsset(
        canonical_symbol="XAUUSD",
        provider_symbol="XAUUSD",
        venue="MT5_BROKER",
        asset_class=AssetClass.METALS,
        quote_currency="USD",
        primary_provider=ProviderType.MT5,
        secondary_providers=(ProviderType.TRADINGVIEW, ProviderType.YFINANCE),
        supported_timeframes=("M5", "M15", "M30", "H1", "H4", "D1"),
        market_session="METALS_HOURS",
        price_precision=2,
        quantity_precision=2,
        pip_size=0.1,
        notes="Primary live feed via MT5 broker terminal.",
    ),
    # Index CFDs
    "NAS100": CanonicalAsset(
        canonical_symbol="NAS100",
        provider_symbol="USTEC",
        venue="MT5_BROKER",
        asset_class=AssetClass.INDEX,
        quote_currency="USD",
        primary_provider=ProviderType.MT5,
        secondary_providers=(ProviderType.TRADINGVIEW, ProviderType.YFINANCE),
        supported_timeframes=("M5", "M15", "M30", "H1", "H4", "D1"),
        market_session="INDEX_HOURS",
        price_precision=2,
        quantity_precision=2,
        pip_size=0.1,
        notes="Primary live feed via MT5 broker terminal (USTEC/NAS100).",
    ),
    "SPX500": CanonicalAsset(
        canonical_symbol="SPX500",
        provider_symbol="US500",
        venue="MT5_BROKER",
        asset_class=AssetClass.INDEX,
        quote_currency="USD",
        primary_provider=ProviderType.MT5,
        secondary_providers=(ProviderType.TRADINGVIEW, ProviderType.YFINANCE),
        supported_timeframes=("M5", "M15", "M30", "H1", "H4", "D1"),
        market_session="INDEX_HOURS",
        price_precision=2,
        quantity_precision=2,
        pip_size=0.1,
        notes="Primary live feed via MT5 broker terminal (US500/SPX500).",
    ),
}

# Explicit Alias Transformations: Generic symbols mapped explicitly to canonical instrument
# Transformation is recorded transparently so that no ambiguous mapping goes unlogged.
ALIAS_MAP: Dict[str, Tuple[str, str]] = {
    "BTCUSD": ("BTCUSDT", "Mapped generic BTCUSD to Binance BTCUSDT"),
    "ETHUSD": ("ETHUSDT", "Mapped generic ETHUSD to Binance ETHUSDT"),
    "BTC/USD": ("BTCUSDT", "Mapped delimited BTC/USD to Binance BTCUSDT"),
    "ETH/USD": ("ETHUSDT", "Mapped delimited ETH/USD to Binance ETHUSDT"),
    "EUR/USD": ("EURUSD", "Stripped delimiter for MT5 EURUSD"),
    "GBP/USD": ("GBPUSD", "Stripped delimiter for MT5 GBPUSD"),
    "USD/JPY": ("USDJPY", "Stripped delimiter for MT5 USDJPY"),
    "AUD/USD": ("AUDUSD", "Stripped delimiter for MT5 AUDUSD"),
    "XAU/USD": ("XAUUSD", "Stripped delimiter for MT5 XAUUSD"),
}


class CanonicalAssetRegistry:
    """
    Authoritative single registry managing instruments, venues, providers, and aliases.
    """

    def __init__(self):
        self._assets: Dict[str, CanonicalAsset] = dict(CANONICAL_REGISTRY)

    def resolve(self, symbol: str) -> Optional[Tuple[CanonicalAsset, Optional[str]]]:
        """
        Resolves a symbol to its canonical asset and records any transformation.
        Returns (CanonicalAsset, transformation_note) or None if unmapped.
        """
        sym_clean = symbol.strip().upper()
        if sym_clean in self._assets:
            return self._assets[sym_clean], None

        if sym_clean in ALIAS_MAP:
            target_sym, note = ALIAS_MAP[sym_clean]
            asset = self._assets.get(target_sym)
            if asset:
                return asset, f"{note} (input='{symbol}')"

        return None

    def get(self, canonical_symbol: str) -> Optional[CanonicalAsset]:
        return self._assets.get(canonical_symbol.strip().upper())

    def get_canonical_symbol(self, symbol: str) -> Optional[str]:
        res = self.resolve(symbol)
        return res[0].canonical_symbol if res else None

    def list_canonical_symbols(self) -> List[str]:
        return list(self._assets.keys())

    def list_assets(self) -> List[CanonicalAsset]:
        return list(self._assets.values())

    def get_by_asset_class(self, asset_class: AssetClass) -> List[CanonicalAsset]:
        return [a for a in self._assets.values() if a.asset_class == asset_class]

    def validate_timeframe(self, canonical_symbol: str, timeframe: str) -> bool:
        asset = self.get(canonical_symbol)
        if not asset:
            return False

        tf = timeframe.strip().upper()
        # Normalization mapping across traditional (H1) and duration (1H) notations
        norm_map = {
            "1H": "H1", "H1": "H1", "1h": "H1",
            "2H": "H2", "H2": "H2", "2h": "H2",
            "4H": "H4", "H4": "H4", "4h": "H4",
            "12H": "H12", "H12": "H12", "12h": "H12",
            "1D": "D1", "D1": "D1", "1d": "D1",
            "1W": "W1", "W1": "W1", "1w": "W1",
            "5M": "M5", "M5": "M5", "5m": "M5",
            "15M": "M15", "M15": "M15", "15m": "M15",
            "30M": "M30", "M30": "M30", "30m": "M30",
            "1M": "M1", "M1": "M1", "1m": "M1",
            "3M": "M3", "M3": "M3", "3m": "M3",
            "SWING": "D1",
        }
        canonical_tf = norm_map.get(tf, tf)
        return canonical_tf in asset.supported_timeframes or tf in asset.supported_timeframes


canonical_asset_registry = CanonicalAssetRegistry()
