from typing import Optional, Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import require_role
from app.core.market_clock import market_clock
from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/swing")
async def get_swing_signals(limit: int = 20):
    """
    Get swing trading signals from canonical database (higher timeframe, longer hold).
    """
    try:
        from app.database.manager import db_manager
        from app.database.models.signal import SignalLifecycleModel
        from sqlalchemy import select, or_

        signals = []
        if db_manager.get_session():
            async with db_manager.get_session()() as db:
                stmt = select(SignalLifecycleModel).where(
                    or_(
                        SignalLifecycleModel.timeframe.in_(["1D", "D1", "1W", "W1", "4H", "H4"]),
                        SignalLifecycleModel.expected_hold_hours >= 24
                    )
                ).order_by(SignalLifecycleModel.created_at.desc()).limit(limit)
                res = await db.execute(stmt)
                db_signals = res.scalars().all()
                for s in db_signals:
                    signals.append({
                        c.name: getattr(s, c.name) for c in s.__table__.columns
                    })
        
        return {"status": "success", "data": signals, "count": len(signals)}
    except Exception as e:
        logger.error(f"Error fetching swing signals: {e}")
        return {"status": "success", "data": [], "count": 0}

@router.get("/h4-intelligence", summary="Get Live H4 Intelligence Scan Matrix")
async def get_h4_intelligence():
    """
    Returns the real-time H4 multi-model intelligence scan breakdown across all monitored assets:
    Asset | Price | Regime | Quant | Kronos | FAISS | Time Pattern | Consensus | Risk | Final
    Separates candidates from validated signals.
    """
    try:
        import pandas as pd
        from datetime import datetime, timezone
        from app.market_data.providers.manager import market_provider_manager
        from app.analytics.consensus_engine import ConsensusEngine
        from app.analytics.feature_engine import FeatureEngine
        from app.market_intelligence.pattern_engine import market_memory
        from app.core.timing import CandleClock
        from app.strategies.strategy_engine.regime_detector import MarketRegimeDetector
        from app.database.manager import db_manager
        from app.database.models.signal import SignalLifecycleModel

        symbols = ["BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "NAS100", "SPX500"]
        regime_detector = MarketRegimeDetector()
        consensus_engine = ConsensusEngine()
        
        status_clock = CandleClock.get_candle_status("H4")
        matrix = []
        candidates = []
        validated_signals = []
        rejected = []

        # 1. Fetch any active canonical H4 signals already in the database
        if db_manager.get_session():
            from sqlalchemy import select
            async with db_manager.get_session()() as db:
                stmt = select(SignalLifecycleModel).where(
                    SignalLifecycleModel.timeframe.in_(["4H", "H4"]),
                    SignalLifecycleModel.status.in_(["ACTIVE", "PENDING"])
                ).order_by(SignalLifecycleModel.created_at.desc())
                res = await db.execute(stmt)
                db_active_h4 = res.scalars().all()
                for s in db_active_h4:
                    validated_signals.append({
                        c.name: getattr(s, c.name) for c in s.__table__.columns
                    })

        for sym in symbols:
            try:
                rates = await market_provider_manager.get_rates(sym, "4H", count=100)
                if not rates or len(rates) < 10:
                    item = {
                        "asset": sym,
                        "price": "UNAVAILABLE",
                        "regime": "UNKNOWN",
                        "quant": "UNAVAILABLE",
                        "kronos": "UNAVAILABLE",
                        "faiss": "UNAVAILABLE",
                        "time_pattern": "INSUFFICIENT_HISTORICAL_SAMPLE",
                        "consensus": "UNAVAILABLE",
                        "confidence_pct": 0.0,
                        "risk": "NO_TRADE",
                        "risk_reason": "DATA_UNAVAILABLE",
                        "final": "NO_VALID_SETUP",
                        "status": "REJECTED"
                    }
                    matrix.append(item)
                    rejected.append(item)
                    continue

                df = pd.DataFrame(rates)
                df = FeatureEngine.add_all_features(df)
                latest_close = float(df['close'].iloc[-1]) if 'close' in df else float(rates[-1].get('close', 0.0))
                
                # Detect Regime
                regime = regime_detector.detect_regime(df)
                
                # Consensus breakdown
                c_res = consensus_engine.generate_consensus(sym, "4H", df)
                breakdown = c_res.get("breakdown", {})
                kronos_val = breakdown.get("kronos", 0.0)
                kronos_dir = "BULLISH" if kronos_val > 0.001 else "BEARISH" if kronos_val < -0.001 else "NEUTRAL"
                
                quant_sig = c_res.get("signal", "NEUTRAL")
                agreement_pct = c_res.get("agreement_percentage", 0.0)
                norm_agree = agreement_pct / 100.0 if agreement_pct > 1.0 else agreement_pct
                conf_score = c_res.get("confidence_score", 0.0)
                norm_conf = conf_score / 100.0 if conf_score > 1.0 else conf_score
                
                # Zero-Trust: Direction is only valid if agreement >= 75% AND confidence >= 65%
                is_valid_consensus = (norm_agree >= 0.75 and norm_conf >= 0.65 and quant_sig in ["BUY", "SELL", "BULLISH", "BEARISH"])
                consensus_dir = ("BUY" if quant_sig in ["BUY", "BULLISH"] else "SELL" if quant_sig in ["SELL", "BEARISH"] else "NEUTRAL") if is_valid_consensus else "NEUTRAL"
                
                # FAISS check
                latest_feats = df.drop(columns=['Future_Return_5', 'close'], errors='ignore').iloc[-1].to_dict()
                mem_res = market_memory.find_similar_patterns(sym, "4H", latest_feats, k=50)
                faiss_status = "VALID" if "error" not in mem_res and mem_res.get("k_matches", 0) >= 10 else "UNAVAILABLE"
                
                # Time pattern
                time_pattern_status = "INSUFFICIENT_HISTORICAL_SAMPLE"
                
                # Risk decision
                if is_valid_consensus:
                    risk_decision = "TAKE_NOW"
                    risk_reason = "CONFIRMED_CONSENSUS_BREAKOUT"
                    final_state = "VALIDATED"
                    cand_status = "VALIDATED"
                else:
                    risk_decision = "NO_TRADE"
                    risk_reason = "CONSENSUS_BELOW_THRESHOLD" if norm_conf < 0.65 else ("LOW_AGREEMENT" if norm_agree < 0.75 else "NO_VALID_SETUP")
                    final_state = "NO_VALID_SETUP"
                    cand_status = "REJECTED"

                row = {
                    "asset": sym,
                    "price": round(latest_close, 5 if latest_close < 10 else 2),
                    "regime": regime,
                    "quant": f"{quant_sig} ({norm_agree*100:.0f}%)",
                    "kronos": f"{kronos_dir} ({kronos_val:+.4f})",
                    "faiss": faiss_status,
                    "time_pattern": time_pattern_status,
                    "consensus": consensus_dir,
                    "confidence_pct": round(norm_conf * 100.0, 1),
                    "risk": risk_decision,
                    "risk_reason": risk_reason,
                    "final": final_state,
                    "status": cand_status
                }
                matrix.append(row)
                candidates.append(row)
                if cand_status == "REJECTED":
                    rejected.append(row)

            except Exception as e:
                err_row = {
                    "asset": sym,
                    "price": "ERROR",
                    "regime": "ERROR",
                    "quant": "ERROR",
                    "kronos": "ERROR",
                    "faiss": "ERROR",
                    "time_pattern": "ERROR",
                    "consensus": "ERROR",
                    "confidence_pct": 0.0,
                    "risk": "NO_TRADE",
                    "risk_reason": str(e),
                    "final": "PIPELINE_ERROR",
                    "status": "REJECTED"
                }
                matrix.append(err_row)
                rejected.append(err_row)

        return {
            "success": True,
            "assets_scanned": len(symbols),
            "valid_setups": len(validated_signals),
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "next_evaluation": status_clock.get("current_candle_close_ist") if status_clock else "—",
            "candle_boundary": status_clock,
            "candidates": candidates,
            "validated_signals": validated_signals,
            "rejected": rejected,
            "matrix": matrix
        }
    except Exception as e:
        logger.error(f"H4 intelligence matrix error: {e}")
        return {
            "success": False, 
            "assets_scanned": 0,
            "valid_setups": 0,
            "candidates": [], 
            "validated_signals": [], 
            "rejected": [], 
            "matrix": [], 
            "error": str(e)
        }

@router.post("/scan", summary="Trigger Live Market Scan")
async def trigger_market_scan():
    """
    Triggers an on-demand market scan using the institutional consensus engine
    across all supported instruments and timeframes.
    """
    try:
        from app.market_intelligence.swing_scanner import swing_scanner
        from app.strategies.manager import strategy_manager
        
        await swing_scanner.generate_forecasts()
        return {
            "success": True,
            "message": "Market scan completed successfully",
            "signals_found": len(strategy_manager.recent_signals)
        }
    except Exception as e:
        logger.error(f"Market scan failed: {e}")
        return {"success": False, "message": str(e), "signals_found": 0}

@router.post("/debug/inject", summary="Inject a strong signal for testing", dependencies=[Depends(require_role(["admin"]))])
async def inject_test_signal():
    try:
        import uuid
        from datetime import datetime, timezone

        from app.strategies.manager import strategy_manager
        
        strong_signal = {
            "signal_id": str(uuid.uuid4()),
            "symbol": "BTC/USD",
            "asset": "BTC/USD",
            "direction": "BUY",
            "confidence": 0.95,
            "strategy_name": "Consensus Engine",
            "winning_strategy": "SMCSequenceConfluenceStrategy",
            "strategy_votes": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trade_quality": "A+",
            "expected_move_pct": 5.0,
            "expected_hold_hours": 48,
            "market_regime": "BULLISH_TREND",
            "volatility_pct": 2.5,
            "timeframe": "H4"
        }
        
        strategy_manager.recent_signals.insert(0, strong_signal)
        from app.utils.event_bus import event_bus
        await event_bus.publish("SignalGenerated", payload=strong_signal)
        
        return {"status": "success", "message": "Injected strong test signal"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _get_ist_day_bounds_utc(days_ago: int = 0):
    """
    Calculates UTC bounds for a given IST calendar day (00:00:00 to 23:59:59.999999 IST).
    days_ago=0 -> Today in IST
    days_ago=1 -> Yesterday in IST
    """
    from datetime import datetime, timezone, timedelta
    from zoneinfo import ZoneInfo
    now_utc = datetime.now(timezone.utc)
    try:
        now_ist = now_utc.astimezone(ZoneInfo("Asia/Kolkata"))
    except Exception:
        # Fallback if tzdata missing
        now_ist = now_utc + timedelta(hours=5, minutes=30)

    target_day_ist = (now_ist - timedelta(days=days_ago)).replace(hour=0, minute=0, second=0, microsecond=0)
    next_day_ist = target_day_ist + timedelta(days=1)

    try:
        start_utc = target_day_ist.astimezone(timezone.utc)
        end_utc = next_day_ist.astimezone(timezone.utc)
    except Exception:
        start_utc = target_day_ist - timedelta(hours=5, minutes=30)
        end_utc = next_day_ist - timedelta(hours=5, minutes=30)
        start_utc = start_utc.replace(tzinfo=timezone.utc)
        end_utc = end_utc.replace(tzinfo=timezone.utc)

    return start_utc, end_utc


@router.get("/today", summary="Get Today's Signals (IST)")
async def get_today_signals():
    try:
        from app.database.manager import get_db_session
        from app.database.models.signal import SignalLifecycleModel
        from sqlalchemy import select
        
        signals = []
        start_utc, end_utc = _get_ist_day_bounds_utc(0)
        
        try:
            async for session in get_db_session():
                stmt = select(SignalLifecycleModel).where(
                    SignalLifecycleModel.created_at >= start_utc,
                    SignalLifecycleModel.created_at < end_utc
                ).order_by(SignalLifecycleModel.created_at.desc())
                res = await session.execute(stmt)
                db_signals = res.scalars().all()
                for s in db_signals:
                    if s.expiry_time and market_clock.is_target_time_expired(s.expiry_time):
                        continue
                    row = {c.name: getattr(s, c.name) for c in s.__table__.columns}
                    row["time_ist_formatted"] = market_clock.format_ist(s.created_at)
                    for k, v in row.items():
                        if hasattr(v, 'isoformat'):
                            row[k] = v.isoformat()
                    signals.append(row)
                break
        except Exception as e:
            logger.warning(f"Failed to fetch today's signals: {e}")
            
        return {"success": True, "signals": signals, "count": len(signals)}
    except Exception as e:
        return {"success": False, "signals": [], "message": str(e)}

@router.get("/yesterday", summary="Get Yesterday's Signals and Results (IST)")
async def get_yesterday_signals():
    try:
        from app.database.manager import get_db_session
        from app.database.models.signal import SignalLifecycleModel
        from sqlalchemy import select
        
        signals = []
        start_utc, end_utc = _get_ist_day_bounds_utc(1)
        
        try:
            async for session in get_db_session():
                stmt = select(SignalLifecycleModel).where(
                    SignalLifecycleModel.created_at >= start_utc,
                    SignalLifecycleModel.created_at < end_utc
                ).order_by(SignalLifecycleModel.created_at.desc())
                res = await session.execute(stmt)
                db_signals = res.scalars().all()
                for s in db_signals:
                    row = {c.name: getattr(s, c.name) for c in s.__table__.columns}
                    row["time_ist_formatted"] = market_clock.format_ist(s.created_at)
                    for k, v in row.items():
                        if hasattr(v, 'isoformat'):
                            row[k] = v.isoformat()
                    signals.append(row)
                break
        except Exception as e:
            logger.warning(f"Failed to fetch yesterday's signals: {e}")
            
        return {"success": True, "signals": signals, "count": len(signals)}
    except Exception as e:
        return {"success": False, "signals": [], "message": str(e)}

@router.get("/active", summary="Get Active Signals")
async def get_active_signals():
    try:
        from app.database.manager import get_db_session
        from app.database.models.signal import SignalLifecycleModel
        from sqlalchemy import select, or_
        
        signals = []
        try:
            async for session in get_db_session():
                stmt = select(SignalLifecycleModel).where(
                    or_(
                        SignalLifecycleModel.status == "ACTIVE",
                        SignalLifecycleModel.signal_state == "ACTIVE"
                    )
                ).order_by(SignalLifecycleModel.created_at.desc())
                res = await session.execute(stmt)
                db_signals = res.scalars().all()
                for s in db_signals:
                    if s.expiry_time and market_clock.is_target_time_expired(s.expiry_time):
                        continue
                    row = {c.name: getattr(s, c.name) for c in s.__table__.columns}
                    row["time_ist_formatted"] = market_clock.format_ist(s.created_at)
                    for k, v in row.items():
                        if hasattr(v, 'isoformat'):
                            row[k] = v.isoformat()
                    signals.append(row)
                break
        except Exception as e:
            logger.warning(f"Failed to fetch active signals: {e}")
            
        return {"success": True, "signals": signals, "count": len(signals)}
    except Exception as e:
        return {"success": False, "signals": [], "message": str(e)}

@router.get("/upcoming", summary="Get Upcoming Opportunities")
async def get_upcoming_signals():
    # Returns signals waiting for candle close or entry zone
    return {"success": True, "signals": []}

@router.get("/next", summary="Get Next Signal Evaluation")
async def get_next_signal_evaluation():
    try:
        from app.forecast_engine.next_signal import NextSignalEngine
        evals = [
            NextSignalEngine.get_next_opportunity("BTCUSD", "H4"),
            NextSignalEngine.get_next_opportunity("EURUSD", "H4"),
            NextSignalEngine.get_next_opportunity("SPX500", "H4")
        ]
        return {"success": True, "data": evals}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/history", summary="Get Signal History with Filters")
async def get_signal_history(
    limit: int = 100,
    time_range: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    asset: Optional[str] = None,
    ablation_mode: Optional[str] = None,
):
    try:
        from datetime import datetime, timezone, timedelta
        from app.database.manager import get_db_session
        from app.database.models.signal import SignalLifecycleModel
        from sqlalchemy import select, and_
        
        signals = []
        filters = []
        resolved_states = ["TP_HIT", "SL_HIT", "TIME_EXIT", "COMPLETED", "EXPIRED", "AMBIGUOUS"]
        filters.append(SignalLifecycleModel.signal_state.in_(resolved_states))

        now_utc = datetime.now(timezone.utc)
        if time_range == "today":
            start_utc, end_utc = _get_ist_day_bounds_utc(0)
            filters.append(SignalLifecycleModel.created_at >= start_utc)
            filters.append(SignalLifecycleModel.created_at < end_utc)
        elif time_range == "yesterday":
            start_utc, end_utc = _get_ist_day_bounds_utc(1)
            filters.append(SignalLifecycleModel.created_at >= start_utc)
            filters.append(SignalLifecycleModel.created_at < end_utc)
        elif time_range == "7d":
            filters.append(SignalLifecycleModel.created_at >= now_utc - timedelta(days=7))
        elif time_range == "30d":
            filters.append(SignalLifecycleModel.created_at >= now_utc - timedelta(days=30))
        elif start_date and end_date:
            try:
                s_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                e_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                filters.append(SignalLifecycleModel.created_at >= s_dt)
                filters.append(SignalLifecycleModel.created_at <= e_dt)
            except Exception:
                pass

        if asset:
            filters.append(SignalLifecycleModel.asset == asset.upper())

        try:
            async for session in get_db_session():
                stmt = select(SignalLifecycleModel)
                if filters:
                    stmt = stmt.where(and_(*filters))
                stmt = stmt.order_by(SignalLifecycleModel.created_at.desc()).limit(limit)
                
                res = await session.execute(stmt)
                db_signals = res.scalars().all()
                for s in db_signals:
                    row = {c.name: getattr(s, c.name) for c in s.__table__.columns}
                    row["time_ist_formatted"] = market_clock.format_ist(s.created_at)
                    # Filter by ablation mode in metadata if requested
                    if ablation_mode:
                        intel = row.get("intelligence_snapshot") or {}
                        strat = row.get("strategy_name") or ""
                        if ablation_mode not in str(intel) and ablation_mode not in strat:
                            continue

                    for k, v in row.items():
                        if hasattr(v, 'isoformat'):
                            row[k] = v.isoformat()
                    signals.append(row)
                break
        except Exception as e:
            logger.warning(f"Failed to fetch history signals: {e}")
            
        return {"success": True, "signals": signals, "count": len(signals)}
    except Exception as e:
        return {"success": False, "signals": [], "message": str(e)}


@router.get("/live", summary="Get Live Signal Panel")
async def get_live_signal_panel():
    try:
        import json

        from app.database.manager import db_manager
        from app.database.models.forecast import (
            ForecastConsensusModel,
            ForecastModelMetadata,
        )
        from app.strategies.ai_validation.engine import ai_validation_layer
        from app.strategies.manager import strategy_manager
        from app.strategies.prediction.engine import prediction_engine
        from app.strategies.scoring.trade_quality import trade_quality_engine

        consensus_score = 0
        models_used = []
        if db_manager.get_session():
            from sqlalchemy import select
            async with db_manager.get_session()() as db:
                stmt = select(ForecastConsensusModel).order_by(ForecastConsensusModel.created_at.desc()).limit(1)
                res = await db.execute(stmt)
                c_row = res.scalars().first()
                if c_row:
                    consensus_score = c_row.combined_confidence
                    weights = c_row.weights_used if isinstance(c_row.weights_used, dict) else json.loads(c_row.weights_used or "{}")
                    if weights:
                        model_ids = list(weights.keys())
                        stmt2 = select(ForecastModelMetadata).where(ForecastModelMetadata.id.in_(model_ids))
                        res2 = await db.execute(stmt2)
                        m_rows = res2.scalars().all()
                        models_used = [m.name for m in m_rows]


        signals = []
        if db_manager.get_session():
            async with db_manager.get_session()() as db:
                from app.database.models.signal import SignalLifecycleModel
                stmt = select(SignalLifecycleModel).order_by(SignalLifecycleModel.created_at.desc()).limit(10)
                res = await db.execute(stmt)
                db_signals = res.scalars().all()
                for s in db_signals:
                    signals.append({
                        c.name: getattr(s, c.name) for c in s.__table__.columns
                    })
            
        live_signals = []
        for sig in signals:
            try:
                prediction = prediction_engine.predict(None, sig.get("direction", "WAIT"), sig)
                quality = trade_quality_engine.evaluate_from_signal(sig)
                ai_result = ai_validation_layer.validate(sig)
                live_signals.append({
                    "signal": sig,
                    "prediction": prediction.to_dict(),
                    "trade_quality": {
                        "score": quality[0],
                        "grade": quality[1],
                        "details": quality[2],
                    },
                    "ai_validation": {
                        **ai_result.to_dict(),
                        "consensus_score": consensus_score,
                        "models_used": models_used
                    },
                })
            except Exception as e:
                live_signals.append({"signal": sig, "error": str(e)})
        return {"success": True, "live_signals": live_signals}
    except Exception as e:
        logger.warning(f"Live signal panel error: {e}")
        return {"success": False, "live_signals": []}


@router.get("/predict/{symbol}", summary="Get Prediction for Symbol")
async def get_prediction(symbol: str, timeframe: str = "4H"):
    try:
        from app.market_data.providers.manager import market_provider_manager
        from app.strategies.prediction.engine import prediction_engine
        rates = await market_provider_manager.get_rates(symbol, timeframe, count=100)
        if not rates:
            return {"success": False, "message": "No data"}
        import pandas as pd
        df = pd.DataFrame(rates)
        signal = {"direction": "WAIT", "confidence": None}
        prediction = prediction_engine.predict(df, "WAIT", signal)
        return {"success": True, "symbol": symbol, "timeframe": timeframe, "prediction": prediction.to_dict()}
    except Exception as e:
        logger.warning(f"Prediction error: {e}")
        return {"success": False, "message": str(e)}


@router.get("/quality", summary="Get Trade Quality Scores for Recent Signals")
async def get_trade_quality():
    try:
        from app.database.models.signal import SignalLifecycleModel
        from app.strategies.scoring.trade_quality import trade_quality_engine
        from sqlalchemy import select

        signals = []
        if db_manager.get_session():
            async with db_manager.get_session()() as db:
                stmt = select(SignalLifecycleModel).order_by(SignalLifecycleModel.created_at.desc()).limit(20)
                res = await db.execute(stmt)
                db_signals = res.scalars().all()
                for s in db_signals:
                    signals.append({
                        c.name: getattr(s, c.name) for c in s.__table__.columns
                    })

        results = []
        for sig in signals:
            score, grade, details = trade_quality_engine.evaluate_from_signal(sig)
            results.append({
                "signal_id": sig.get("signal_id", ""),
                "strategy": sig.get("strategy_name", ""),
                "symbol": sig.get("symbol", sig.get("asset", "")),
                "direction": sig.get("direction", ""),
                "score": score,
                "grade": grade,
                "verdict": details["verdict"],
                "breakdown": details["breakdown"],
            })
        return {"success": True, "quality_scores": results}
    except Exception as e:
        logger.warning(f"Trade quality error: {e}")
        return {"success": False, "quality_scores": []}


@router.get("/validate", summary="AI Validate Recent Signals")
async def ai_validate_signals():
    try:
        from app.database.models.signal import SignalLifecycleModel
        from app.strategies.ai_validation.engine import ai_validation_layer
        from sqlalchemy import select

        signals = []
        if db_manager.get_session():
            async with db_manager.get_session()() as db:
                stmt = select(SignalLifecycleModel).order_by(SignalLifecycleModel.created_at.desc()).limit(20)
                res = await db.execute(stmt)
                db_signals = res.scalars().all()
                for s in db_signals:
                    signals.append({
                        c.name: getattr(s, c.name) for c in s.__table__.columns
                    })

        results = []
        for sig in signals:
            result = ai_validation_layer.validate(sig)
            results.append({
                "signal_id": sig.get("signal_id", ""),
                "strategy": sig.get("strategy_name", ""),
                "symbol": sig.get("symbol", sig.get("asset", "")),
                "decision": result.decision,
                "confidence_adjustment": result.confidence_adjustment,
                "reasoning": result.reasoning,
                "risk_summary": result.risk_summary,
                "alternative_scenario": result.alternative_scenario,
            })
        return {"success": True, "validations": results}
    except Exception as e:
        logger.warning(f"AI validation error: {e}")
        return {"success": False, "validations": []}


@router.get("/holding/{strategy_name}", summary="Get Adaptive Holding Decision")
async def get_holding_decision(
    strategy_name: str,
    direction: str = "BUY",
    asset_type: str = "forex",
    elapsed_minutes: int = 30,
    trend_valid: bool | None = None,
    momentum_valid: bool | None = None,
    ai_agrees: bool | None = None,
    risk_acceptable: bool | None = None,
):
    try:
        from app.strategies.holding.adaptive import adaptive_holding
        decision = adaptive_holding.evaluate(
            direction=direction,
            asset_type=asset_type,
            elapsed_minutes=elapsed_minutes,
            trend_valid=trend_valid,
            momentum_valid=momentum_valid,
            ai_agrees=ai_agrees,
            risk_acceptable=risk_acceptable,
        )
        return {"success": True, "decision": decision.to_dict()}
    except Exception as e:
        logger.warning(f"Holding decision error: {e}")
        return {"success": False, "message": str(e)}


@router.get("/smc_analysis/{symbol}", summary="Get SMC Breakdown for Symbol")
async def get_smc_analysis(symbol: str):
    try:
        import pandas as pd

        from app.market_data.providers.manager import market_provider_manager
        from app.strategies.smart_money.blocks import order_block_engine
        from app.strategies.smart_money.fvg import fvg_engine
        from app.strategies.smart_money.liquidity import liquidity_engine
        from app.strategies.smart_money.structure import structure_engine
        rates = await market_provider_manager.get_rates(symbol, "1H", count=200)
        if not rates:
            return {"success": False, "message": "Failed to fetch market data"}
        df = pd.DataFrame(rates)
        structure = structure_engine.analyze(df)
        liquidity = liquidity_engine.analyze(df)
        blocks = order_block_engine.analyze(df)
        fvgs = fvg_engine.analyze(df)
        return {
            "success": True,
            "symbol": symbol,
            "smc_data": {
                "structure": structure,
                "liquidity": liquidity,
                "order_blocks": blocks,
                "fvg": fvgs,
            },
        }
    except Exception as e:
        logger.warning(f"Failed to perform SMC analysis for {symbol}: {e}")
        return {"success": False, "error": str(e)}

@router.get("/{signal_id}", summary="Get Complete Canonical Signal Record")
async def get_signal_by_id(signal_id: str):
    try:
        from app.database.manager import get_db_session
        from app.database.models.signal import SignalLifecycleModel
        from sqlalchemy import select
        
        signal = None
        async for session in get_db_session():
            res = await session.execute(select(SignalLifecycleModel).where(SignalLifecycleModel.signal_id == signal_id))
            signal = res.scalars().first()
            break
            
        if not signal:
            return {"success": False, "error": "Signal not found"}
            
        row = {c.name: getattr(signal, c.name) for c in signal.__table__.columns}
        for k, v in row.items():
            if hasattr(v, 'isoformat'):
                row[k] = v.isoformat()
                
        return {"success": True, "signal": row}
    except Exception as e:
        logger.error(f"Error fetching signal {signal_id}: {e}")
        return {"success": False, "error": str(e)}

@router.get("/{signal_id}/ai-consensus", summary="Get AI Consensus Breakdown for Signal")
async def get_signal_ai_consensus(signal_id: str):
    try:
        from app.database.manager import get_db_session
        from app.database.models.signal import SignalLifecycleModel
        from sqlalchemy import select
        
        signal = None
        async for session in get_db_session():
            res = await session.execute(select(SignalLifecycleModel).where(SignalLifecycleModel.signal_id == signal_id))
            signal = res.scalars().first()
            break
            
        if not signal:
            return {"success": False, "error": "Signal not found"}
            
        # Only return real data - do NOT fabricate model consensus
        models_used = signal.ai_models_used or []
        model_trace = signal.model_trace  # Real per-model trace from Phase 33
        intelligence_snapshot = signal.intelligence_snapshot
        
        return {
            "success": True,
            "signal_id": signal_id,
            "consensus_pct": signal.consensus_pct,
            "models_used": models_used,
            "model_trace": model_trace,  # Real trace or null
            "intelligence_snapshot": intelligence_snapshot,  # Real snapshot or null
            "data_availability": "REAL" if (model_trace or intelligence_snapshot) else "UNAVAILABLE",
        }
    except Exception as e:
        logger.error(f"Error fetching AI consensus: {e}")
        return {"success": False, "error": str(e)}
