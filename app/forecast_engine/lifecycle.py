import asyncio
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, update

from app.database.manager import db_manager
from app.database.models.forecast import ForecastConsensusModel, ForecastResultModel
from app.database.models.signal import SignalLifecycleModel
from app.execution.outcome_engine import outcome_engine, OUTCOME_UNRESOLVED
from app.logs.logger import get_logger

logger = get_logger(__name__)

class PredictionLifecycleManager:
    """
    Manages the lifecycle of predictions and signals:
    Created -> Validated -> Published -> Active -> Outcome Resolution (TP/SL/Time/Ambiguous) -> Completed
    """
    
    def __init__(self):
        self._task = None
        self._running = False
        self._poll_interval = 30 # Check every 30 seconds

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Prediction Lifecycle Manager started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Prediction Lifecycle Manager stopped")

    async def _run_loop(self):
        while self._running:
            try:
                await self.resolve_active_signals()
                await self.expire_old_predictions()
            except Exception as e:
                logger.error(f"Error in Prediction Lifecycle loop: {e}")
            
            await asyncio.sleep(self._poll_interval)

    async def resolve_active_signals(self):
        session_factory = db_manager.get_session()
        if not session_factory:
            return

        async with session_factory() as session:
            try:
                stmt = select(SignalLifecycleModel).where(
                    SignalLifecycleModel.status == "ACTIVE"
                )
                res = await session.execute(stmt)
                active_signals = res.scalars().all()

                for sig in active_signals:
                    if not sig.entry_price or not sig.stop_loss or not sig.take_profit_1:
                        continue

                    expiry = sig.expiry_time
                    if not expiry and sig.created_at:
                        holding_hours = sig.expected_holding_time or 4.0
                        expiry = sig.created_at + timedelta(hours=holding_hours)

                    if not expiry:
                        continue

                    outcome = await outcome_engine.resolve(
                        symbol=sig.asset,
                        timeframe=sig.timeframe or "H4",
                        direction=sig.direction,
                        entry_price=sig.entry_price,
                        stop_loss=sig.stop_loss,
                        take_profit=sig.take_profit_1,
                        signal_time=sig.created_at,
                        expiry_time=expiry,
                    )

                    if outcome.outcome != OUTCOME_UNRESOLVED:
                        sig.signal_state = outcome.outcome
                        sig.outcome = outcome.outcome
                        sig.status = "COMPLETED"
                        sig.exit_price = outcome.exit_price
                        sig.exit_time = outcome.exit_time
                        sig.gross_pnl = outcome.gross_pnl
                        sig.spread_cost = outcome.spread_cost
                        sig.slippage_cost = outcome.slippage_cost
                        sig.fees_cost = outcome.fees_cost
                        sig.net_pnl = outcome.net_pnl
                        sig.pnl = outcome.net_pnl
                        sig.r_multiple = outcome.r_multiple
                        sig.closed_at = outcome.exit_time or datetime.now(timezone.utc)

                        logger.info(
                            f"[Lifecycle] Resolved Signal {sig.signal_id} ({sig.asset} {sig.direction}) "
                            f"-> {outcome.outcome} | Net PnL: {outcome.net_pnl}"
                        )

                        # Broadcast outcome update via event bus / ws
                        try:
                            from app.api.v1.ws import broadcast_ws_message
                            await broadcast_ws_message(
                                "signal_outcome_updated",
                                {
                                    "signal_id": sig.signal_id,
                                    "asset": sig.asset,
                                    "direction": sig.direction,
                                    "outcome": outcome.outcome,
                                    "exit_price": outcome.exit_price,
                                    "net_pnl": outcome.net_pnl,
                                }
                            )
                        except Exception:
                            pass

                await session.commit()
            except Exception as e:
                logger.warning(f"Failed to resolve active signals: {e}")

    async def expire_old_predictions(self):
        session_factory = db_manager.get_session()
        if not session_factory:
            return

        now = datetime.now(timezone.utc)
        
        async with session_factory() as session:
            try:
                stmt = (
                    update(ForecastResultModel)
                    .where(ForecastResultModel.lifecycle_state == "ACTIVE")
                    .where(ForecastResultModel.expiry_timestamp <= now)
                    .values(lifecycle_state="EXPIRED")
                )
                res1 = await session.execute(stmt)
                
                stmt2 = (
                    update(ForecastConsensusModel)
                    .where(ForecastConsensusModel.lifecycle_state == "ACTIVE")
                    .where(ForecastConsensusModel.created_at <= now - timedelta(hours=24))
                    .values(lifecycle_state="EXPIRED")
                )
                await session.execute(stmt2)

                await session.commit()
                
                if res1.rowcount > 0:
                    logger.info(f"Prediction Lifecycle Manager: Expired {res1.rowcount} predictions.")
            except Exception as e:
                logger.warning(f"Failed to expire old predictions: {e}")

prediction_lifecycle_manager = PredictionLifecycleManager()

