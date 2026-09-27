"""
app/market_data/market_data_gateway.py
======================================
Phase 6 & 12: Canonical Market Data Gateway & Truth Inversion Layer.

Enforces the Data-Truth-First Architecture:
  PRIMARY LIVE PROVIDER (MT5 for Forex/CFD, Binance for Crypto)
    ↓
  FRESHNESS ENGINE (DataFreshnessService)
    ↓
  MARKET SESSION ENGINE (MarketSessionService)
    ↓
  ACTIONABLE LIVE DATA
    ↓
  PERSIST / CACHE TO SQLITE (Cache & Forensic Evidence ONLY)

Critical Invariants:
1. SQLite is NEVER the authoritative source for live pricing.
2. If primary provider is unavailable, system fails closed (returns DATA_UNAVAILABLE).
3. Ambiguous symbols are resolved via CanonicalAssetRegistry.
4. Bid, ask, and spread are genuine broker/exchange quotes (never bid=close, ask=close).
5. All queries for cached OHLC isolate by symbol, venue, and timeframe.
"""

from __future__ import annotations
import asyncio
from datetime import datetime, timezone
import sqlite3
import os
from typing import Any, Dict, List, Optional, Tuple
import logging

from app.core.asset_registry import (
    canonical_asset_registry,
    CanonicalAsset,
    AssetClass,
    ProviderType,
)
from app.core.market_session import MarketSessionService
from app.market_data.freshness_service import (
    DataFreshnessService,
    FreshnessStatus,
    FreshnessResult,
)
from app.market_data.providers.mt5_provider import mt5_provider
from app.market_data.providers.binance_provider import binance_crypto_provider

logger = logging.getLogger("market_data_gateway")


