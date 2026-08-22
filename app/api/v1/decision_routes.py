from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.database.manager import db_manager
from app.database.models.decision import DecisionHistoryModel

router = APIRouter()

@router.get("/history", response_model=list[dict[str, Any]])
async def get_decision_history(limit: int = 50):
    session_factory = db_manager.get_session()
    if not session_factory:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    async with session_factory() as session:
        result = await session.execute(
            select(DecisionHistoryModel)
            .order_by(DecisionHistoryModel.created_at.desc())
            .limit(limit)
        )
        decisions = result.scalars().all()
        
        return [
            {
                "id": d.id,
                "request_id": d.request_id,
                "qualification_score": d.qualification_score,
                "trade_grade": d.trade_grade,
                "is_approved": d.is_approved,
                "confidence": d.confidence,
                "risk_reward_ratio": d.risk_reward_ratio,
                "status": d.status,
                "explanation": d.explanation,
                "created_at": d.created_at.isoformat()
            } for d in decisions
        ]

@router.get("/{decision_id}", response_model=dict[str, Any])
async def get_decision_details(decision_id: str):
    session_factory = db_manager.get_session()
    if not session_factory:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    async with session_factory() as session:
        result = await session.execute(
            select(DecisionHistoryModel).filter(DecisionHistoryModel.id == decision_id)
        )
        decision = result.scalar_one_or_none()
        
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
            
        return {
            "id": decision.id,
            "request_id": decision.request_id,
            "qualification_score": decision.qualification_score,
            "trade_grade": decision.trade_grade,
            "is_approved": decision.is_approved,
            "confidence": decision.confidence,
            "model_agreement_pct": decision.model_agreement_pct,
            "risk_reward_ratio": decision.risk_reward_ratio,
            "expected_value": decision.expected_value,
            "max_drawdown_estimate": decision.max_drawdown_estimate,
            "probability_of_success": decision.probability_of_success,
            "market_regime": decision.market_regime,
            "session_score": decision.session_score,
            "active_session": decision.active_session,
            "entry_quality": decision.entry_quality,
            "recommended_profit_target": decision.recommended_profit_target,
            "recommended_stop_loss": decision.recommended_stop_loss,
            "recommended_trailing_stop": decision.recommended_trailing_stop,
            "explanation": decision.explanation,
            "warnings": decision.warnings,
            "rejection_reasons": decision.rejection_reasons,
            "status": decision.status,
            "created_at": decision.created_at.isoformat()
        }
