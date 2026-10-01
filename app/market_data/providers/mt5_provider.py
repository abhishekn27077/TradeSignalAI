"""
app/market_data/providers/mt5_provider.py
=========================================
Phase 79: Primary Forex & CFD Market Data Provider via MetaTrader 5 Python SDK.

Authoritative Provider for:
- FOREX (EURUSD, GBPUSD, USDJPY, AUDUSD)
- METALS (XAUUSD)
- INDEX CFDs (NAS100, SPX500)

Invariants & Acceptance Criteria:
- Detects installed Windows MT5 terminal across common paths and MT5_TERMINAL_PATH.
- Initializes against locally configured terminal session without embedding credentials.
- Distinguishes exact failure diagnostics:
  * MT5_TERMINAL_NOT_FOUND
  * MT5_INITIALIZATION_FAILED
  * MT5_NOT_CONNECTED
  * MT5_ACCOUNT_NOT_LOGGED_IN
  * MT5_AUTHORIZATION_FAILED
  * MT5_SYMBOL_NOT_FOUND
  * MT5_SYMBOL_NOT_VISIBLE
  * MT5_NO_TICK
  * MT5_STALE_TICK
  * MT5_INVALID_TICK
  * MT5_MARKET_CLOSED
  * MT5_PROVIDER_READY
- Resolves broker-specific symbols dynamically for 7 canonical assets:
  EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD, NAS100, SPX500.
- Validates live ticks (bid > 0, ask > 0, ask >= bid, timestamp not future or stale).
- Enforces single canonical freshness policy: LIVE_TICK_MAX_AGE_SECONDS = 120.0.
- Validates market trading sessions (Forex weekend closure and CFD tradability).
- Fails closed if MT5 is unauthorized or disconnected; NEVER substitutes fake prices,
  Binance, Yahoo, or SQLite historical data as live Forex authority.
- Exposes strictly safe diagnostic metadata and safe user remediation guidance.
"""

from __future__ import annotations
import asyncio
from datetime import datetime, timezone, timedelta
from enum import Enum
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional, Tuple

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


class MT5DiagnosticReason(str, Enum):
    MT5_TERMINAL_NOT_FOUND = "MT5_TERMINAL_NOT_FOUND"
    MT5_INITIALIZATION_FAILED = "MT5_INITIALIZATION_FAILED"
    MT5_NOT_CONNECTED = "MT5_NOT_CONNECTED"
    MT5_ACCOUNT_NOT_LOGGED_IN = "MT5_ACCOUNT_NOT_LOGGED_IN"
    MT5_AUTHORIZATION_FAILED = "MT5_AUTHORIZATION_FAILED"
    MT5_SYMBOL_NOT_FOUND = "MT5_SYMBOL_NOT_FOUND"
    MT5_SYMBOL_NOT_VISIBLE = "MT5_SYMBOL_NOT_VISIBLE"
    MT5_NO_TICK = "MT5_NO_TICK"
    MT5_STALE_TICK = "MT5_STALE_TICK"
    MT5_INVALID_TICK = "MT5_INVALID_TICK"
    MT5_MARKET_CLOSED = "MT5_MARKET_CLOSED"
    MT5_PROVIDER_READY = "MT5_PROVIDER_READY"


# Single Canonical Freshness Policy (Part A9)
LIVE_TICK_MAX_AGE_SECONDS: float = 120.0

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

# 7 Canonical Assets for MT5
CANONICAL_MT5_ASSETS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "NAS100", "SPX500"]

