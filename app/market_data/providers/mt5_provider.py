"""
app/market_data/providers/mt5_provider.py
=========================================
Phase 2: Primary Forex & CFD Market Data Provider via MetaTrader 5 Python SDK.

Authoritative Provider for:
- FOREX (EURUSD, GBPUSD, USDJPY, AUDUSD)
- METALS (XAUUSD)
- INDEX CFDs (NAS100, SPX500)

Invariants:
- Real bid, ask, and spread directly from broker terminal.
- Never fabricates bid = close or ask = close.
- If MT5 is disconnected/unavailable, fails closed and returns DATA_UNAVAILABLE.
- Exposes full provenance: provider, broker, server, source_timestamp, received_timestamp, data_age_ms.
"""

from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import logging

from app.config.settings import get_settings
from app.market_data.freshness_service import DataFreshnessService, FreshnessStatus
from app.market_data.providers.base import BaseDataProvider
from app.market_data.types import Candle, OrderBook, Timeframe

logger = logging.getLogger("mt5_provider")

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False


TIMEFRAME_MAP: Dict[str, Any] = {}
if MT5_AVAILABLE:
    TIMEFRAME_MAP = {
        "M1": mt5.TIMEFRAME_M1,
        "1m": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "5m": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "15m": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "30m": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "1h": mt5.TIMEFRAME_H1,
        "1H": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "4h": mt5.TIMEFRAME_H4,
        "4H": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
        "1d": mt5.TIMEFRAME_D1,
        "1D": mt5.TIMEFRAME_D1,
    }


