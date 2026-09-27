import asyncio
import io
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any

try:
    from tvDatafeed import Interval, TvDatafeed
    TV_DATAFEED_AVAILABLE = True
except ImportError:
    TV_DATAFEED_AVAILABLE = False
    class Interval:  # type: ignore
        in_1_minute = "1m"
        in_3_minute = "3m"
        in_5_minute = "5m"
        in_15_minute = "15m"
        in_30_minute = "30m"
        in_1_hour = "1h"
        in_2_hour = "2h"
        in_4_hour = "4h"
        in_daily = "1d"
        in_weekly = "1w"
        in_monthly = "1M"
    TvDatafeed = None  # type: ignore

from app.config.settings import get_settings
from app.logs.logger import get_logger
from app.market_data.providers.base import BaseDataProvider
from app.market_data.types import Candle, OrderBook, Timeframe

logger = get_logger(__name__)

# ── Silence tvDatafeed's own stdout/stderr prints ─────────────────────────────
@contextmanager
def _suppress_tv_output():
    """Redirect tvDatafeed's noisy stdout/stderr to /dev/null during calls."""
    old_stdout, old_stderr = sys.stdout, sys.stderr
    try:
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


class TradingViewDataProvider(BaseDataProvider):
    """
    Market Data Provider using tvDatafeed to fetch data from TradingView.

    Circuit Breaker: after CIRCUIT_FAIL_THRESHOLD consecutive failures,
    the provider stops making requests for CIRCUIT_COOLDOWN_SECS seconds.
    This prevents the console from being flooded with repeated errors.
    """

    CIRCUIT_FAIL_THRESHOLD = 5          # Open circuit after 5 consecutive failures
    CIRCUIT_COOLDOWN_SECS  = 300        # Stay open for 5 minutes before retrying

    def __init__(self):
        self.settings = get_settings()
        self._connected = False
        self._tv = None

        # Circuit breaker state
        self._consecutive_failures = 0
        self._circuit_open_until: float = 0.0   # epoch seconds

        self._interval_map = {
            Timeframe.M1: Interval.in_1_minute,
            Timeframe.M3: Interval.in_3_minute,
            Timeframe.M5: Interval.in_5_minute,
            Timeframe.M15: Interval.in_15_minute,
            Timeframe.M30: Interval.in_30_minute,
            Timeframe.H1: Interval.in_1_hour,
            Timeframe.H4: Interval.in_4_hour,
            Timeframe.D1: Interval.in_daily,
            Timeframe.W1: Interval.in_weekly,
            Timeframe.MN1: Interval.in_monthly,
        }

        self.default_exchange = "BINANCE"

    @property
    def name(self) -> str:
        return "tradingview"

    # ── Circuit Breaker ────────────────────────────────────────────────────────

    def _is_circuit_open(self) -> bool:
        if self._consecutive_failures >= self.CIRCUIT_FAIL_THRESHOLD:
            if time.time() < self._circuit_open_until:
                return True
            # Cooldown expired — allow one probe attempt
            logger.info("TradingView circuit breaker: cooldown expired, probing...")
            self._consecutive_failures = 0
        return False

    def _record_failure(self):
        self._consecutive_failures += 1
        self._connected = False
        if self._consecutive_failures >= self.CIRCUIT_FAIL_THRESHOLD:
            self._circuit_open_until = time.time() + self.CIRCUIT_COOLDOWN_SECS
            logger.warning(
                f"TradingView circuit breaker OPEN after {self._consecutive_failures} "
                f"consecutive failures. Pausing requests for {self.CIRCUIT_COOLDOWN_SECS}s."
            )

    def _record_success(self):
        self._consecutive_failures = 0
        self._circuit_open_until = 0.0

    # ── Connection ────────────────────────────────────────────────────────────

    async def connect(self) -> bool:
        if not TV_DATAFEED_AVAILABLE:
            self._connected = False
            return False
        if self._connected:
            return True
        if self._is_circuit_open():
            return False

        loop = asyncio.get_event_loop()
        retries = 3

        for attempt in range(retries):
            try:
                if self.settings.TV_USERNAME and self.settings.TV_PASSWORD:
                    self._tv = await loop.run_in_executor(
                        None,
                        lambda: TvDatafeed(self.settings.TV_USERNAME, self.settings.TV_PASSWORD)
                    )
                else:
                    with _suppress_tv_output():
                        self._tv = await loop.run_in_executor(None, TvDatafeed)

                self._connected = True
                self._record_success()
                logger.info("TradingView Data Provider connected successfully.")
                return True
            except Exception as e:
                logger.warning(f"TradingView connect attempt {attempt + 1}/{retries}: {e}")
                await asyncio.sleep(2 ** attempt)

        self._record_failure()
        return False

    async def check_health(self) -> bool:
        if self._is_circuit_open():
            return False
        if not self._connected:
            if not await self.connect():
                return False

        retries = 2
        for attempt in range(retries):
            try:
                loop = asyncio.get_event_loop()
                with _suppress_tv_output():
                    res = await loop.run_in_executor(
                        None, self._tv.get_hist, "BTCUSD", "BINANCE", Interval.in_1_minute, 1
                    )
                if res is not None and not res.empty:
                    self._record_success()
                    return True
            except Exception as e:
                logger.debug(f"TradingView health check attempt {attempt+1}: {e}")
                if attempt < retries - 1:
                    self._connected = False
                    await self.connect()

        self._record_failure()
        return False

    async def is_connected(self) -> bool:
        return self._connected

    def _split_symbol_exchange(self, symbol: str) -> tuple[str, str]:
        # Normalize symbol formatting (remove slashes, etc.)
        normalized_symbol = symbol.replace("/", "").replace("-", "").upper()

        if ":" in normalized_symbol:
            exchange, sym = normalized_symbol.split(":", 1)
            return sym, exchange

        if normalized_symbol in ["NAS100", "SPX500", "US30", "XAUUSD"]:
            return normalized_symbol, "BLACKBULL"

        if normalized_symbol.endswith("USD") or normalized_symbol.endswith("USDT"):
            # Binance uses USDT instead of USD for most spot pairs
            if normalized_symbol.endswith("USD") and not normalized_symbol.endswith("USDT"):
                # If they asked for BTCUSD, give them BTCUSDT for Binance
                binance_sym = normalized_symbol.replace("USD", "USDT")
                return binance_sym, "BINANCE"
            return normalized_symbol, "BINANCE"
        if symbol in ["AAPL", "TSLA", "MSFT", "GOOGL"]:
            return symbol, "NASDAQ"

        return symbol, self.default_exchange

    async def get_ticker(self, symbol: str) -> dict[str, Any] | None:
        if self._is_circuit_open():
            return None
        try:
            if not self._connected:
                await self.connect()

            sym, exchange = self._split_symbol_exchange(symbol)
            loop = asyncio.get_event_loop()

            with _suppress_tv_output():
                df = await loop.run_in_executor(
                    None, self._tv.get_hist, sym, exchange, Interval.in_1_minute, 1
                )

            if df is not None and not df.empty:
                last_row = df.iloc[-1]
                self._record_success()
                return {
                    "symbol": symbol,
                    "price": float(last_row['close']),
                    "volume": float(last_row.get('volume', 0.0)),
                    "timestamp": last_row.name.isoformat() if hasattr(last_row, 'name') and last_row.name else datetime.utcnow().isoformat()
                }
            else:
                logger.debug(f"TradingView get_hist returned empty for {symbol}")
                self._record_failure()
            return None
        except Exception as e:
            logger.debug(f"TradingView get_ticker({symbol}): {e}")
            self._record_failure()
            return None

    async def get_rates(self, symbol: str, timeframe: str, count: int = 100) -> list[dict[str, Any]]:
        if self._is_circuit_open():
            return []
        try:
            if not self._connected:
                await self.connect()

            sym, exchange = self._split_symbol_exchange(symbol)

            tf_enum = None
            for t in Timeframe:
                if t.value == timeframe:
                    tf_enum = t
                    break

            interval = self._interval_map.get(tf_enum, Interval.in_1_minute)

            loop = asyncio.get_event_loop()
            with _suppress_tv_output():
                df = await loop.run_in_executor(
                    None, self._tv.get_hist, sym, exchange, interval, count
                )

            if df is None or df.empty:
                logger.debug(f"TradingView get_hist returned empty for {symbol} {timeframe}")
                self._record_failure()
                return []

            self._record_success()
            rates = []
            for index, row in df.iterrows():
                rates.append({
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": index.isoformat() if isinstance(index, pd.Timestamp) else str(index),
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "volume": float(row.get('volume', 0.0))
                })
            return rates
        except Exception as e:
            logger.debug(f"TradingView get_rates({symbol}, {timeframe}): {e}")
            self._record_failure()
            return []

    async def get_historical_klines(self, symbol: str, interval: str, limit: int = 100) -> list[Candle]:
        rates = await self.get_rates(symbol, interval, limit)
        candles = []
        for r in rates:
            candles.append(Candle(
                symbol=r["symbol"],
                timeframe=Timeframe(r["timeframe"]),
                timestamp=pd.to_datetime(r["timestamp"]),
                open=r["open"],
                high=r["high"],
                low=r["low"],
                close=r["close"],
                volume=r["volume"]
            ))
        return candles

    async def validate_secondary_parity(
        self, symbol: str, primary_price: float, tolerance_pct: float = 0.5
    ) -> dict[str, Any]:
        """
        Phase 4: Performs secondary validation against primary feed.
        Never replaces primary feed, records exact discrepancy and parity status.
        """
        sec_ticker = await self.get_ticker(symbol)
        if not sec_ticker or sec_ticker.get("price") is None:
            return {
                "symbol": symbol,
                "role": "SECONDARY_VALIDATION",
                "status": "SECONDARY_UNAVAILABLE",
                "primary_price": primary_price,
                "secondary_price": None,
                "discrepancy": None,
                "discrepancy_pct": None,
                "parity_passed": True,  # Non-blocking if secondary is down
            }

        sec_price = float(sec_ticker["price"])
        diff = abs(primary_price - sec_price)
        diff_pct = (diff / primary_price) * 100.0 if primary_price > 0 else 0.0
        passed = diff_pct <= tolerance_pct

        return {
            "symbol": symbol,
            "role": "SECONDARY_VALIDATION",
            "provider": "TRADINGVIEW",
            "status": "PARITY_CONFIRMED" if passed else "DISCREPANCY_DETECTED",
            "primary_price": primary_price,
            "secondary_price": sec_price,
            "discrepancy": round(diff, 5),
            "discrepancy_pct": round(diff_pct, 4),
            "parity_passed": passed,
            "timestamp": sec_ticker.get("timestamp"),
        }

    async def get_orderbook(self, symbol: str, depth: int = 10) -> OrderBook:
        return OrderBook(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            bids=[],
            asks=[]
        )
