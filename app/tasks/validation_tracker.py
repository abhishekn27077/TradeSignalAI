import asyncio
from datetime import datetime

from sqlalchemy.future import select

from app.database.manager import db_manager
from app.database.models.validation import ResearchValidationRecord
from app.logs.logger import get_logger
from app.market_data.service import market_service
from app.utils.event_bus import event_bus

logger = get_logger(__name__)

class ValidationTracker:
    def __init__(self):
        self._running = False
        self._task = None
        
    async def _on_signal_generated(self, payload: dict, **kwargs):
        """
        Listens to new signals and creates a ResearchValidationRecord.
        payload should contain signal details.
        """
        try:
            session_maker = db_manager.get_session()
            async with session_maker() as session:
                record = ResearchValidationRecord(
                    prediction_timestamp=datetime.utcnow(),
                    asset=payload.get("symbol"),
                    timeframe=payload.get("timeframe", "1h"),
                    entry_price=payload.get("entry"),
                    stop_price=payload.get("stop"),
                    target_price=payload.get("target"),
                    confidence=payload.get("confidence", 0.0),
                    consensus_score=payload.get("consensus", 0.0),
                    grade=payload.get("grade", "C"),
                    expected_hold_time_minutes=payload.get("expected_hold_minutes", 120),
                    status="PENDING",
                    strategy_name="Consensus Engine",
                    model_name="Ensemble",
                    session="NY"
                )
                session.add(record)
                await session.commit()
                logger.info(f"Created validation record for new signal on {record.asset}")
        except Exception as e:
            logger.error(f"Error creating validation record: {e}")

    async def _tracker_loop(self):
        # Register to signal events
        event_bus.subscribe("SignalGenerated", self._on_signal_generated)
        
        while self._running:
            try:
                session_maker = db_manager.get_session()
                async with session_maker() as session:
                    stmt = select(ResearchValidationRecord).where(ResearchValidationRecord.status == "PENDING")
                    result = await session.execute(stmt)
                    pending_records = result.scalars().all()
                    
                    for record in pending_records:
                        if not record.asset:
                            continue
                            
                        # Fetch latest rates for the asset to check against targets/stops
                        # For a true backtest tracker, we should fetch since the prediction_timestamp.
                        # For live, getting current ticker might suffice if we check frequently, but OHLC is safer.
                        try:
                            rates = await market_service.get_rates(record.asset, record.timeframe, count=10)
                        except Exception as e:
                            logger.warning(f"Could not fetch rates for validation of {record.asset}: {e}")
                            continue
                            
                        if not rates:
                            continue
                            
                        # Filter rates after prediction timestamp
                        # Assuming rates have 'time' in seconds or milliseconds, or ISO string.
                        # If the structure of rates isn't exact, we can at least check the latest price.
                        ticker = await market_service.get_ticker(record.asset)
                        if not ticker or "price" not in ticker:
                            continue
                            
                        current_price = ticker["price"]
                        is_buy = record.target_price and record.entry_price and record.target_price > record.entry_price
                        
                        resolved = False
                        target_hit = False
                        stop_hit = False
                        
                        # Simplified resolution logic
                        if is_buy:
                            if record.target_price is not None and current_price >= record.target_price:
                                target_hit = True
                                resolved = True
                            elif record.stop_price is not None and current_price <= record.stop_price:
                                stop_hit = True
                                resolved = True
                        else:
                            if record.target_price is not None and current_price <= record.target_price:
                                target_hit = True
                                resolved = True
                            elif record.stop_price is not None and current_price >= record.stop_price:
                                stop_hit = True
                                resolved = True
                                
                        elapsed = (datetime.utcnow() - record.prediction_timestamp).total_seconds() / 60
                        expired = False
                        
                        if not resolved and elapsed > (record.expected_hold_time_minutes or 120):
                            expired = True
                            resolved = True
                            
                        if resolved:
                            record.actual_exit_price = current_price
                            record.actual_hold_time_minutes = elapsed
                            
                            if record.entry_price is not None and record.entry_price > 0:
                                if is_buy:
                                    record.pnl_pct = (current_price - record.entry_price) / record.entry_price
                                else:
                                    record.pnl_pct = (record.entry_price - current_price) / record.entry_price
                            else:
                                record.pnl_pct = 0.0
                                
                            record.target_hit = target_hit
                            record.stop_hit = stop_hit
                            record.expired = expired
                            record.direction_correct = (record.pnl_pct > 0)
                            record.status = "RESOLVED"
                            
                            logger.info(f"Resolved validation record for {record.asset} (Target Hit: {target_hit}, Stop Hit: {stop_hit}, Expired: {expired})")
                            
                            # Fire event for SelfLearningEngine
                            await event_bus.publish("ForecastEvaluated", {
                                "validation_id": record.id,
                                "asset": record.asset,
                                "direction_correct": record.direction_correct,
                                "target_hit": target_hit,
                                "stop_hit": stop_hit,
                                "pnl_pct": record.pnl_pct
                            })
                            
                    await session.commit()
            except Exception as e:
                logger.error(f"Error in validation tracker loop: {e}")
                
            await asyncio.sleep(60) # Check every 60 seconds

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._tracker_loop())
            logger.info("Validation Tracker started")

    async def stop(self):
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            logger.info("Validation Tracker stopped")

validation_tracker = ValidationTracker()