class MT5DataProvider(BaseDataProvider):
    """
    Primary Market Data Provider using official MetaTrader 5 API.
    """

    def __init__(self):
        self._connected = False
        self._broker_name: str = "MetaQuotes Software Corp."
        self._server_name: str = "Demo"
        self._login: Optional[int] = None
        self._lock = asyncio.Lock()

    @property
    def name(self) -> str:
        return "MT5"

    async def connect(self) -> bool:
        if not MT5_AVAILABLE:
            logger.warning("MetaTrader5 python package not available.")
            self._connected = False
            return False

        settings = get_settings()
        init_kwargs: Dict[str, Any] = {}
        if settings.MT5_PATH:
            init_kwargs["path"] = settings.MT5_PATH
        if settings.MT5_LOGIN:
            try:
                init_kwargs["login"] = int(settings.MT5_LOGIN)
            except ValueError:
                pass
        if settings.MT5_PASSWORD:
            init_kwargs["password"] = settings.MT5_PASSWORD
        if settings.MT5_SERVER:
            init_kwargs["server"] = settings.MT5_SERVER

        loop = asyncio.get_event_loop()
        try:
            res = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: mt5.initialize(**init_kwargs)),
                timeout=2.0,
            )
            if res:
                self._connected = True
                term_info = await loop.run_in_executor(None, mt5.terminal_info)
                acct_info = await loop.run_in_executor(None, mt5.account_info)
                if term_info:
                    self._broker_name = getattr(term_info, "name", "MT5_BROKER")
                if acct_info:
                    self._server_name = getattr(acct_info, "server", "MT5_SERVER")
                    self._login = getattr(acct_info, "login", None)
                logger.info(f"MT5 connected successfully to {self._broker_name} ({self._server_name})")
                return True
            else:
                err = mt5.last_error()
                logger.warning(f"MT5 initialize failed: {err}")
                self._connected = False
                return False
        except asyncio.TimeoutError:
            logger.warning("MT5 initialize timed out after 2.0s (terminal unavailable). Failing closed.")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"Error during MT5 initialization: {e}")
            self._connected = False
            return False

    async def check_health(self) -> bool:
        if not MT5_AVAILABLE:
            return False
        loop = asyncio.get_event_loop()
        try:
            info = await loop.run_in_executor(None, mt5.terminal_info)
            if info and getattr(info, "connected", False):
                self._connected = True
                return True
        except Exception:
            pass
        self._connected = False
        return False

    async def is_connected(self) -> bool:
        return self._connected

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves authoritative live tick for a symbol from MT5 broker terminal.
        Returns None (fails closed) if MT5 is disconnected or tick unavailable.
        """
        if not self._connected:
            connected = await self.connect()
            if not connected:
                return None

        clean_symbol = symbol.replace("/", "").strip()
        loop = asyncio.get_event_loop()
        try:
            # Ensure symbol is selected in Market Watch
            await loop.run_in_executor(None, lambda: mt5.symbol_select(clean_symbol, True))
            tick = await loop.run_in_executor(None, lambda: mt5.symbol_info_tick(clean_symbol))
            if tick is None:
                logger.debug(f"MT5 symbol_info_tick returned None for {clean_symbol}")
                return None

            rec_time = datetime.now(timezone.utc)

            # Determine source timestamp from tick
            if hasattr(tick, "time_msc") and tick.time_msc > 0:
                src_time = datetime.fromtimestamp(tick.time_msc / 1000.0, tz=timezone.utc)
            else:
                src_time = datetime.fromtimestamp(tick.time, tz=timezone.utc)

            bid = float(tick.bid) if tick.bid else None
            ask = float(tick.ask) if tick.ask else None
            last = float(tick.last) if hasattr(tick, "last") and tick.last else (bid or ask)
            spread = (ask - bid) if (ask is not None and bid is not None) else None

            # Freshness calculation
            freshness = DataFreshnessService.evaluate_tick_freshness(
                source_timestamp=src_time,
                received_timestamp=rec_time,
                asset_class="FOREX",
            )

            return {
                "symbol": clean_symbol,
                "canonical_symbol": clean_symbol,
                "price": last or bid,
                "bid": bid,
                "ask": ask,
                "spread": spread,
                "volume": float(getattr(tick, "volume", 0.0)),
                "provider": "MT5",
                "venue": "MT5_BROKER",
                "broker": self._broker_name,
                "server": self._server_name,
                "source_timestamp": src_time.isoformat(),
                "received_timestamp": rec_time.isoformat(),
                "data_age_ms": freshness.data_age_ms,
                "freshness_status": freshness.status.value,
                "is_actionable": freshness.is_actionable,
            }
        except Exception as e:
            logger.warning(f"MT5 get_ticker failed for {symbol}: {e}")
            return None

    async def get_rates(
        self, symbol: str, timeframe: str, count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieves genuine OHLC bars from MT5 terminal for the requested timeframe.
        """
        if not self._connected:
            connected = await self.connect()
            if not connected:
                return []

        clean_symbol = symbol.replace("/", "").strip()
        tf_mt5 = TIMEFRAME_MAP.get(timeframe)
        if tf_mt5 is None:
            logger.warning(f"Unsupported timeframe for MT5: {timeframe}")
            return []

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, lambda: mt5.symbol_select(clean_symbol, True))
            rates = await loop.run_in_executor(
                None, lambda: mt5.copy_rates_from_pos(clean_symbol, tf_mt5, 0, count)
            )
            if rates is None or len(rates) == 0:
                logger.debug(f"MT5 copy_rates_from_pos returned no rates for {clean_symbol}")
                return []

            rec_time = datetime.now(timezone.utc)
            candles: List[Dict[str, Any]] = []

            for r in rates:
                ts = datetime.fromtimestamp(r["time"], tz=timezone.utc)
                candles.append({
                    "symbol": clean_symbol,
                    "canonical_symbol": clean_symbol,
                    "timeframe": timeframe,
                    "timestamp": ts.isoformat(),
                    "open": float(r["open"]),
                    "high": float(r["high"]),
                    "low": float(r["low"]),
                    "close": float(r["close"]),
                    "volume": float(r["tick_volume"]),
                    "spread": float(r["spread"]) if "spread" in r.dtype.names else None,
                    "provider": "MT5",
                    "venue": "MT5_BROKER",
                    "broker": self._broker_name,
                    "server": self._server_name,
                    "received_timestamp": rec_time.isoformat(),
                })
            return candles
        except Exception as e:
            logger.warning(f"MT5 get_rates failed for {symbol} ({timeframe}): {e}")
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
        # MT5 does not provide Level 2 orderbook on all broker accounts without special subscription
        return OrderBook(
            symbol=symbol,
            timestamp=datetime.now(timezone.utc),
            bids=[],
            asks=[],
        )

    def shutdown(self):
        if MT5_AVAILABLE:
            try:
                mt5.shutdown()
            except Exception:
                pass
        self._connected = False


mt5_provider = MT5DataProvider()
MT5MarketDataProvider = MT5DataProvider
