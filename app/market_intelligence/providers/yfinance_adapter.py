"""
YFinance Data Provider Adapter
================================
Maps internal symbols/timeframes to yfinance format and fetches OHLCV data.
Free provider, no API key required.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)

# ── Symbol mapping: internal → yfinance ticker ───────────────────────────────

SYMBOL_MAP = {
    # Forex
    "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X", "USDCHF": "USDCHF=X", "USDCAD": "USDCAD=X",
    "NZDUSD": "NZDUSD=X", "EURGBP": "EURGBP=X", "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X",
    # Crypto
    "BTCUSDT": "BTC-USD", "ETHUSDT": "ETH-USD", "BNBUSDT": "BNB-USD",
    "SOLUSDT": "SOL-USD", "XRPUSDT": "XRP-USD",
    # Indices
    "SPX500": "^GSPC", "NAS100": "^IXIC", "US30": "^DJI",
    # Commodities
    "XAUUSD": "GC=F", "XAGUSD": "SI=F", "USOIL": "CL=F",
}

# ── Timeframe mapping: internal → yfinance interval ─────────────────────────

TIMEFRAME_MAP = {
    "M1": "1m", "M5": "5m", "M15": "15m", "M30": "30m",
    "H1": "1h", "H4": "4h", "D1": "1d", "W1": "1wk",
}

# yfinance limits max period for intraday data
TIMEFRAME_MAX_DAYS = {
    "M1": 7, "M5": 60, "M15": 60, "M30": 60,
    "H1": 730, "H4": 730, "D1": 36500, "W1": 36500,
}


class YFinanceAdapter:
    """
    Adapter for fetching OHLCV data from Yahoo Finance via yfinance.
    Handles symbol/timeframe mapping and returns normalized candle dicts.
    """

    def __init__(self):
        self.name = "yfinance"
        self._yf = None

    def _ensure_yfinance(self):
        """Lazy-load yfinance to avoid import errors if not installed."""
        if self._yf is None:
            try:
                import yfinance as yf
                self._yf = yf
            except ImportError:
                raise ImportError(
                    "yfinance is required for market data downloads. "
                    "Install with: pip install yfinance"
                )

    def map_symbol(self, symbol: str) -> str:
        """Map internal symbol to yfinance ticker."""
        return SYMBOL_MAP.get(symbol, symbol)

    def map_timeframe(self, timeframe: str) -> str:
        """Map internal timeframe to yfinance interval."""
        return TIMEFRAME_MAP.get(timeframe, "1d")

    def get_max_days(self, timeframe: str) -> int:
        """Get maximum history depth yfinance supports for a timeframe."""
        return TIMEFRAME_MAX_DAYS.get(timeframe, 365)

    async def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch OHLCV candles from yfinance.

        Args:
            symbol: Internal symbol (e.g. 'EURUSD')
            timeframe: Internal timeframe (e.g. 'H1')
            start_date: Start of range (UTC)
            end_date: End of range (UTC), defaults to now

        Returns:
            List of candle dicts with keys:
            timestamp, open, high, low, close, volume
        """
        self._ensure_yfinance()

        yf_symbol = self.map_symbol(symbol)
        yf_interval = self.map_timeframe(timeframe)
        max_days = self.get_max_days(timeframe)

        if end_date is None:
            end_date = datetime.now(timezone.utc)

        # Clamp start_date to yfinance limits
        earliest_allowed = end_date - timedelta(days=max_days)
        if start_date < earliest_allowed:
            start_date = earliest_allowed
            logger.info(
                f"Clamped start_date to {start_date.date()} for {symbol} {timeframe} "
                f"(yfinance max {max_days} days)"
            )

        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        logger.info(f"Fetching {symbol} ({yf_symbol}) {timeframe} from {start_str} to {end_str}")

        try:
            # Run yfinance in executor to not block async loop
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: self._yf.download(
                    yf_symbol,
                    start=start_str,
                    end=end_str,
                    interval=yf_interval,
                    progress=False,
                    auto_adjust=True,
                ),
            )

            if df is None or df.empty:
                logger.warning(f"No data returned for {symbol} {timeframe}")
                return []

            # Handle multi-level columns from yfinance
            if isinstance(df.columns, type(df.columns)) and df.columns.nlevels > 1:
                df.columns = df.columns.droplevel(1)

            candles = []
            for idx, row in df.iterrows():
                ts = idx
                if hasattr(ts, 'to_pydatetime'):
                    ts = ts.to_pydatetime()
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)

                candle = {
                    "timestamp": ts,
                    "open": float(row.get("Open", row.get("open", 0))),
                    "high": float(row.get("High", row.get("high", 0))),
                    "low": float(row.get("Low", row.get("low", 0))),
                    "close": float(row.get("Close", row.get("close", 0))),
                    "volume": float(row.get("Volume", row.get("volume", 0))),
                }

                # Skip invalid candles
                if candle["open"] <= 0 or candle["high"] <= 0 or candle["close"] <= 0:
                    continue

                candles.append(candle)

            logger.info(f"Fetched {len(candles)} candles for {symbol} {timeframe}")
            return candles

        except Exception as e:
            logger.error(f"YFinance fetch error for {symbol} {timeframe}: {e}")
            return []

    def is_available(self) -> bool:
        """Check if yfinance is installed and importable."""
        try:
            self._ensure_yfinance()
            return True
        except ImportError:
            return False


# Singleton
yfinance_adapter = YFinanceAdapter()
