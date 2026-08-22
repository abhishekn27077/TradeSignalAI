import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.market_intelligence.h4_engine import h4_forecast_engine
from app.market_intelligence.swing_scanner import swing_scanner
from app.execution.coordinator import coordinator
from app.execution.router import smart_router
from app.utils.event_bus import event_bus
from app.database.manager import db_manager
from app.logs.logger import get_logger

logger = get_logger("Phase20Test")

async def test_execution_flow():
    db_manager.connect()
    await db_manager.init_db()
    
    # Start coordinator to listen for ConsensusCompleted
    coordinator.start()
    
    # Force initialize the dummy broker by requesting an asset
    broker = smart_router.get_broker_for_asset("EURUSD")
    logger.info(f"Broker acquired: {type(broker)}")
    
    logger.info("Triggering H4 Engine Forecasts...")
    await h4_forecast_engine.generate_forecasts()
    
    # Wait a bit for events to propagate
    await asyncio.sleep(3)
    
    logger.info("Checking open positions and balance...")
    bal = await smart_router.get_balance()
    pos = await smart_router.get_positions()
    orders = await smart_router.get_orders()
    
    logger.info(f"Balance: {bal}")
    logger.info(f"Positions: {pos}")
    logger.info(f"Orders: {orders}")
    
    # Also check DB for SignalLifecycleModel
    async with db_manager.get_session()() as session:
        from app.database.models.signal import SignalLifecycleModel
        from sqlalchemy import select
        res = await session.execute(select(SignalLifecycleModel).order_by(SignalLifecycleModel.created_at.desc()).limit(5))
        signals = res.scalars().all()
        for s in signals:
            logger.info(f"DB Signal: {s.signal_id} | {s.asset} | {s.direction} | Exec: {s.execution_status} | Status: {s.status}")

if __name__ == "__main__":
    asyncio.run(test_execution_flow())
