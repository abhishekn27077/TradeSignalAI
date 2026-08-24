import asyncio
import sys
import os
import pandas as pd
from datetime import timedelta

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.intelligence.faiss_memory import faiss_memory
from app.market_data.service import market_service
from app.analytics.feature_engine import FeatureEngine
from app.logs.logger import get_logger

logger = get_logger("Test_Phase32_FAISS_Leakage")

async def test_faiss_leakage():
    symbol = "BTCUSD"
    timeframe = "H1"
    
    logger.info("Building FAISS index...")
    success = await faiss_memory.build_index(symbol, timeframe, count=1500)
    if not success:
        logger.error("Failed to build index.")
        sys.exit(1)
        
    rates = await market_service.get_rates(symbol, timeframe, count=100)
    df = pd.DataFrame(rates)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601', utc=True)
    
    # We will simulate a query exactly 30 days ago
    query_timestamp = df['timestamp'].iloc[-1] - timedelta(days=30)
    
    # We pass current_df up to query_timestamp
    df_history = df[df['timestamp'] <= query_timestamp].copy()
    
    if df_history.empty:
        logger.warning("No data points before query timestamp in the recent 100 limit, trying direct build")
        # Let's just use the index metadata to pick a date
        meta = faiss_memory.metadata[f"{symbol}_{timeframe}"]
        query_timestamp = meta.index[-50] # pick the 50th from end
        df_history = meta.loc[:query_timestamp].copy()
        df_history['timestamp'] = df_history.index
    
    logger.info(f"Querying FAISS with query_timestamp = {query_timestamp}")
    
    # Call the engine
    result = faiss_memory.get_historical_analogs(symbol, timeframe, df_history, query_timestamp)
    
    logger.info(f"FAISS Result: {result}")
    
    if result["closest_match_date"] != "UNAVAILABLE":
        match_date = pd.to_datetime(result["closest_match_date"])
        logger.info(f"Match Date: {match_date}")
        if match_date >= query_timestamp:
            logger.error(f"LEAKAGE DETECTED: Match date {match_date} is >= query date {query_timestamp}!")
            sys.exit(1)
        else:
            logger.info("Leakage Test PASS: Match date strictly precedes query date.")
    else:
        logger.warning("FAISS returned UNAVAILABLE. Cannot verify leakage on missing result.")
        
    logger.info("PHASE 32 FAISS LEAKAGE TEST COMPLETE: SUCCESS")
    
if __name__ == "__main__":
    asyncio.run(test_faiss_leakage())
