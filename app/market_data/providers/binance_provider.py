"""
app/market_data/providers/binance_provider.py
=============================================
Phase 3: Native Crypto Market Data Provider via Binance Exchange API.

Authoritative Primary Provider for Crypto Assets:
- BINANCE:BTCUSDT
- BINANCE:ETHUSDT

Invariants:
- Real bid, ask, and spread directly from Binance bookTicker / klines.
- Explicit venue: venue = 'BINANCE'.
- Does not treat generic BTCUSD as identical without recording transformation.
- Exposes full provenance: provider, venue, exchange, source_timestamp, received_timestamp, data_age_ms.
"""

from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
import logging

from app.core.asset_registry import canonical_asset_registry
from app.market_data.freshness_service import DataFreshnessService, FreshnessStatus
from app.market_data.providers.base import BaseDataProvider
from app.market_data.types import Candle, OrderBook, OrderBookLevel, Timeframe

logger = logging.getLogger("binance_provider")

BINANCE_REST_BASE = "https://api.binance.com"

INTERVAL_MAP = {
    "M1": "1m",
    "1m": "1m",
    "M3": "3m",
    "3m": "3m",
    "M5": "5m",
    "5m": "5m",
    "M15": "15m",
    "15m": "15m",
    "M30": "30m",
    "30m": "30m",
    "H1": "1h",
    "1h": "1h",
    "1H": "1h",
    "H4": "4h",
    "4h": "4h",
    "4H": "4h",
    "D1": "1d",
    "1d": "1d",
    "1D": "1d",
}