# Known Broker Alias Map for Non-Standard Naming
CANONICAL_ASSET_ALIASES: Dict[str, List[str]] = {
    "EURUSD": ["EURUSD", "EURUSDm", "EURUSD.a", "EURUSD.pro", "EURUSD#", "EURUSD_i", "EURUSDecn", "EURUSD.r", "EURUSD.c"],
    "GBPUSD": ["GBPUSD", "GBPUSDm", "GBPUSD.a", "GBPUSD.pro", "GBPUSD#", "GBPUSD_i", "GBPUSDecn", "GBPUSD.r", "GBPUSD.c"],
    "USDJPY": ["USDJPY", "USDJPYm", "USDJPY.a", "USDJPY.pro", "USDJPY#", "USDJPY_i", "USDJPYecn", "USDJPY.r", "USDJPY.c"],
    "AUDUSD": ["AUDUSD", "AUDUSDm", "AUDUSD.a", "AUDUSD.pro", "AUDUSD#", "AUDUSD_i", "AUDUSDecn", "AUDUSD.r", "AUDUSD.c"],
    "XAUUSD": ["XAUUSD", "GOLD", "XAUUSDm", "XAUUSD.a", "XAUUSD.pro", "XAUUSD#", "GOLDm", "GOLD.a", "GOLD.pro"],
    "NAS100": ["NAS100", "USTEC", "US100", "NAS100.cash", "NDX", "US Tech 100", "NASUSD", "NQ", "USTECm", "NAS100m"],
    "SPX500": ["SPX500", "US500", "SP500", "SPX500.cash", "USA500", "US 500", "SPXUSD", "ES", "US500m", "SPX500m"],
}

SAFE_REMEDIATION_GUIDANCE: List[str] = [
    "1. Start MetaTrader 5 on your local Windows workstation.",
    "2. Log into the intended broker demo/live account inside the MT5 terminal.",
    "3. Confirm the terminal status bar shows 'Connected' with active green data transfer.",
    "4. Confirm the required symbol exists in your broker instrument specification.",
    "5. Confirm the symbol is visible in the Market Watch window (Ctrl+M).",
    "6. Return to TradeSignalAI and refresh the provider status.",
]


