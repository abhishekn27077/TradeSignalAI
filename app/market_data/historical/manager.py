import asyncio
import logging
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

from app.database.manager import db_manager
from app.database.models.market import CandleModel
from app.analytics.feature_engine import FeatureEngine

logger = logging.getLogger(__name__)

# Yahoo Finance mapping
YF_ASSETS = {
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "AUDUSD": "AUDUSD=X",
    "XAUUSD": "GC=F",
    "NAS100": "NQ=F",
    "SPX500": "^GSPC",
}

TIMEFRAME_MAP = {
    "15M": "15m",
    "1H": "1h",
    "4H": "1h",  # We will resample 1h to 4h because yfinance lacks 4h natively or it's buggy
    "1D": "1d",
    "1W": "1wk"
}

class HistoricalManager:
    """
    Institutional historical data downloader and storage engine.
    """
    
    @staticmethod
    def resample_4h(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        # Resample to 4H boundaries
        df_4h = df.resample('4h').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        return df_4h

    @classmethod
    async def download_and_store(cls, asset: str, tf: str):
        yf_ticker = YF_ASSETS.get(asset)
        yf_tf = TIMEFRAME_MAP.get(tf)
        
        logger.info(f"Downloading {asset} ({yf_ticker}) on {tf}...")
        
        # Max period allowed by yf per timeframe
        if tf == "15M":
            period = "60d"
        elif tf in ["1H", "4H"]:
            period = "730d"
        else:
            period = "5y"
            
        try:
            ticker = yf.Ticker(yf_ticker)
            # Use threads=False because we wrap in to_thread anyway
            df = await asyncio.to_thread(
                ticker.history, period=period, interval=yf_tf, auto_adjust=True
            )
            
            if df.empty:
                logger.warning(f"No data returned for {asset} on {tf}")
                return
                
            # Formatting
            df.index = df.index.tz_localize(None)
            df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
            
            # Resample if 4H
            if tf == "4H":
                df = cls.resample_4h(df)
                
            # Apply institutional features
            df = FeatureEngine.add_all_features(df)
            
            # Store in database
            await cls._store_to_db(asset, tf, df)
            
        except Exception as e:
            logger.error(f"Failed downloading {asset} {tf}: {e}")

    @classmethod
    async def _store_to_db(cls, asset: str, tf: str, df: pd.DataFrame):
        from sqlalchemy import select
        
        if db_manager._session_factory is None:
            logger.error("DB not initialized")
            return
            
        async with db_manager._session_factory() as session:
            # For speed, we will find the latest timestamp in DB and only insert new ones
            stmt = select(CandleModel).filter(
                CandleModel.symbol == asset,
                CandleModel.timeframe == tf
            ).order_by(CandleModel.timestamp.desc()).limit(1)
            
            result = await session.execute(stmt)
            latest_record = result.scalars().first()
            
            if latest_record:
                # Need to localize latest_record.timestamp to None if it's tz-aware to compare
                latest_ts = latest_record.timestamp.replace(tzinfo=None)
                df = df[df.index > latest_ts]
                
            if df.empty:
                logger.info(f"No new records to insert for {asset} {tf}.")
                return
                
            # Convert to dicts for fast insertion
            records = []
            for ts, row in df.iterrows():
                # Extract numerical features for JSON
                features_dict = row.drop(['open', 'high', 'low', 'close', 'volume'], errors='ignore').to_dict()
                # Clean nan for json
                features_dict = {k: v for k, v in features_dict.items() if pd.notnull(v)}
                
                records.append(
                    CandleModel(
                        symbol=asset,
                        timeframe=tf,
                        timestamp=ts,
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        volume=float(row['volume']),
                        features_json=features_dict,
                        provider="yfinance"
                    )
                )
            
            session.add_all(records)
            await session.commit()
            logger.info(f"Stored {len(records)} new candles for {asset} {tf}.")

    @classmethod
    async def update_all_historical(cls):
        """
        Runs the daily background sync for all assets and timeframes.
        """
        assets = list(YF_ASSETS.keys())
        timeframes = ["15M", "1H", "4H", "1D", "1W"]
        
        for asset in assets:
            for tf in timeframes:
                await cls.download_and_store(asset, tf)
                # Rate limit protection
                await asyncio.sleep(2)
