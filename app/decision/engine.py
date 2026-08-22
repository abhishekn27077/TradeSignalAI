import uuid
from typing import Any

from app.database.manager import db_manager
from app.database.models.decision import DecisionHistoryModel
from app.decision.entry import entry_quality_analyzer
from app.decision.exit import exit_intelligence
from app.decision.explanation import explanation_generator
from app.decision.qualification import trade_qualification_system
from app.decision.regime import market_regime_engine
from app.decision.risk_reward import risk_reward_analyzer
from app.decision.session import session_analyzer
from app.logs.logger import get_logger
from app.utils.event_bus import event_bus

logger = get_logger(__name__)

class DecisionEngine:
    def __init__(self):
        pass

    async def handle_forecast_created(self, payload: dict[str, Any]):
        """
        Triggered when ForecastOrchestrator finishes and emits ForecastCreated.
        """
        request_id = payload.get("request_id")
        symbol = payload.get("symbol")
        direction = payload.get("direction")
        confidence = payload.get("confidence", 0.0)
        
        logger.info(f"DecisionEngine evaluating forecast {request_id} for {symbol}")
        
        # 1. Gather component analysis
        regime_data = market_regime_engine.analyze(symbol)
        session_data = session_analyzer.analyze()
        entry_data = entry_quality_analyzer.analyze(symbol, direction, 50000.0, payload) # Stub price
        
        # Stub expected move
        expected_move = 0.05 
        exit_data = exit_intelligence.analyze(symbol, direction, 50000.0, expected_move)
        
        rr_data = risk_reward_analyzer.analyze(
            entry_price=50000.0,
            profit_target=exit_data.get("recommended_profit_target"),
            stop_loss=exit_data.get("recommended_stop_loss"),
            probability=confidence
        )
        
        # 2. Aggregate factors for qualification
        factors = {
            "confidence": confidence,
            "rr_ratio": rr_data.get("rr_ratio", 0),
            "session_score": session_data.get("session_score", 0),
            "entry_quality_score": entry_data.get("entry_quality_score", 0),
            "model_agreement_pct": payload.get("agreement_percentage", 80.0) / 100.0 # Stub 80%
        }
        
        qual_data = trade_qualification_system.qualify(factors)
        
        # 3. Generate Explanation
        explanation_data = explanation_generator.generate(
            score=qual_data["qualification_score"],
            grade=qual_data["trade_grade"],
            is_approved=qual_data["is_approved"],
            factors=factors
        )
        
        # 4. Save to DB
        decision_id = str(uuid.uuid4())
        session_factory = db_manager.get_session()
        
        if session_factory:
            async with session_factory() as session:
                db_model = DecisionHistoryModel(
                    id=decision_id,
                    request_id=request_id,
                    qualification_score=qual_data["qualification_score"],
                    trade_grade=qual_data["trade_grade"],
                    is_approved=qual_data["is_approved"],
                    confidence=confidence,
                    model_agreement_pct=factors["model_agreement_pct"],
                    risk_reward_ratio=rr_data.get("rr_ratio"),
                    expected_value=rr_data.get("expected_value"),
                    max_drawdown_estimate=rr_data.get("max_drawdown_estimate"),
                    probability_of_success=rr_data.get("probability_of_success"),
                    market_regime=regime_data.get("regime"),
                    session_score=session_data.get("session_score"),
                    active_session=session_data.get("active_session"),
                    entry_quality=entry_data.get("entry_quality_score"),
                    recommended_profit_target=exit_data.get("recommended_profit_target"),
                    recommended_stop_loss=exit_data.get("recommended_stop_loss"),
                    recommended_trailing_stop=exit_data.get("recommended_trailing_stop"),
                    explanation=explanation_data.get("explanation"),
                    warnings=explanation_data.get("warnings"),
                    rejection_reasons=explanation_data.get("rejection_reasons"),
                    status="PUBLISHED" if qual_data["is_approved"] else "REJECTED"
                )
                session.add(db_model)
                await session.commit()
                
        # 5. Broadcast Decision events
        decision_payload = {
            "decision_id": decision_id,
            "request_id": request_id,
            "symbol": symbol,
            "direction": direction,
            "is_approved": qual_data["is_approved"],
            "trade_grade": qual_data["trade_grade"],
            "qualification_score": qual_data["qualification_score"],
            "explanation": explanation_data.get("explanation")
        }
        
        await event_bus.publish("DecisionCreated", decision_payload)
        
        if qual_data["is_approved"]:
            await event_bus.publish("DecisionApproved", decision_payload)
        else:
            await event_bus.publish("DecisionRejected", decision_payload)

decision_engine = DecisionEngine()
event_bus.subscribe("ForecastCreated", decision_engine.handle_forecast_created)