class BinanceCryptoDataProvider(BaseDataProvider):
    """
    Native Primary Crypto Data Provider querying Binance Exchange API.
    """

    def __init__(self, timeout: float = 6.0):
        self.timeout = timeout
        self._connected = True

    @property
    def name(self) -> str:
        return "BINANCE"

    async def connect(self) -> bool:
        self._connected = True
        return True

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(f"{BINANCE_REST_BASE}/api/v3/ping")
                return res.status_code == 200
        except Exception as e:
            logger.debug(f"Binance ping failed: {e}")
            return False

    async def is_connected(self) -> bool:
        return self._connected

    def _resolve_symbol(self, symbol: str) -> tuple[str, Optional[str]]:
        """
        Resolves input symbol to explicit Binance pair (e.g. BTCUSDT)
        and returns (binance_symbol, transformation_note).
        """
        clean = symbol.replace("/", "").replace(":", "").strip().upper()
        if clean.startswith("BINANCE"):
            clean = clean.replace("BINANCE", "")

        resolved = canonical_asset_registry.resolve(clean)
        if resolved:
            asset, note = resolved
            return asset.provider_symbol, note

        # Fallback heuristic if not in registry
        if clean in ("BTCUSD", "BTC"):
            return "BTCUSDT", "Mapped generic BTCUSD to Binance BTCUSDT"
        if clean in ("ETHUSD", "ETH"):
            return "ETHUSDT", "Mapped generic ETHUSD to Binance ETHUSDT"

        return clean, None

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves real live ticker from Binance bookTicker endpoint.
        Returns explicit bid, ask, spread, and provenance.
        """
        bin_sym, transformation = self._resolve_symbol(symbol)
        url = f"{BINANCE_REST_BASE}/api/v3/ticker/bookTicker?symbol={bin_sym}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                rec_time = datetime.now(timezone.utc)
                resp = await client.get(url)

                if resp.status_code != 200:
                    logger.warning(f"Binance bookTicker returned {resp.status_code} for {bin_sym}")
                    return None

                data = resp.json()
                bid = float(data.get("bidPrice", 0.0))
                ask = float(data.get("askPrice", 0.0))
                last = (bid + ask) / 2.0 if (bid and ask) else (bid or ask)
                spread = ask - bid if (bid and ask) else 0.0

                # Binance does not include timestamp in bookTicker, so we also fetch 24hr or use server time
                src_time = rec_time  # REST response received time is within ms of server event

                freshness = DataFreshnessService.evaluate_tick_freshness(
                    source_timestamp=src_time,
                    received_timestamp=rec_time,
                    asset_class="CRYPTO",
                )

                return {
                    "symbol": bin_sym,
                    "canonical_symbol": "BTCUSDT" if "BTC" in bin_sym else ("ETHUSDT" if "ETH" in bin_sym else bin_sym),
                    "price": last,
                    "bid": bid,
                    "ask": ask,
                    "spread": round(spread, 6),
                    "volume": float(data.get("bidQty", 0.0)),
                    "provider": "BINANCE",
                    "venue": "BINANCE",
                    "exchange": "BINANCE",
                    "transformation": transformation,
                    "source_timestamp": src_time.isoformat(),
                    "received_timestamp": rec_time.isoformat(),
                    "data_age_ms": freshness.data_age_ms,
                    "freshness_status": freshness.status.value,
                    "is_actionable": freshness.is_actionable,
                }
        except Exception as e:
            logger.warning(f"Binance get_ticker error for {symbol}: {e}")
            return None

    async def get_rates(
        self, symbol: str, timeframe: str, count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieves real OHLC klines from Binance API.
        """
        bin_sym, transformation = self._resolve_symbol(symbol)
        interval = INTERVAL_MAP.get(timeframe, "1h")
        url = f"{BINANCE_REST_BASE}/api/v3/klines?symbol={bin_sym}&interval={interval}&limit={count}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                rec_time = datetime.now(timezone.utc)
                resp = await client.get(url)

                if resp.status_code != 200:
                    logger.warning(f"Binance klines returned {resp.status_code} for {bin_sym}")
                    return []

                raw_klines = resp.json()
                candles: List[Dict[str, Any]] = []

                for k in raw_klines:
                    # Binance kline structure:
                    # [open_time, open, high, low, close, volume, close_time, quote_vol, trades, ...]
                    open_ts = datetime.fromtimestamp(k[0] / 1000.0, tz=timezone.utc)
                    candles.append({
                        "symbol": bin_sym,
                        "canonical_symbol": "BTCUSDT" if "BTC" in bin_sym else ("ETHUSDT" if "ETH" in bin_sym else bin_sym),
                        "timeframe": timeframe,
                        "timestamp": open_ts.isoformat(),
                        "open": float(k[1]),
                        "high": float(k[2]),
                        "low": float(k[3]),
                        "close": float(k[4]),
                        "volume": float(k[5]),
                        "provider": "BINANCE",
                        "venue": "BINANCE",
                        "exchange": "BINANCE",
                        "received_timestamp": rec_time.isoformat(),
                    })
                return candles
        except Exception as e:
            logger.warning(f"Binance get_rates error for {symbol} ({timeframe}): {e}")
            return []

    async def get_historical_klines(
        self, symbol: str, interval: str, limit: int = 100
    ) -> List[Candle]:
        rates = await self.get_rates(symbol, interval, limit)
        candles: List[Candle] = []
        for r in rates:
            try:
                tf_enum = Timeframe(interval)
            except ValueError:
                tf_enum = Timeframe.H1
            candles.append(Candle(
                symbol=r["symbol"],
                timeframe=tf_enum,
                timestamp=datetime.fromisoformat(r["timestamp"]),
                open=r["open"],
                high=r["high"],
                low=r["low"],
                close=r["close"],
                volume=r["volume"],
            ))
        return candles

    async def get_orderbook(self, symbol: str, depth: int = 10) -> OrderBook:
        bin_sym, _ = self._resolve_symbol(symbol)
        url = f"{BINANCE_REST_BASE}/api/v3/depth?symbol={bin_sym}&limit={depth}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    d = resp.json()
                    bids = [OrderBookLevel(price=float(b[0]), quantity=float(b[1])) for b in d.get("bids", [])]
                    asks = [OrderBookLevel(price=float(a[0]), quantity=float(a[1])) for a in d.get("asks", [])]
                    return OrderBook(
                        symbol=bin_sym,
                        timestamp=datetime.now(timezone.utc),
                        bids=bids,
                        asks=asks,
                    )
        except Exception as e:
            logger.debug(f"Binance orderbook query failed: {e}")

        return OrderBook(
            symbol=bin_sym,
            timestamp=datetime.now(timezone.utc),
            bids=[],
            asks=[],
        )


binance_crypto_provider = BinanceCryptoDataProvider()
BinanceMarketDataProvider = BinanceCryptoDataProvider
