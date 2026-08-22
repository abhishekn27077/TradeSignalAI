import asyncio
import logging
from datetime import datetime, timedelta
import pandas as pd

from app.database.manager import db_manager
from sqlalchemy import text
from app.market_data.providers.manager import market_provider_manager

logger = logging.getLogger(__name__)

class HistoricalDatabaseSync:
    """
    Downloads and synchronizes minimum 12 months of historical OHLCV data
    for all supported assets.
    """
    def __init__(self):
        self.symbols = ["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "NAS100", "SPX500"]
        self.timeframes = ["1h", "4h", "1d"]

    async def sync_all_assets(self):
        """
        Main entrypoint for historical sync.
        """
        logger.info("Starting historical database sync for 12 months...")
        
        # Ensure tables exist
        session_factory = db_manager.get_session()
        async with session_factory() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS historical_ohlcv (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    UNIQUE(symbol, timeframe, timestamp)
                )
            """))
            await session.commit()
            
            # Use index for efficient retrieval
            await session.execute(text("CREATE INDEX IF NOT EXISTS idx_hist_ohlcv ON historical_ohlcv(symbol, timeframe, timestamp)"))
            await session.commit()
            
        # Download data
        for symbol in self.symbols:
            for tf in self.timeframes:
                await self._download_and_store(symbol, tf)
                
        logger.info("Historical database sync complete.")

    async def _download_and_store(self, symbol: str, timeframe: str):
        logger.info(f"Syncing historical data for {symbol} ({timeframe})...")
        
        try:
            # yfinance mapping logic
            yf_symbol = symbol
            if symbol in ["BTCUSD", "ETHUSD"]:
                yf_symbol = f"{symbol[:3]}-{symbol[3:]}"
            elif symbol in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]:
                yf_symbol = f"{symbol}=X"
            elif symbol == "XAUUSD":
                yf_symbol = "GC=F"
            elif symbol == "NAS100":
                yf_symbol = "^NDX"
            elif symbol == "SPX500":
                yf_symbol = "^GSPC"
                
            # Run yfinance in executor to avoid blocking
            import yfinance as yf
            def fetch_yf():
                period = "1y" if timeframe in ["1d", "4h", "1h"] else "max" 
                interval = timeframe
                if interval == "4h":
                    interval = "1h" # yfinance 4h is sometimes flaky, fetch 1h and resample later if needed
                
                ticker = yf.Ticker(yf_symbol)
                # Ensure 12 months (approx 365 days)
                return ticker.history(period=period, interval=interval)
                
            df = await asyncio.to_thread(fetch_yf)
            
            if df.empty:
                logger.warning(f"No historical data returned for {symbol} ({yf_symbol}) via yfinance.")
                return
                
            # Store to DB
            session_factory = db_manager.get_session()
            async with session_factory() as session:
                for idx, row in df.iterrows():
                    # Handle tz-aware index
                    ts = idx.to_pydatetime()
                    if ts.tzinfo is not None:
                        ts = ts.replace(tzinfo=None)
                        
                    # Insert or ignore via raw SQL for speed
                    stmt = text("""
                        INSERT OR IGNORE INTO historical_ohlcv (symbol, timeframe, timestamp, open, high, low, close, volume)
                        VALUES (:sym, :tf, :ts, :o, :h, :l, :c, :v)
                    """)
                    await session.execute(stmt, {
                        "sym": symbol,
                        "tf": timeframe,
                        "ts": ts,
                        "o": float(row['Open']),
                        "h": float(row['High']),
                        "l": float(row['Low']),
                        "c": float(row['Close']),
                        "v": float(row.get('Volume', 0.0))
                    })
                await session.commit()
            logger.info(f"Successfully synced {len(df)} candles for {symbol} ({timeframe}).")
            
        except Exception as e:
            logger.error(f"Error syncing {symbol} ({timeframe}): {e}")

historical_sync = HistoricalDatabaseSync()
