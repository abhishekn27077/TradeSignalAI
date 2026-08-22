import asyncio
import logging
from datetime import datetime, timezone
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.pipeline.orchestrator import pipeline_orchestrator
from app.market_data.registry import AssetConfig, AssetClass, MarketSession

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Phase31_Validation")

async def test_pipeline_end_to_end():
    logger.info("Starting Phase 31 Pipeline Orchestrator Test...")
    
    # 1. Trigger the pipeline manually for a single test symbol
    # We use BTCUSD as it always has a valid crypto session
    logger.info("Triggering pipeline orchestrator for BTCUSD...")
    
    # Mock the DB fetch so we guarantee data
    from app.pipeline.orchestrator import pipeline_orchestrator
    import pandas as pd
    import numpy as np
    
    async def mock_fetch(*args, **kwargs):
        # Create a mock dataframe of 50 candles trending strongly upwards
        dates = pd.date_range(end=datetime.now(timezone.utc), periods=50, freq='4h')
        df = pd.DataFrame({
            "close": np.linspace(50000, 60000, 50),
            "high": np.linspace(50500, 60500, 50),
            "low": np.linspace(49500, 59500, 50),
            "open": np.linspace(49800, 59800, 50),
            "volume": np.random.randint(100, 1000, 50),
            "ATR_14": np.linspace(500, 600, 50)
        }, index=dates)
        return df

    pipeline_orchestrator.forecast_manager._fetch_recent_data = mock_fetch

    # Run the pipeline
    await pipeline_orchestrator._trigger_pipeline(["BTCUSD"])
    
    logger.info("Pipeline execution completed.")
    
    # 2. Check the recent_signals queue to see what was published
    from app.strategies.manager import strategy_manager
    signals = strategy_manager.recent_signals
    
    if signals:
        latest = signals[0]
        logger.info("="*50)
        logger.info("SUCCESS: Signal published to Signal Lifecycle!")
        logger.info(f"Asset: {latest['asset']}")
        logger.info(f"Direction: {latest['direction']}")
        logger.info(f"Entry: {latest['entry_price']}")
        logger.info(f"Stop Loss: {latest['stop_loss']}")
        logger.info(f"Take Profit: {latest['take_profit']}")
        logger.info(f"R:R: {latest['risk_reward']}")
        
        intel = latest.get("intelligence", {})
        logger.info(f"Historical Analog: {intel.get('historical_analog')}")
        logger.info(f"Market Regime: {latest.get('market_regime')}")
        logger.info("="*50)
    else:
        logger.warning("No signal was published. This is expected if the Consensus Engine returns NEUTRAL, NO_TRADE, or there was insufficient data.")

if __name__ == "__main__":
    asyncio.run(test_pipeline_end_to_end())
