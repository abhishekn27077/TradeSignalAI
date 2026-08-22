import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from app.database.manager import db_manager
from app.database.models.forecast import (
    ForecastConsensusModel,
    ForecastRequestModel,
    ForecastResultModel,
)
from app.forecast_engine.base.models import ForecastRequest, ForecastResult
from app.forecast_engine.consensus.engine import forecast_consensus_engine
from app.forecast_engine.registry.manager import model_registry
from app.forecast_engine.validation.engine import forecast_validator
from app.logs.logger import get_logger
from app.utils.event_bus import event_bus

logger = get_logger(__name__)

class ForecastOrchestrator:
    """
    Coordinates the entire forecasting lifecycle:
    1. Receive request
    2. Load historical/feature data
    3. Dispatch to multiple providers in parallel
    4. Validate results
    5. Compute consensus
    6. Persist to DB
    """

    async def run_forecast(self, symbol: str, timeframe: str, forecast_horizon: int, market_regime: str = None) -> dict[str, Any]:
        request_id = str(uuid.uuid4())
        logger.info(f"Starting forecast orchestrator for {symbol} {timeframe}, request_id={request_id}")
        
        # 1. Create DB Request Record
        session_factory = db_manager.get_session()
        if not session_factory:
            return {"error": "Database not configured"}

        async with session_factory() as session:
            db_request = ForecastRequestModel(
                id=request_id,
                symbol=symbol,
                timeframe=timeframe,
                forecast_horizon=forecast_horizon,
                market_regime=market_regime,
                status="running"
            )
            session.add(db_request)
            await session.commit()

        # 2. Gather active models
        providers = model_registry.get_all_active_providers()
        if not providers:
            await self._update_request_status(request_id, "failed", "No active forecast models found")
            return {"error": "No active forecast models found"}

        # 3. Load Data (History & Features)
        from app.market_data.providers.manager import market_provider_manager
        rates = await market_provider_manager.get_rates(symbol, timeframe, count=200)
        historical_data = rates if rates else [] 
        feature_data = []    # TODO: Fetch from FeatureStore

        req_payload = ForecastRequest(
            request_id=request_id,
            symbol=symbol,
            timeframe=timeframe,
            forecast_horizon=forecast_horizon,
            market_regime=market_regime,
            historical_data=historical_data,
            feature_data=feature_data
        )

        # 4. Dispatch parallel predictions
        tasks = []
        for provider in providers:
            tasks.append(self._safe_predict(provider, req_payload))
        
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 5. Validate Results
        valid_results: list[ForecastResult] = []
        db_results: list[ForecastResultModel] = []
        
        for provider, res in zip(providers, raw_results):
            db_res = ForecastResultModel(
                request_id=request_id,
                model_id=provider.model_id,
            )
            
            if isinstance(res, Exception):
                logger.warning(f"Provider {provider.provider_name} failed: {res}")
                db_res.is_valid = False
                db_res.validation_errors = [str(res)]
                db_res.direction = "UNKNOWN"
                db_res.confidence = 0.0
            else:
                is_valid, errors = forecast_validator.validate(res)
                db_res.is_valid = is_valid
                db_res.validation_errors = errors
                db_res.direction = res.direction
                db_res.confidence = res.confidence
                db_res.expected_move_pct = res.expected_move_pct
                db_res.expected_volatility = res.expected_volatility
                db_res.expected_hold_candles = res.expected_hold_candles
                db_res.probability = res.probability
                db_res.reasoning_metadata = res.reasoning_metadata
                
                if is_valid:
                    valid_results.append(res)

            db_results.append(db_res)

        # 6. Compute Consensus
        consensus = forecast_consensus_engine.compute_consensus(valid_results)
        
        # Phase 5: Build Agreement Matrix, Explainability, Breakdown, Scorecard
        agreement_matrix = self._build_agreement_matrix(valid_results, consensus)
        explainability = self._build_explainability(valid_results, consensus, symbol)
        breakdown = self._build_confidence_breakdown(consensus)
        grade = self._calculate_quality_grade(consensus, agreement_matrix)
        
        # Timeline
        now_str = datetime.now(timezone.utc).isoformat()
        timeline = [
            {"state": "CREATED", "timestamp": now_str},
            {"state": "VALIDATED", "timestamp": now_str},
            {"state": "PUBLISHED", "timestamp": now_str}
        ]
        
        # Auto publish to active if grade is A+ or A, else just published/archived
        is_active = grade in ("A+", "A")
        initial_state = "ACTIVE" if is_active else "PUBLISHED"
        if is_active:
            timeline.append({"state": "ACTIVE", "timestamp": now_str})

        db_consensus = ForecastConsensusModel(
            request_id=request_id,
            combined_direction=consensus.combined_direction,
            combined_confidence=consensus.combined_confidence,
            combined_probability=consensus.combined_probability,
            weights_used=consensus.weights_used,
            models_included=consensus.models_included,
            agreement_matrix=agreement_matrix,
            explainability_data=explainability,
            confidence_breakdown=breakdown,
            timeline_events=timeline,
            quality_grade=grade,
            lifecycle_state=initial_state
        )

        # 7. Persist Results & Consensus
        async with session_factory() as session:
            session.add_all(db_results)
            session.add(db_consensus)
            
            # Update Request status
            from sqlalchemy import text
            await session.execute(
                text("UPDATE forecast_requests SET status = 'completed', completed_at = :now WHERE id = :id"),
                {"now": datetime.now(timezone.utc), "id": request_id}
            )
            await session.commit()

        logger.info(f"Forecast completed for {symbol}, Consensus: {consensus.combined_direction} ({consensus.combined_confidence:.2f}) - Grade {grade}")
        
        base_payload = {
            "symbol": symbol,
            "direction": consensus.combined_direction,
            "confidence": consensus.combined_confidence,
            "grade": grade,
            "request_id": request_id,
            "expected_move_pct": consensus.expected_move_pct,
            "expected_volatility": consensus.expected_volatility,
            "expected_hold_candles": consensus.expected_hold_candles
        }
        await event_bus.publish("ForecastCreated", base_payload)
        
        if is_active:
            await event_bus.publish("ForecastActive", base_payload)
            await event_bus.publish("RankingUpdated", {"source": "new_active_forecast"})
        
        return {
            "request_id": request_id,
            "status": "completed",
            "consensus": consensus.model_dump(),
            "models_ran": len(providers),
            "valid_results": len(valid_results),
            "grade": grade,
            "is_active": is_active
        }

    # -- Phase 5 Helpers --
    def _build_agreement_matrix(self, results: list[ForecastResult], consensus) -> dict[str, Any]:
        matrix = {"models": {}}
        agree_count = 0
        for r in results:
            agree = (r.direction == consensus.combined_direction)
            if agree: agree_count += 1
            matrix["models"][r.model_id] = {
                "direction": r.direction,
                "confidence": r.confidence,
                "agrees": agree
            }
        matrix["agreement_percentage"] = (agree_count / len(results)) * 100 if results else 0
        return matrix

    def _build_explainability(self, results: list[ForecastResult], consensus, symbol: str) -> dict[str, Any]:
        reasons = []
        for r in results:
            if r.reasoning_metadata:
                rule = r.reasoning_metadata.get("rule", r.model_id)
                reasons.append(f"{r.model_id} ({r.direction}): {rule}")
        
        return {
            "why_direction": f"Consensus {consensus.combined_direction} based on {len(results)} active models.",
            "market_regime": "Dynamic (Computed)",
            "historical_similarity": round(consensus.combined_confidence * 0.8, 2), # Approximated from confidence
            "risk_factors": [f"Divergence in {len([r for r in results if r.direction != consensus.combined_direction])} models"]
        }
        
    def _build_confidence_breakdown(self, consensus) -> dict[str, float]:
        conf = consensus.combined_confidence
        # We look at the actual weights used to distribute the confidence breakdown
        breakdown = {}
        for model_id, weight in consensus.weights_used.items():
            breakdown[model_id] = round(conf * weight, 4)
        return breakdown
        
    def _calculate_quality_grade(self, consensus, agreement_matrix) -> str:
        conf = consensus.combined_confidence
        agree = agreement_matrix.get("agreement_percentage", 0)
        
        if conf >= 0.90 and agree >= 80:
            return "A+"
        elif conf >= 0.85 and agree >= 70:
            return "A"
        elif conf >= 0.75:
            return "B"
        elif conf >= 0.60:
            return "C"
        return "D"

    async def _safe_predict(self, provider, request: ForecastRequest) -> Any:
        try:
            return await provider.predict(request)
        except NotImplementedError as e:
            return e
        except Exception as e:
            logger.error(f"Error in {provider.provider_name}: {e}")
            return e

    async def _update_request_status(self, request_id: str, status: str, error_msg: str = None):
        session_factory = db_manager.get_session()
        if not session_factory:
            return
        async with session_factory() as session:
            req = await session.get(ForecastRequestModel, request_id)
            if req:
                req.status = status
                req.error_message = error_msg
                req.completed_at = datetime.now(timezone.utc)
                await session.commit()

forecast_orchestrator = ForecastOrchestrator()
