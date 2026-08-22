import asyncio
import sys
import os

# Add root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.market_data.registry import asset_registry
from app.market_data.service import market_service
from app.logs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger("Phase32_RealDataValidation")

async def main():
    universe = asset_registry.get_validation_universe()
    logger.info(f"Validating real market data for universe: {universe}")
    
    all_passed = True
    
    for symbol in universe:
        logger.info(f"--- Validating {symbol} ---")
        
        # 1. Test Latest Price
        latest_price = await market_service.get_latest_price(symbol)
        if latest_price is None or latest_price <= 0:
            logger.error(f"{symbol} failed latest price check: {latest_price}")
            all_passed = False
        else:
            logger.info(f"{symbol} latest price: {latest_price} (PASS)")
            
        # 2. Test Historical OHLCV (H1)
        rates = await market_service.get_rates(symbol, "H1", count=500)
        
        if not rates or len(rates) < 100:
            logger.error(f"{symbol} failed historical data length check: found {len(rates)} rates")
            all_passed = False
            continue
            
        # OHLCV validation
        timestamps = set()
        duplicates = 0
        invalid_prices = 0
        invalid_high_low = 0
        
        for r in rates:
            ts = r['timestamp']
            if ts in timestamps:
                duplicates += 1
            timestamps.add(ts)
            
            o, h, l, c = r['open'], r['high'], r['low'], r['close']
            
            if any(p <= 0 for p in [o, h, l, c]):
                invalid_prices += 1
                
            if h < l:
                invalid_high_low += 1
                
        logger.info(f"{symbol} Data Audit (Count: {len(rates)}):")
        logger.info(f"  Duplicates: {duplicates}")
        logger.info(f"  Invalid Prices (<=0): {invalid_prices}")
        logger.info(f"  Invalid High/Low (High < Low): {invalid_high_low}")
        
        if duplicates > 0 or invalid_prices > 0 or invalid_high_low > 0:
            logger.error(f"{symbol} FAILED data structural validation.")
            all_passed = False
        else:
            logger.info(f"{symbol} structural validation (PASS)")

    if all_passed:
        logger.info("PHASE 32 REAL DATA VALIDATION COMPLETE: SUCCESS")
    else:
        logger.error("PHASE 32 REAL DATA VALIDATION COMPLETE: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
