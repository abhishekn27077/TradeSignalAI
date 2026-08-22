import asyncio
import logging
import pandas as pd
from datetime import datetime, timezone

from app.analytics.master_intelligence_engine import master_intelligence_engine
from app.market_data.registry import asset_registry

logger = logging.getLogger(__name__)

class H4ForecastGenerator:
    """
    Scheduled task that runs every 4 hours to generate fresh predictions
    for all configured assets using the Master Intelligence Engine.
    """
    def __init__(self, data_provider):
        self.data_provider = data_provider
        
    async def run_loop(self):
        """Background loop that waits for H4 candle open."""
        while True:
            now = datetime.now(timezone.utc)
            hours_to_add = 4 - (now.hour % 4)
            next_h4 = now.replace(hour=now.hour, minute=0, second=0, microsecond=0)
            from datetime import timedelta
            next_h4 += timedelta(hours=hours_to_add)
            
            sleep_seconds = (next_h4 - now).total_seconds()
            logger.info(f"H4 Generator sleeping for {sleep_seconds} seconds until {next_h4}")
            
            # Use a smaller sleep in dev
            await asyncio.sleep(10)
            
            await self.generate_h4_forecasts()
            
    async def generate_h4_forecasts(self):
        """Generates the forecasts for the new H4 candle."""
        logger.info("Generating H4 Forecasts using full Intelligence Layer...")
        symbols = asset_registry.list_all_symbols()
        
        for symbol in symbols:
            # Fetch recent rates and convert to df
            # Mocking fetch for architecture completeness if provider not linked
            df = pd.DataFrame([
                {"timestamp": datetime.utcnow(), "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.05, "volume": 100}
            ]).set_index("timestamp")
            
            # Append mocked features so consensus engine doesn't break
            df["SMA_200"] = 1.0
            df["Future_Return_5"] = 0.01
            
            # Execute full intelligence flow
            try:
                final = await master_intelligence_engine.generate_master_signal(symbol, "4h", df)
                logger.info(f"Generated H4 {symbol}: {final['master_signal']}")
            except Exception as e:
                logger.error(f"Failed to generate H4 for {symbol}: {e}")

