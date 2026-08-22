
from fastapi import APIRouter

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/performance", summary="Get Performance Metrics")
async def get_performance():
    try:
        from app.journal.manager import journal_manager
        stats = await journal_manager.get_statistics()
        return {"success": True, **stats}
    except Exception as e:
        logger.warning(f"Performance error: {e}")
        return {"success": True, "total_trades": 0, "winning_trades": 0, "losing_trades": 0, "win_rate": 0, "total_pnl": 0, "avg_pnl": 0}

@router.get("/dashboard", summary="Get Dashboard Summary")
async def get_dashboard_summary():
    try:
        from app.database.manager import get_db_session
        from app.database.models.signal import SignalLifecycleModel
        from app.api.v1.signals import _get_ist_day_bounds_utc
        from sqlalchemy import select, or_
        from datetime import datetime, timezone
        
        start_utc, end_utc = _get_ist_day_bounds_utc(0)
        signals_today = 0
        today_wins = 0
        today_losses = 0
        today_net_pnl = 0.0
        active_signals_count = 0
        avg_confidence = 0.0
        avg_grade = "—"
        recent_results = []
        
        try:
            async for session in get_db_session():
                # 1. Fetch Today's signals
                stmt_today = select(SignalLifecycleModel).where(
                    SignalLifecycleModel.created_at >= start_utc,
                    SignalLifecycleModel.created_at < end_utc
                ).order_by(SignalLifecycleModel.created_at.desc())
                res_today = await session.execute(stmt_today)
                signals = res_today.scalars().all()
                
                signals_today = len(signals)
                if signals_today > 0:
                    valid_confidences = [s.confidence for s in signals if s.confidence is not None]
                    if valid_confidences:
                        avg_confidence = sum(valid_confidences) / len(valid_confidences)
                    
                    grades = [s.trade_quality for s in signals if s.trade_quality]
                    if grades:
                        grades.sort()
                        avg_grade = grades[0]

                    for s in signals:
                        state = (s.signal_state or s.outcome or "").upper()
                        if state == "TP_HIT":
                            today_wins += 1
                            if s.net_pnl is not None:
                                today_net_pnl += s.net_pnl
                        elif state == "SL_HIT":
                            today_losses += 1
                            if s.net_pnl is not None:
                                today_net_pnl += s.net_pnl
                        elif state in ("TIME_EXIT", "AMBIGUOUS", "EXPIRED"):
                            if s.net_pnl is not None:
                                today_net_pnl += s.net_pnl

                # 2. Count Active signals
                stmt_active = select(SignalLifecycleModel).where(
                    or_(
                        SignalLifecycleModel.status == "ACTIVE",
                        SignalLifecycleModel.signal_state == "ACTIVE"
                    )
                )
                res_active = await session.execute(stmt_active)
                active_signals_count = len(res_active.scalars().all())

                # 3. Recent 5 resolved results
                resolved_states = ["TP_HIT", "SL_HIT", "TIME_EXIT", "EXPIRED", "AMBIGUOUS", "COMPLETED"]
                stmt_recent = select(SignalLifecycleModel).where(
                    SignalLifecycleModel.signal_state.in_(resolved_states)
                ).order_by(SignalLifecycleModel.created_at.desc()).limit(5)
                res_recent = await session.execute(stmt_recent)
                for r in res_recent.scalars().all():
                    recent_results.append({
                        "signal_id": r.signal_id,
                        "asset": r.asset,
                        "direction": r.direction,
                        "entry_price": r.entry_price or r.current_price,
                        "exit_price": r.exit_price,
                        "outcome": r.signal_state or r.outcome,
                        "net_pnl": r.net_pnl,
                        "r_multiple": r.r_multiple,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                        "exit_time": r.exit_time.isoformat() if r.exit_time else None,
                    })
                break
        except Exception as db_err:
            logger.warning(f"Database session warning in dashboard summary: {db_err}")
            
        return {
            "success": True,
            "signals_today": signals_today,
            "today_wins": today_wins,
            "today_losses": today_losses,
            "today_net_pnl": round(today_net_pnl, 4),
            "active_signals_count": active_signals_count,
            "avg_confidence": round(avg_confidence, 4),
            "avg_grade": avg_grade,
            "recent_results": recent_results
        }
    except Exception as e:
        logger.warning(f"Dashboard summary error: {e}")
        return {
            "success": True,
            "signals_today": 0,
            "today_wins": 0,
            "today_losses": 0,
            "today_net_pnl": 0.0,
            "active_signals_count": 0,
            "avg_confidence": 0,
            "avg_grade": "—",
            "recent_results": []
        }



@router.get("/patterns", summary="Get Pattern Analysis")
async def get_patterns(symbol: str = "EURUSD"):
    try:
        from app.analytics.patterns import pattern_analyzer
        patterns = await pattern_analyzer.analyze(symbol) if hasattr(pattern_analyzer, "analyze") else []
        return {"success": True, "symbol": symbol, "patterns": patterns}
    except Exception as e:
        logger.warning(f"Patterns error: {e}")
        return {"success": True, "symbol": symbol, "patterns": []}


@router.get("/recommendations", summary="Get AI Recommendations")
async def get_recommendations():
    try:
        from app.analytics.recommendations import recommendation_engine
        recs = await recommendation_engine.get_recommendations() if hasattr(recommendation_engine, "get_recommendations") else []
        return {"success": True, "recommendations": recs}
    except Exception as e:
        logger.warning(f"Recommendations error: {e}")
        return {"success": True, "recommendations": []}


@router.get("/operational-metrics", summary="Get Live Operational Metrics")
async def get_operational_metrics():
    try:
        from app.tasks.monitoring import system_monitor
        metrics = system_monitor.get_operational_metrics()
        return {"success": True, **metrics}
    except Exception as e:
        logger.warning(f"Operational metrics error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/monte-carlo", summary="Get Monte Carlo Simulation Results")
async def get_monte_carlo():
    try:
        from app.analytics.monte_carlo import MonteCarloSimulator
        from app.journal.manager import journal_manager
        trades = await journal_manager.get_trades(limit=1000)
        
        # Remove mock trades injection
        if not trades:
            return {"success": True, "data": {}}
            
        simulator = MonteCarloSimulator(iterations=1000)
        result = simulator.simulate(trades)
        return {"success": True, "data": result}
    except Exception as e:
        logger.warning(f"Monte Carlo error: {e}")
        return {"success": False, "error": str(e)}

@router.get("/walk-forward", summary="Get Walk Forward Optimization Results")
async def get_walk_forward():
    try:
        from app.analytics.walk_forward import WalkForwardOptimizer
        from app.journal.manager import journal_manager
        trades = await journal_manager.get_trades(limit=1000)
        
        if not trades:
            return {"success": True, "data": {}}
            
        result = WalkForwardOptimizer.optimize(trades, window_size=50, step_size=10)
        return {"success": True, "data": result}
    except Exception as e:
        logger.warning(f"Walk forward error: {e}")
        return {"success": False, "error": str(e)}