class MT5DataProvider(BaseDataProvider):
    """
    Primary Market Data Provider using official MetaTrader 5 API with dynamic
    terminal discovery, broker symbol resolution, session validation, and
    fail-closed diagnostics.
    """

    KNOWN_BROKER_SUFFIXES = ["", "m", ".a", "#", ".pro", "_i", "ecn", ".r", ".c", "+", ".cash"]

    def __init__(self):
        self._connected = False
        self._broker_name: str = "MetaQuotes Software Corp."
        self._server_name: str = "Demo"
        self._company_name: str = "MetaQuotes Ltd."
        self._terminal_build: Optional[int] = None
        self._account_login: Optional[int] = None
        self._account_currency: Optional[str] = None
        self._account_trade_mode: Optional[str] = None
        self._account_leverage: Optional[int] = None
        self._discovered_terminal_path: Optional[str] = None
        self._last_connect_failure: Optional[datetime] = None
        self._connect_cooldown_seconds: float = 15.0
        self._resolved_symbol_cache: Dict[str, str] = {}
        self._last_diagnostic_reason: MT5DiagnosticReason = MT5DiagnosticReason.MT5_NOT_CONNECTED
        self._last_error_code: Optional[int] = None
        self._last_error_message: Optional[str] = None
        self._last_successful_tick_time: Optional[datetime] = None
        self._lock = asyncio.Lock()

    @property
    def name(self) -> str:
        return "MT5"

    def discover_terminal_path(self) -> Optional[str]:
        """
        Discovers the MetaTrader 5 terminal executable path on Windows.
        Checks MT5_TERMINAL_PATH, settings.MT5_PATH, and standard installation paths.
        """
        candidates: List[Optional[str]] = [
            os.environ.get("MT5_TERMINAL_PATH"),
            get_settings().MT5_PATH,
            r"C:\Program Files\MetaTrader 5\terminal64.exe",
            r"C:\Program Files\MetaTrader 5\terminal.exe",
            r"C:\Program Files (x86)\MetaTrader 5\terminal.exe",
            r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
        ]

        appdata = os.environ.get("APPDATA", "")
        if appdata:
            candidates.append(os.path.join(appdata, "MetaQuotes", "Terminal", "terminal64.exe"))

        for path in candidates:
            if path and os.path.isfile(path):
                self._discovered_terminal_path = path
                return path

        self._discovered_terminal_path = None
        return None

    def _is_terminal_process_running(self) -> bool:
        """Checks if terminal64.exe or terminal.exe is running via tasklist."""
        try:
            res = subprocess.check_output(
                ["tasklist", "/FI", "IMAGENAME eq terminal64.exe"],
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if "terminal64.exe" in res:
                return True
            res32 = subprocess.check_output(
                ["tasklist", "/FI", "IMAGENAME eq terminal.exe"],
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            return "terminal.exe" in res32
        except Exception:
            return False

    def _should_skip_connect_attempt(self) -> bool:
        if self._last_connect_failure is None:
            return False
        elapsed = (datetime.now(timezone.utc) - self._last_connect_failure).total_seconds()
        return elapsed < self._connect_cooldown_seconds

    async def connect(self) -> bool:
        """
        Connects to the local MetaTrader 5 terminal instance.
        Validates terminal discovery, session authorization, and account info.
        Fails closed with granular MT5DiagnosticReason on any failure.
        """
        if not MT5_AVAILABLE:
            logger.warning("MetaTrader5 Python package not available.")
            self._connected = False
            self._last_diagnostic_reason = MT5DiagnosticReason.MT5_INITIALIZATION_FAILED
            self._last_error_code = -100
            self._last_error_message = "MetaTrader5 Python package not installed"
            return False

        if self._should_skip_connect_attempt():
            return self._connected

        term_path = self.discover_terminal_path()
        if not term_path:
            logger.warning("MetaTrader 5 terminal executable could not be discovered.")
            self._connected = False
            self._last_diagnostic_reason = MT5DiagnosticReason.MT5_TERMINAL_NOT_FOUND
            self._last_error_code = -101
            self._last_error_message = "MetaTrader 5 terminal executable not found on host"
            self._last_connect_failure = datetime.now(timezone.utc)
            return False

        settings = get_settings()
        init_kwargs: Dict[str, Any] = {"path": term_path}
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
                timeout=3.0,
            )
            if res:
                term_info = await loop.run_in_executor(None, mt5.terminal_info)
                acct_info = await loop.run_in_executor(None, mt5.account_info)
                version_info = await loop.run_in_executor(None, mt5.version)

                if version_info and len(version_info) >= 2:
                    self._terminal_build = version_info[1]

                if term_info:
                    self._broker_name = getattr(term_info, "name", "MetaQuotes")
                    self._company_name = getattr(term_info, "company", "MetaQuotes Ltd.")

                if acct_info:
                    self._server_name = getattr(acct_info, "server", "MT5_SERVER")
                    self._account_login = getattr(acct_info, "login", None)
                    self._account_currency = getattr(acct_info, "currency", "USD")
                    self._account_leverage = getattr(acct_info, "leverage", None)
                    trade_mode_code = getattr(acct_info, "trade_mode", 0)
                    self._account_trade_mode = "DEMO" if trade_mode_code == 0 else ("CONTEST" if trade_mode_code == 1 else "REAL")

                # Verify connection state
                if term_info and not getattr(term_info, "connected", False):
                    self._connected = False
                    self._last_diagnostic_reason = MT5DiagnosticReason.MT5_NOT_CONNECTED
                    self._last_error_message = "Terminal running but not connected to broker server"
                    self._last_connect_failure = datetime.now(timezone.utc)
                    return False

                if acct_info is None or getattr(acct_info, "login", 0) == 0:
                    self._connected = False
                    self._last_diagnostic_reason = MT5DiagnosticReason.MT5_ACCOUNT_NOT_LOGGED_IN
                    self._last_error_message = "No active account session in MetaTrader 5 terminal"
                    self._last_connect_failure = datetime.now(timezone.utc)
                    return False

                self._connected = True
                self._last_connect_failure = None
                self._last_error_code = None
                self._last_error_message = None
                self._last_diagnostic_reason = MT5DiagnosticReason.MT5_PROVIDER_READY
                logger.info(f"MT5 connected successfully to {self._broker_name} ({self._server_name})")
                return True
            else:
                err = mt5.last_error()
                err_code = err[0] if isinstance(err, tuple) and len(err) >= 1 else -1
                err_msg = str(err[1]) if isinstance(err, tuple) and len(err) >= 2 else str(err)
                self._last_error_code = err_code
                self._last_error_message = err_msg

                if err_code == -6:
                    self._last_diagnostic_reason = MT5DiagnosticReason.MT5_AUTHORIZATION_FAILED
                elif err_code == -1:
                    self._last_diagnostic_reason = MT5DiagnosticReason.MT5_INITIALIZATION_FAILED
                else:
                    self._last_diagnostic_reason = MT5DiagnosticReason.MT5_INITIALIZATION_FAILED

                logger.warning(f"MT5 initialize failed: {err_code} - {err_msg}")
                self._connected = False
                self._last_connect_failure = datetime.now(timezone.utc)
                return False

        except asyncio.TimeoutError:
            logger.warning("MT5 initialize timed out after 3.0s (terminal unavailable). Failing closed.")
            self._connected = False
            self._last_diagnostic_reason = MT5DiagnosticReason.MT5_INITIALIZATION_FAILED
            self._last_error_code = -2
            self._last_error_message = "Initialization timed out after 3.0s"
            self._last_connect_failure = datetime.now(timezone.utc)
            return False
        except Exception as e:
            logger.error(f"Error during MT5 initialization: {e}")
            self._connected = False
            self._last_diagnostic_reason = MT5DiagnosticReason.MT5_INITIALIZATION_FAILED
            self._last_error_code = -3
            self._last_error_message = str(e)
            self._last_connect_failure = datetime.now(timezone.utc)
            return False

    def resolve_broker_symbol(self, canonical_asset: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Dynamically discovers and verifies the broker-specific symbol for a canonical asset.
        Supports exact match, known aliases, suffix probes, and metadata verification.
        Returns (broker_symbol, symbol_metadata) or None.
        """
        if not MT5_AVAILABLE or not self._connected:
            return None

        clean_symbol = canonical_asset.replace("/", "").replace(":", "").strip().upper()
        candidates_to_try: List[str] = []

        # 1. Exact canonical asset
        candidates_to_try.append(clean_symbol)

        # 2. Known alias list
        if clean_symbol in CANONICAL_ASSET_ALIASES:
            for alias in CANONICAL_ASSET_ALIASES[clean_symbol]:
                if alias not in candidates_to_try:
                    candidates_to_try.append(alias)

        # 3. Suffix variations
        for suffix in self.KNOWN_BROKER_SUFFIXES:
            cand = f"{clean_symbol}{suffix}"
            if cand not in candidates_to_try:
                candidates_to_try.append(cand)

        for candidate in candidates_to_try:
            try:
                info = mt5.symbol_info(candidate)
                if info is not None:
                    # Verify basic symbol properties
                    meta = {
                        "canonical_asset": clean_symbol,
                        "broker_symbol": candidate,
                        "description": getattr(info, "description", ""),
                        "currency_base": getattr(info, "currency_base", ""),
                        "currency_profit": getattr(info, "currency_profit", ""),
                        "digits": getattr(info, "digits", 0),
                        "point": getattr(info, "point", 0.0),
                        "trade_mode": getattr(info, "trade_mode", 0),
                        "visible": getattr(info, "visible", False),
                        "bid": getattr(info, "bid", 0.0),
                        "ask": getattr(info, "ask", 0.0),
                    }
                    self._resolved_symbol_cache[clean_symbol] = candidate
                    return candidate, meta
            except Exception:
                continue

        return None

    def _resolve_broker_symbol(self, canonical_asset: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Backward-compatible private alias for resolve_broker_symbol."""
        return self.resolve_broker_symbol(canonical_asset)

    def is_market_open_for_symbol(self, canonical_asset: str, broker_symbol: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validates whether the market session is open and tradable for the symbol.
        Enforces Sunday weekend closure for Forex and checks broker trade_mode.
        """
        now_utc = datetime.now(timezone.utc)
        weekday = now_utc.weekday()  # Monday is 0, Sunday is 6
        hour = now_utc.hour

        is_forex = canonical_asset in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
        is_metal = canonical_asset in ["XAUUSD"]
        is_cfd_index = canonical_asset in ["NAS100", "SPX500"]

        # Forex Sunday closure: closed Friday 22:00 UTC through Sunday 21:00 UTC
        if is_forex or is_metal:
            if weekday == 5:  # Saturday
                return False, "MARKET_CLOSED_WEEKEND: Saturday global market closure."
            if weekday == 6 and hour < 21:  # Sunday before Asian open
                return False, "MARKET_CLOSED_WEEKEND: Sunday pre-open global market closure."
            if weekday == 4 and hour >= 22:  # Friday post-close
                return False, "MARKET_CLOSED_WEEKEND: Friday post-close weekend session."

        if is_cfd_index:
            if weekday in [5, 6]:
                return False, "MARKET_CLOSED_WEEKEND: Index CFDs closed on weekend."

        if MT5_AVAILABLE and self._connected and broker_symbol:
            try:
                info = mt5.symbol_info(broker_symbol)
                if info is not None:
                    trade_mode = getattr(info, "trade_mode", 0)
                    if hasattr(mt5, "SYMBOL_TRADE_MODE_DISABLED") and trade_mode == mt5.SYMBOL_TRADE_MODE_DISABLED:
                        return False, "MARKET_TRADING_DISABLED: Broker trade mode is disabled for symbol."
            except Exception:
                pass

        return True, "MARKET_OPEN"

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves authoritative live tick for a symbol from MT5 broker terminal.
        Returns None (fails closed) if MT5 is disconnected, tick unavailable, or stale.
        """
        if not self._connected:
            connected = await self.connect()
            if not connected:
                return None

        clean_symbol = symbol.replace("/", "").replace(":", "").strip().upper()
        res = self.resolve_broker_symbol(clean_symbol)
        if not res:
            logger.debug(f"Broker symbol could not be resolved for {clean_symbol}")
            self._last_diagnostic_reason = MT5DiagnosticReason.MT5_SYMBOL_NOT_FOUND
            return None

        broker_symbol, meta = res
        loop = asyncio.get_event_loop()

        try:
            # Ensure symbol is selected in Market Watch (Part A7)
            selected = await loop.run_in_executor(None, lambda: mt5.symbol_select(broker_symbol, True))
            if not selected:
                self._last_diagnostic_reason = MT5DiagnosticReason.MT5_SYMBOL_NOT_VISIBLE
                logger.debug(f"MT5 could not select symbol {broker_symbol} in Market Watch")

            tick = await loop.run_in_executor(None, lambda: mt5.symbol_info_tick(broker_symbol))
            if tick is None:
                self._last_diagnostic_reason = MT5DiagnosticReason.MT5_NO_TICK
                logger.debug(f"MT5 symbol_info_tick returned None for {broker_symbol} ({clean_symbol})")
                return None

            now_utc = datetime.now(timezone.utc)

            # Determine source timestamp
            if hasattr(tick, "time_msc") and tick.time_msc > 0:
                src_time = datetime.fromtimestamp(tick.time_msc / 1000.0, tz=timezone.utc)
            else:
                src_time = datetime.fromtimestamp(tick.time, tz=timezone.utc)

            bid = float(tick.bid) if tick.bid else 0.0
            ask = float(tick.ask) if tick.ask else 0.0
            last = float(tick.last) if hasattr(tick, "last") and tick.last else (bid or ask)

            # Part A8: Validate bid > 0, ask > 0, ask >= bid
            if bid <= 0.0 or ask <= 0.0 or ask < bid:
                self._last_diagnostic_reason = MT5DiagnosticReason.MT5_INVALID_TICK
                logger.warning(f"Invalid MT5 tick geometry for {broker_symbol}: bid={bid}, ask={ask}")
                return None

            mid_price = round((bid + ask) / 2.0, 5 if bid < 500 else 2)
            spread = round(ask - bid, 5 if bid < 500 else 2)
            spread_bps = round((spread / mid_price) * 10000.0, 2) if mid_price > 0 else 0.0

            # Clock sanity: reject future timestamps beyond 5s tolerance
            age_seconds = (now_utc - src_time).total_seconds()
            if age_seconds < -5.0:
                self._last_diagnostic_reason = MT5DiagnosticReason.MT5_INVALID_TICK
                logger.warning(f"MT5 tick timestamp in future: {src_time} (now {now_utc})")
                return None

            data_age_seconds = max(0.0, age_seconds)

            # Part A9: Canonical Freshness Gate
            if data_age_seconds > LIVE_TICK_MAX_AGE_SECONDS:
                self._last_diagnostic_reason = MT5DiagnosticReason.MT5_STALE_TICK
                logger.debug(f"MT5 tick for {broker_symbol} is stale: {data_age_seconds:.1f}s > {LIVE_TICK_MAX_AGE_SECONDS}s")
                return None

            # Part A10: Market session check
            is_open, session_reason = self.is_market_open_for_symbol(clean_symbol, broker_symbol)
            if not is_open:
                self._last_diagnostic_reason = MT5DiagnosticReason.MT5_MARKET_CLOSED
                logger.debug(f"MT5 market session closed for {clean_symbol}: {session_reason}")
                return None

            self._last_successful_tick_time = now_utc
            self._last_diagnostic_reason = MT5DiagnosticReason.MT5_PROVIDER_READY

            return {
                "symbol": clean_symbol,
                "canonical_symbol": clean_symbol,
                "broker_symbol": broker_symbol,
                "price": mid_price or last or bid,
                "mid_price": mid_price,
                "bid": bid,
                "ask": ask,
                "spread": spread,
                "spread_bps": spread_bps,
                "volume": float(getattr(tick, "volume", 0.0)),
                "provider": "MT5",
                "venue": "MT5_BROKER",
                "broker": self._broker_name,
                "server": self._server_name,
                "source_timestamp": src_time.isoformat(),
                "received_timestamp": now_utc.isoformat(),
                "data_age_seconds": round(data_age_seconds, 2),
                "data_age_ms": round(data_age_seconds * 1000.0, 1),
                "freshness_status": "FRESH" if data_age_seconds <= 30.0 else "AGED",
                "is_actionable": True,
            }

        except Exception as e:
            logger.warning(f"MT5 get_ticker failed for {symbol}: {e}")
            return None

    async def get_rates(
        self, symbol: str, timeframe: str, count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieves genuine OHLC bars from MT5 terminal for the requested timeframe.
        Validates candle integrity (Part A12): high >= max(open, close), low <= min(open, close),
        prices > 0, timestamps monotonically increasing, no future candles.
        """
        if not self._connected:
            connected = await self.connect()
            if not connected:
                return []

        clean_symbol = symbol.replace("/", "").replace(":", "").strip().upper()
        res = self.resolve_broker_symbol(clean_symbol)
        if not res:
            return []

        broker_symbol, _ = res
        tf_mt5 = TIMEFRAME_MAP.get(timeframe)
        if tf_mt5 is None:
            logger.warning(f"Unsupported timeframe for MT5: {timeframe}")
            return []

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, lambda: mt5.symbol_select(broker_symbol, True))
            rates = await loop.run_in_executor(
                None, lambda: mt5.copy_rates_from_pos(broker_symbol, tf_mt5, 0, count)
            )
            if rates is None or len(rates) == 0:
                return []

            now_utc = datetime.now(timezone.utc)
            candles: List[Dict[str, Any]] = []
            prev_ts: Optional[datetime] = None

            for r in rates:
                ts = datetime.fromtimestamp(r["time"], tz=timezone.utc)
                o = float(r["open"])
                h = float(r["high"])
                l = float(r["low"])
                c = float(r["close"])
                v = float(r["tick_volume"])

                # Part A12: Strict Candle Validation
                if o <= 0.0 or h <= 0.0 or l <= 0.0 or c <= 0.0:
                    continue  # Reject non-positive price
                if h < max(o, c) or l > min(o, c) or h < l:
                    continue  # Reject impossible candle geometry
                if ts > now_utc + timedelta(seconds=60):
                    continue  # Reject future candle
                if prev_ts is not None and ts <= prev_ts:
                    continue  # Monotonically increasing & duplicate check

                prev_ts = ts
                candles.append({
                    "symbol": clean_symbol,
                    "canonical_symbol": clean_symbol,
                    "broker_symbol": broker_symbol,
                    "timeframe": timeframe,
                    "timestamp": ts.isoformat(),
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": c,
                    "volume": v,
                    "spread": float(r["spread"]) if "spread" in r.dtype.names else None,
                    "provider": "MT5",
                    "venue": "MT5_BROKER",
                    "broker": self._broker_name,
                    "server": self._server_name,
                    "received_timestamp": now_utc.isoformat(),
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
        return OrderBook(
            symbol=symbol,
            timestamp=datetime.now(timezone.utc),
            bids=[],
            asks=[],
        )

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

    def get_safe_diagnostics(self) -> Dict[str, Any]:
        """
        Exposes strictly safe diagnostic status without revealing credentials or secrets.
        Never prints password, investor password, secret token, or auth credentials (Part A4).
        """
        term_path = self.discover_terminal_path()
        terminal_detected = term_path is not None
        terminal_running = self._is_terminal_process_running()

        settings = get_settings()
        account_configured = bool(settings.MT5_LOGIN)
        server_configured = bool(settings.MT5_SERVER)

        connection_state = "CONNECTED" if self._connected else "DISCONNECTED"
        if self._connected:
            authorization_state = "AUTHORIZED"
            status = "ACTIONABLE"
            reason = MT5DiagnosticReason.MT5_PROVIDER_READY.value
        else:
            if not terminal_detected:
                authorization_state = "UNAUTHORIZED"
                reason = MT5DiagnosticReason.MT5_TERMINAL_NOT_FOUND.value
            elif self._last_error_code == -6:
                authorization_state = "UNAUTHORIZED"
                reason = MT5DiagnosticReason.MT5_AUTHORIZATION_FAILED.value
            elif not account_configured and self._account_login is None:
                authorization_state = "UNAUTHORIZED"
                reason = MT5DiagnosticReason.MT5_ACCOUNT_NOT_LOGGED_IN.value
            else:
                authorization_state = "FAILED"
                reason = self._last_diagnostic_reason.value if self._last_diagnostic_reason else MT5DiagnosticReason.MT5_NOT_CONNECTED.value
            status = "BLOCKED / NOT VERIFIED"

        data_age = None
        last_tick_iso = None
        if self._last_successful_tick_time:
            data_age = round(max(0.0, (datetime.now(timezone.utc) - self._last_successful_tick_time).total_seconds()), 2)
            last_tick_iso = self._last_successful_tick_time.isoformat()

        return {
            "provider": "MT5",
            "terminal_detected": terminal_detected,
            "terminal_path": term_path,
            "terminal_running": terminal_running,
            "terminal_build": self._terminal_build,
            "connection_state": connection_state,
            "authorization_state": authorization_state,
            "broker_name": self._broker_name,
            "company_name": self._company_name,
            "server_name": self._server_name,
            "account_login": self._account_login or (int(settings.MT5_LOGIN) if settings.MT5_LOGIN and settings.MT5_LOGIN.isdigit() else None),
            "account_currency": self._account_currency,
            "account_trade_mode": self._account_trade_mode,
            "account_leverage": self._account_leverage,
            "account_present": account_configured or (self._account_login is not None),
            "server_present": server_configured or bool(self._server_name),
            "diagnostic_reason": reason,
            "last_error_code": self._last_error_code,
            "last_error_message": self._last_error_message,
            "last_successful_tick": last_tick_iso,
            "data_age": data_age,
            "status": status,
            "is_actionable": self._connected and (data_age is not None and data_age <= LIVE_TICK_MAX_AGE_SECONDS),
            "safe_remediation_guidance": SAFE_REMEDIATION_GUIDANCE if not self._connected else [],
        }

    def shutdown(self):
        if MT5_AVAILABLE:
            try:
                mt5.shutdown()
            except Exception:
                pass
        self._connected = False


mt5_provider = MT5DataProvider()
MT5MarketDataProvider = MT5DataProvider
