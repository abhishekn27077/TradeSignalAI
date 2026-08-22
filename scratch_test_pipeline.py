import asyncio
import logging
from app.analytics.forecast_manager import ForecastManager
from app.database.manager import db_manager
from app.market_data.historical.manager import HistoricalManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_pipeline():
    logger.info("Connecting to DB...")
    db_manager.connect()
    await db_manager.init_db()

    logger.info("Running H4 Pipeline Test on BTCUSD...")
    
    # 1. Ensure history
    logger.info("Ingesting historical data...")
    await HistoricalManager.download_and_store("BTCUSD", "4H")
    logger.info("Historical data downloaded and stored.")
    
    # 2. Run forecast manager
    logger.info("Running forecast scan...")
    fm = ForecastManager()
    results = await fm.scan_market(["BTCUSD"])
    
    for r in results:
        logger.info(f"Result: {r}")
        
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(run_pipeline())