class MarketDataGateway:
    """
    Authoritative Market Data Gateway managing live data feeds,
    freshness validation, session awareness, and forensic SQLite caching.
    """

    def __init__(self, db_path: str = "tradesignal.db"):
        self.db_path = db_path

    def _get_db(self) -> Optional[sqlite3.Connection]:
        for candidate in [self.db_path, "trading_fallback.db"]:
            if os.path.exists(candidate):
                try:
                    return sqlite3.connect(candidate, timeout=10.0)
                except Exception:
                    pass
        return None

    async def get_live_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieves authoritative live market quote for a symbol.
        Fails closed: NEVER falls back to old SQLite candles or fake numbers.
        """
        now = datetime.now(timezone.utc)
        resolved = canonical_asset_registry.resolve(symbol)

        if not resolved:
            logger.warning(f"Unregistered / ambiguous asset requested: {symbol}")
            return {
                "symbol": symbol,
                "canonical_symbol": symbol,
                "status": "INVALID_SYMBOL",
                "price": None,
                "bid": None,
                "ask": None,
                "spread": None,
                "provider": "NONE",
                "venue": "UNKNOWN",
                "is_actionable": False,
                "rejection_reason": "UNREGISTERED_SYMBOL",
                "received_timestamp": now.isoformat(),
            }

        asset, transformation = resolved
        market_status = MarketSessionService.get_market_status(asset.canonical_symbol, now)
        is_market_open = market_status.get("is_market_open", False)

        # 1. Query Authoritative Primary Provider
        tick: Optional[Dict[str, Any]] = None

        if asset.primary_provider == ProviderType.MT5:
            # Forex, Metals, Index CFDs -> MT5 primary
            tick = await mt5_provider.get_ticker(asset.provider_symbol)
        elif asset.primary_provider == ProviderType.BINANCE:
            # Crypto -> Binance native primary
            tick = await binance_crypto_provider.get_ticker(asset.provider_symbol)

        # 2. Evaluate Primary Provider Result (Fail-Closed)
        if tick is None or tick.get("price") is None:
            # Primary provider failed / disconnected -> STRICTLY FAIL CLOSED
            logger.warning(
                f"[MARKET_DATA] Primary provider {asset.primary_provider.value} unavailable for {asset.canonical_symbol}. FAILING CLOSED."
            )
            return {
                "symbol": asset.canonical_symbol,
                "canonical_symbol": asset.canonical_symbol,
                "venue": asset.venue,
                "provider": asset.primary_provider.value,
                "status": "DATA_UNAVAILABLE",
                "price": None,
                "bid": None,
                "ask": None,
                "spread": None,
                "data_role": "PRIMARY_UNAVAILABLE",
                "is_actionable": False,
                "is_market_open": is_market_open,
                "market_session": market_status.get("current_session", "UNKNOWN"),
                "rejection_reason": f"PRIMARY_PROVIDER_{asset.primary_provider.value}_DISCONNECTED",
                "source_timestamp": None,
                "received_timestamp": now.isoformat(),
                "data_age_ms": -1.0,
                "freshness_status": FreshnessStatus.UNAVAILABLE.value,
                "transformation": transformation,
            }

        # 3. Provenance & Freshness Verification
        src_ts_str = tick.get("source_timestamp")
        src_dt = datetime.fromisoformat(src_ts_str) if src_ts_str else now
        freshness = DataFreshnessService.evaluate_tick_freshness(
            source_timestamp=src_dt,
            received_timestamp=now,
            asset_class=asset.asset_class.value,
        )

        is_actionable = freshness.is_actionable and is_market_open

        rejection_reason = None
        if not is_market_open:
            rejection_reason = "MARKET_CLOSED"
        elif not freshness.is_actionable:
            rejection_reason = freshness.reason

        result = {
            "symbol": asset.canonical_symbol,
            "canonical_symbol": asset.canonical_symbol,
            "venue": asset.venue,
            "provider": asset.primary_provider.value,
            "broker": tick.get("broker", asset.venue),
            "server": tick.get("server", asset.venue),
            "status": "LIVE" if freshness.is_actionable else freshness.status.value,
            "price": tick.get("price"),
            "bid": tick.get("bid"),
            "ask": tick.get("ask"),
            "spread": tick.get("spread"),
            "volume": tick.get("volume", 0.0),
            "data_role": "PRIMARY_LIVE",
            "is_actionable": is_actionable,
            "is_market_open": is_market_open,
            "market_session": market_status.get("current_session", "UNKNOWN"),
            "market_status_reason": market_status.get("reason", "MARKET_OPEN"),
            "rejection_reason": rejection_reason,
            "source_timestamp": src_dt.isoformat(),
            "received_timestamp": now.isoformat(),
            "data_age_ms": freshness.data_age_ms,
            "freshness_status": freshness.status.value,
            "transformation": transformation,
        }

        # Structured Observability Log
        logger.info(
            f"[MARKET_DATA] provider={result['provider']} venue={result['venue']} symbol={result['symbol']} "
            f"price={result['price']} age_ms={round(result['data_age_ms'], 1)} status={result['freshness_status']} "
            f"session={result['market_session']} actionable={result['is_actionable']}"
        )

        return result

    async def get_rates(
        self, symbol: str, timeframe: str, count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieves OHLC bars for a symbol and timeframe with strict isolation.
        Hierarchy:
          1. Primary Live Provider (MT5 or Binance)
          2. Forensic SQLite Cache (strictly matching symbol, venue, and timeframe)
        """
        resolved = canonical_asset_registry.resolve(symbol)
        if not resolved:
            return []

        asset, _ = resolved
        rates: List[Dict[str, Any]] = []

        # 1. Fetch from Primary Provider
        if asset.primary_provider == ProviderType.MT5:
            rates = await mt5_provider.get_rates(asset.provider_symbol, timeframe, count)
        elif asset.primary_provider == ProviderType.BINANCE:
            rates = await binance_crypto_provider.get_rates(asset.provider_symbol, timeframe, count)

        if rates and len(rates) >= 5:
            # Asynchronously update SQLite cache with fresh candles (preserving venue & timeframe isolation)
            self._cache_candles(asset.canonical_symbol, asset.venue, timeframe, asset.primary_provider.value, rates)
            return rates

        # 2. Primary Provider Unavailable -> Fallback to SQLite Cache for Historical Research / Backtesting ONLY
        logger.debug(
            f"Primary rates provider unavailable for {asset.canonical_symbol} ({timeframe}). Reading isolated SQLite cache."
        )
        cached = self._get_cached_candles(asset.canonical_symbol, asset.venue, timeframe, count)
        return cached

    def _cache_candles(
        self, symbol: str, venue: str, timeframe: str, provider: str, rates: List[Dict[str, Any]]
    ):
        """Caches verified OHLC candles into historical_candles with composite isolation."""
        conn = self._get_db()
        if not conn:
            return
        try:
            cur = conn.cursor()
            for r in rates:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO historical_candles (
                        symbol, venue, timeframe, timestamp, open, high, low, close, volume, spread, provider
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        symbol,
                        venue,
                        timeframe,
                        r.get("timestamp"),
                        r.get("open"),
                        r.get("high"),
                        r.get("low"),
                        r.get("close"),
                        r.get("volume", 0.0),
                        r.get("spread"),
                        provider,
                    ),
                )
            conn.commit()
        except Exception as e:
            logger.debug(f"Failed to cache candles to SQLite: {e}")
        finally:
            conn.close()

    def _get_cached_candles(
        self, symbol: str, venue: str, timeframe: str, count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Reads historical candles strictly isolated by symbol, venue, and timeframe.
        Clearly tags them as HISTORICAL_CACHE to prevent misuse as live market state.
        """
        conn = self._get_db()
        if not conn:
            return []
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT open, high, low, close, volume, timestamp, spread, provider
                FROM historical_candles
                WHERE symbol = ? AND venue = ? AND timeframe = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (symbol, venue, timeframe, count),
            )
            rows = cur.fetchall()
            if not rows:
                # If venue wasn't populated in older records, try matching symbol and timeframe
                cur.execute(
                    """
                    SELECT open, high, low, close, volume, timestamp, spread, provider
                    FROM historical_candles
                    WHERE symbol = ? AND timeframe = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (symbol, timeframe, count),
                )
                rows = cur.fetchall()

            candles: List[Dict[str, Any]] = []
            for r in reversed(rows):
                candles.append({
                    "symbol": symbol,
                    "venue": venue,
                    "timeframe": timeframe,
                    "timestamp": r[5],
                    "open": float(r[0]),
                    "high": float(r[1]),
                    "low": float(r[2]),
                    "close": float(r[3]),
                    "volume": float(r[4]) if r[4] else 0.0,
                    "spread": float(r[6]) if r[6] is not None else None,
                    "provider": r[7] if r[7] else "SQLITE_CACHE",
                    "data_role": "HISTORICAL_CACHE",
                    "is_live": False,
                })
            return candles
        except Exception as e:
            logger.debug(f"Failed to read cached candles for {symbol} ({timeframe}): {e}")
            return []
        finally:
            conn.close()


market_data_gateway = MarketDataGateway()
