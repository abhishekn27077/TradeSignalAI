"""
app/pipeline/orchestrator.py  — Phase 33
==========================================
Phase 33: trace_id injected at pipeline entry point. Every stage
receives and forwards the same UUID. Full lifecycle trace is built here.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone

from app.core.timing import CandleClock, ISTConverter
from app.market_data.registry import asset_registry
from app.analytics.forecast_manager import ForecastManager

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Phase 31 / Phase 33: True Signal Orchestrator.

    Phase 33 enhancement: generates a trace_id at candle boundary detection
    and propagates it through the entire pipeline. Every stage logs the
    same trace_id so the full signal lifecycle can be reconstructed.
    """

    def __init__(self):
        self._running = False
        self._task = None
        self.timeframes = ["H4", "D1", "W1"]
        self.forecast_manager = ForecastManager()

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Pipeline Orchestrator started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Pipeline Orchestrator stopped")

    async def _run_loop(self):
        logger.info("Entering precise orchestration loop...")
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                status = CandleClock.get_candle_status("H4", reference_time=now)

                remaining = status["remaining_seconds"]
                if remaining <= 0:
                    remaining = 240 * 60

                logger.info(
                    f"Orchestrator sleeping {remaining}s until next H4 candle boundary "
                    f"(closes at {status.get('current_candle_close_ist', '?')} IST)..."
                )

                await asyncio.sleep(remaining + 1)

                # ── Phase 33: generate trace_id AT candle boundary ─────────
                trace_id = str(uuid.uuid4())
                prediction_timestamp = datetime.now(timezone.utc)
                prediction_timestamp_ist = ISTConverter.to_ist_string(prediction_timestamp)

                logger.info(
                    f"[trace={trace_id}] Candle boundary reached at "
                    f"{prediction_timestamp.isoformat()} / {prediction_timestamp_ist}. "
                    f"Triggering full intelligence pipeline."
                )

                symbols = asset_registry.list_symbols()
                await self._trigger_pipeline(symbols, trace_id, prediction_timestamp)

            except asyncio.CancelledError:
                logger.info("Orchestrator loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in Orchestrator loop: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _trigger_pipeline(
        self,
        symbols: list[str],
        trace_id: str,
        prediction_timestamp: datetime,
    ):
        """
        Executes the intelligence pipeline with trace_id propagation.
        Phase 33: trace_id and prediction_timestamp are forwarded to
        forecast_manager and subsequently to MasterIntelligenceEngine.
        """
        logger.info(
            f"[trace={trace_id}] Triggering pipeline for {len(symbols)} symbols..."
        )
        try:
            results = await self.forecast_manager.scan_market(
                symbols,
                trace_id=trace_id,
                prediction_timestamp=prediction_timestamp,
            )
            from app.market_intelligence.h4_engine import h4_forecast_engine
            await h4_forecast_engine.publish_results(results)
        except Exception as e:
            logger.error(
                f"[trace={trace_id}] Pipeline execution failed: {e}", exc_info=True
            )


pipeline_orchestrator = PipelineOrchestrator()
