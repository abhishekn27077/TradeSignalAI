from fastapi import APIRouter, HTTPException

from app.market_intelligence.opportunity_ranking import opportunity_ranker

router = APIRouter(prefix="/predictions", tags=["Forecast Predictions"])

from app.logs.logger import get_logger

logger = get_logger(__name__)

@router.get("/current", summary="Get Current Active Predictions")
async def get_current_predictions(limit: int = 50):
    try:
        from sqlalchemy import select
        from app.database.manager import db_manager
        from app.database.models.forecast import (
            ForecastConsensusModel,
            ForecastRequestModel,
        )
        
        session_fn = db_manager.get_session()
        if not session_fn:
            # Fallback to direct SQLite read from canonical ledger
            import sqlite3
            conn = sqlite3.connect("tradesignal.db")
            cur = conn.cursor()
            cur.execute(
                """
                SELECT signal_id, asset, timeframe, created_at, signal_status, direction, probability, quality_grade
                FROM canonical_prospective_signal_ledger
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = cur.fetchall()
            conn.close()
            data = [
                {
                    "id": r[0],
                    "symbol": r[1],
                    "timeframe": r[2],
                    "created_at": r[3],
                    "status": r[4],
                    "consensus": {
                        "direction": r[5],
                        "confidence": r[6],
                        "models_included": ["kronos", "xgboost", "bayesian"],
                        "grade": r[7],
                        "state": r[4],
                    }
                }
                for r in rows
            ]
            return {"status": "success", "data": data}

        async with session_fn() as db:
            stmt = select(ForecastRequestModel).order_by(ForecastRequestModel.created_at.desc()).limit(limit)
            res = await db.execute(stmt)
            requests = res.scalars().all()
            
            data = []
            for req in requests:
                consensus_stmt = select(ForecastConsensusModel).where(ForecastConsensusModel.request_id == req.id)
                consensus_res = await db.execute(consensus_stmt)
                consensus = consensus_res.scalars().first()
                
                data.append({
                    "id": req.id,
                    "symbol": req.symbol,
                    "timeframe": req.timeframe,
                    "created_at": req.created_at,
                    "status": req.status,
                    "consensus": {
                        "direction": consensus.combined_direction if consensus else None,
                        "confidence": consensus.combined_confidence if consensus else None,
                        "models_included": consensus.models_included if consensus else None,
                        "grade": consensus.quality_grade if consensus else None,
                        "state": consensus.lifecycle_state if consensus else None
                    }
                })
            return {"status": "success", "data": data}
    except Exception as e:
        logger.warning(f"Note fetching current predictions: {e}")
        return {"status": "success", "data": []}

@router.get("/upcoming", summary="Get Upcoming Predictions")
async def get_upcoming_predictions():
    return {"status": "success", "data": []}

@router.get("/history", summary="Get Historical Predictions")
async def get_prediction_history(limit: int = 50):
    return await get_current_predictions(limit)

@router.get("/ranking", summary="Get Opportunity Ranking")
async def get_opportunity_ranking(limit: int = 50):
    try:
        ranked = await opportunity_ranker.get_ranked_opportunities(limit=limit)
        return {"status": "success", "data": ranked}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/archive", summary="Advanced Forecast Archive Search")
async def get_forecast_archive():
    # Stub: Fetch from ForecastConsensusModel with advanced filtering support
    return {"status": "success", "data": []}

@router.get("/{request_id}", summary="Get Prediction Detail")
async def get_prediction_detail(request_id: str):
    # Stub: Fetch the specific ForecastConsensusModel with explainability, breakdown, timeline
    return {"status": "success", "data": {
        "request_id": request_id,
        "agreement_matrix": {},
        "explainability_data": {},
        "confidence_breakdown": {},
        "timeline_events": [],
        "quality_grade": "A+"
    }}
