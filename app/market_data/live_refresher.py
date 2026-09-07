"""
Live Market Data Refresher
==========================
Fetches fresh candles from yfinance and upserts them into the historical_candles table.
Run this every 5 minutes via scheduler, or call refresh_all() at startup.

Usage:
    python -m app.market_data.live_refresher
    or: from app.market_data.live_refresher import refresh_all; await refresh_all()
"""
import asyncio
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from app.logs.logger import get_logger

logger = get_logger(__name__)

# Symbol mapping: internal name -> yfinance ticker
YFINANCE_SYMBOL_MAP = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "AUDUSD": "AUDUSD=X",
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
    "XAUUSD": "GC=F",      # Gold futures
    "NAS100": "^IXIC",     # NASDAQ Composite
    "SPX500": "^GSPC",     # S&P 500
}

# Timeframe mapping: internal -> yfinance interval
TIMEFRAME_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
    "1H": "1h",
    "4h": "1h",   # yfinance doesn't have 4h; fetch 1h and aggregate
    "4H": "1h",
    "1d": "1d",
    "D1": "1d",
    "1wk": "1wk",
}

DB_PATH = "tradesignal.db"


def _upsert_candles(symbol: str, timeframe: str, candles: list[dict], provider: str = "yfinance") -> int:
    """Upsert candles into historical_candles. Returns count of new/updated rows."""
    if not candles:
        return 0
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    cur = conn.cursor()
    inserted = 0
    for c in candles:
        try:
            cur.execute(
                """
                INSERT INTO historical_candles (symbol, timeframe, timestamp, open, high, low, close, volume, provider)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, timeframe, timestamp, provider) DO UPDATE SET
                    open=excluded.open, high=excluded.high, low=excluded.low,
                    close=excluded.close, volume=excluded.volume
                """,
                (symbol, timeframe, c["timestamp"], c["open"], c["high"], c["low"], c["close"], c["volume"], provider),
            )
            if cur.rowcount > 0:
                inserted += 1
        except sqlite3.Error as e:
            logger.debug(f"Upsert error for {symbol}/{timeframe}: {e}")
    conn.commit()
    conn.close()
    return inserted


def fetch_candles_yfinance(symbol: str, timeframe: str, limit: int = 100) -> list[dict]:
    """Fetch candles from yfinance for a given symbol and timeframe."""
    import yfinance as yf

    yf_ticker = YFINANCE_SYMBOL_MAP.get(symbol)
    if not yf_ticker:
        logger.warning(f"No yfinance mapping for {symbol}")
        return []

    interval = TIMEFRAME_MAP.get(timeframe, "1h")

    # Determine period based on timeframe
    if timeframe in ("1m", "5m", "15m"):
        period = "1d"
    elif timeframe in ("1h", "1H"):
        period = "5d"
    elif timeframe in ("4h", "4H"):
        period = "30d"
    elif timeframe in ("1d", "D1"):
        period = "3mo"
    elif timeframe == "1wk":
        period = "1y"
    else:
        period = "5d"

    try:
        ticker = yf.Ticker(yf_ticker)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            return []

        candles = []
        for idx, row in hist.iterrows():
            ts = idx.to_pydatetime()
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            ts_str = ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            candles.append({
                "timestamp": ts_str,
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row.get("Volume", 0) or 0),
            })

        # For 4h timeframe, aggregate 1h candles into 4h
        if timeframe in ("4h", "4H") and interval == "1h":
            candles = _aggregate_to_4h(candles)

        return candles[-limit:]
    except Exception as e:
        logger.warning(f"yfinance fetch failed for {symbol}/{timeframe}: {e}")
        return []


def _aggregate_to_4h(candles_1h: list[dict]) -> list[dict]:
    """Aggregate 1h candles into 4h candles."""
    if len(candles_1h) < 4:
        return candles_1h
    result = []
    for i in range(0, len(candles_1h) - 3, 4):
        chunk = candles_1h[i:i+4]
        result.append({
            "timestamp": chunk[0]["timestamp"],
            "open": chunk[0]["open"],
            "high": max(c["high"] for c in chunk),
            "low": min(c["low"] for c in chunk),
            "close": chunk[-1]["close"],
            "volume": sum(c["volume"] for c in chunk),
        })
    return result


def refresh_symbol(symbol: str, timeframes: Optional[list[str]] = None) -> dict:
    """Refresh all timeframes for a single symbol. Returns stats."""
    if timeframes is None:
        timeframes = ["1h", "4h", "1d"]
    stats = {"symbol": symbol, "updated": 0, "errors": []}
    for tf in timeframes:
        try:
            candles = fetch_candles_yfinance(symbol, tf, limit=200)
            if candles:
                n = _upsert_candles(symbol, tf, candles)
                stats["updated"] += n
                logger.info(f"Refreshed {symbol}/{tf}: {n} candles upserted")
            else:
                stats["errors"].append(f"{tf}: no data")
        except Exception as e:
            stats["errors"].append(f"{tf}: {e}")
    return stats


def refresh_all(symbols: Optional[list[str]] = None) -> dict:
    """Refresh all symbols and timeframes. Returns summary stats."""
    if symbols is None:
        symbols = list(YFINANCE_SYMBOL_MAP.keys())
    summary = {"total_updated": 0, "symbols": {}, "errors": []}
    for sym in symbols:
        try:
            stats = refresh_symbol(sym)
            summary["symbols"][sym] = stats
            summary["total_updated"] += stats["updated"]
        except Exception as e:
            summary["errors"].append(f"{sym}: {e}")
    logger.info(f"Live refresh complete: {summary['total_updated']} candles updated across {len(symbols)} symbols")
    return summary


async def refresh_all_async(symbols: Optional[list[str]] = None) -> dict:
    """Async wrapper — runs refresh in thread pool to avoid blocking event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, refresh_all, symbols)


if __name__ == "__main__":
    print("Starting live market data refresh...")
    result = refresh_all()
    print(f"Done. Total candles updated: {result['total_updated']}")
    for sym, stats in result["symbols"].items():
        print(f"  {sym}: {stats['updated']} updated, errors: {stats['errors'] or 'none'}")
