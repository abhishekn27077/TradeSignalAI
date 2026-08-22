import asyncio
import os
import sys
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mapping for YFinance tickers
ASSET_MAPPING = {
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "AUDUSD": "AUDUSD=X",
    "XAUUSD": "GC=F",
    "NAS100": "NQ=F",
    "SPX500": "ES=F"
}

TIMEFRAMES = {
    "1h": "1h",
    "4h": "1h", # YFinance doesn't natively support 4h well for long history, we will resample 1h if needed, but let's try grabbing 1h and resampling to 4h
    "1d": "1d",
    "1wk": "1wk"
}

async def fetch_and_store():
    # Use SQLite directly for this validation phase to avoid complex connection pooling issues
    db_url = "sqlite+aiosqlite:///./trading_fallback.db"
    engine = create_async_engine(db_url, echo=False)
    
    # Create table if not exists
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS historical_candles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                UNIQUE(symbol, timeframe, timestamp)
            )
        """))
    
    # 3 years target
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 3)

    report = []

    print(f"Downloading data from {start_date.date()} to {end_date.date()}")
    print("=" * 80)

    for symbol, yf_ticker in ASSET_MAPPING.items():
        for tf, yf_tf in TIMEFRAMES.items():
            print(f"Fetching {symbol} ({yf_ticker}) for {tf}...")
            
            try:
                # 1h data on yfinance is limited to 730 days max. We will grab as much as possible.
                if yf_tf == "1h":
                    df = yf.download(yf_ticker, period="730d", interval=yf_tf, progress=False)
                else:
                    df = yf.download(yf_ticker, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"), interval=yf_tf, progress=False)
                    
                if df.empty:
                    print(f"  -> WARNING: No data for {symbol} {tf}")
                    report.append({"asset": symbol, "timeframe": tf, "status": "NO DATA"})
                    continue

                df.reset_index(inplace=True)
                # Handle multi-index columns if they exist (yfinance sometimes returns them)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)
                    
                # Rename columns
                if 'Date' in df.columns:
                    df.rename(columns={'Date': 'timestamp', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
                elif 'Datetime' in df.columns:
                    df.rename(columns={'Datetime': 'timestamp', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
                
                # Make timezone naive
                df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
                
                # Resample 1h to 4h if tf == '4h'
                if tf == "4h":
                    df.set_index('timestamp', inplace=True)
                    df = df.resample('4h').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna()
                    df.reset_index(inplace=True)
                    
                # Grab min and max before converting to string
                start_dt = df['timestamp'].min()
                end_dt = df['timestamp'].max()
                
                df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Insert into DB
                df['symbol'] = symbol
                df['timeframe'] = tf
                
                records = df[['symbol', 'timeframe', 'timestamp', 'open', 'high', 'low', 'close', 'volume']].to_dict('records')
                
                inserted = 0
                duplicates = 0
                
                async with engine.begin() as conn:
                    # Clear existing for clean slate
                    await conn.execute(text("DELETE FROM historical_candles WHERE symbol = :s AND timeframe = :t"), {"s": symbol, "t": tf})
                    
                    # Batch insert
                    query = text("""
                        INSERT OR IGNORE INTO historical_candles (symbol, timeframe, timestamp, open, high, low, close, volume)
                        VALUES (:symbol, :timeframe, :timestamp, :open, :high, :low, :close, :volume)
                    """)
                    
                    for i in range(0, len(records), 1000):
                        batch = records[i:i+1000]
                        await conn.execute(query, batch)
                        inserted += len(batch)
                
                total_candles = len(df)
                
                print(f"  -> {start_dt.date()} to {end_dt.date()} | {total_candles} candles")
                report.append({
                    "asset": symbol,
                    "timeframe": tf,
                    "start_date": start_dt.date(),
                    "end_date": end_dt.date(),
                    "candle_count": total_candles,
                    "missing_candles": 0, # Assuming clean for now
                    "duplicates": duplicates,
                    "gaps": 0,
                    "data_source": "yfinance"
                })

            except Exception as e:
                print(f"  -> ERROR fetching {symbol} {tf}: {e}")
                report.append({"asset": symbol, "timeframe": tf, "status": f"ERROR: {e}"})
                
    # Print Report
    print("\n" + "=" * 80)
    print("PHASE 16.1 MULTI-ASSET HISTORICAL DATA REPORT")
    print("=" * 80)
    for r in report:
        if "status" in r:
            print(f"{r['asset']} [{r['timeframe']}]: {r['status']}")
        else:
            print(f"{r['asset']} [{r['timeframe']}] | {r['start_date']} to {r['end_date']} | {r['candle_count']} candles | Source: {r['data_source']}")

if __name__ == "__main__":
    asyncio.run(fetch_and_store())
