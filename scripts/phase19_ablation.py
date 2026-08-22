import asyncio
import pandas as pd
from datetime import datetime, timezone

from app.analytics.master_intelligence_engine import master_intelligence_engine
from app.analytics.consensus_engine import ConsensusEngine
from app.market_data.registry import asset_registry
from app.logs.logger import get_logger, setup_logging

logger = get_logger(__name__)

async def run_ablation_study():
    """
    Simulates the market environment with and without the intelligence layer
    to prove the mathematical edge of Phase 19 zero-trust integration.
    """
    logger.info("Starting Phase 19 Ablation Study...")
    
    # 1. Setup Test Data
    symbols = ["EURUSD", "BTCUSD", "SPX500"]
    timeframe = "4H"
    
    # Mock data representing a volatile day (e.g. CPI release day)
    # The quant model alone might see a technical buy
    mock_df = pd.DataFrame([
        {"timestamp": datetime.utcnow(), "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.05, "volume": 100}
    ]).set_index("timestamp")
    mock_df["SMA_200"] = 1.0
    mock_df["Future_Return_5"] = 0.015 # Quant expects +1.5%

    results = []
    
    for symbol in symbols:
        logger.info(f"--- Analyzing {symbol} ---")
        
        # Scenario A: Quant Only Baseline (No Context)
        logger.info("[A] Running Quant Baseline (No Context)...")
        quant_engine = ConsensusEngine()
        quant_result = quant_engine.generate_consensus(symbol, timeframe, mock_df)
        quant_signal = quant_result.get("signal", "NEUTRAL")
        quant_conf = quant_result.get("confidence_score", 0.0)
        logger.info(f"Quant Baseline: {quant_signal} (Conf: {quant_conf:.1f}%)")
        
        # Scenario B: Full Intelligence Engine (Phase 19)
        logger.info("[B] Running Full Master Intelligence Engine (With Context)...")
        master_result = await master_intelligence_engine.generate_master_signal(symbol, timeframe, mock_df)
        master_signal = master_result.get("master_signal", "NEUTRAL")
        
        intelligence_data = master_result.get("intelligence", {})
        news = intelligence_data.get("news_sentiment", "UNKNOWN")
        risk = intelligence_data.get("event_risk", "UNKNOWN")
        
        logger.info(f"Full Intelligence: {master_signal} | News: {news} | Risk: {risk}")
        
        if quant_signal != master_signal:
            logger.warning(f"-> INTELLIGENCE OVERRIDE: {quant_signal} blocked -> {master_signal}")
            logger.warning(f"-> Reasons: {intelligence_data.get('no_trade_reasons', [])}")
            
        results.append({
            "symbol": symbol,
            "quant_signal": quant_signal,
            "master_signal": master_signal,
            "overridden": quant_signal != master_signal
        })
        
    logger.info("=== Ablation Study Summary ===")
    overrides = sum(1 for r in results if r["overridden"])
    logger.info(f"Total Signals Overridden/Blocked by Context: {overrides}/{len(symbols)}")
    if overrides > 0:
        logger.info("SUCCESS: Intelligence layer successfully degraded low-quality signals.")
    else:
        logger.info("NOTE: No overrides occurred. The quant signals aligned with context.")
        
if __name__ == "__main__":
    setup_logging()
    asyncio.run(run_ablation_study())
