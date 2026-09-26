import asyncio
from typing import Any

from app.logs.logger import get_logger
from app.utils.event_bus import event_bus
from app.database.manager import get_db_session
from app.database.models.signal import SignalLifecycleModel
import uuid

logger = get_logger(__name__)


class ExecutionCoordinator:
    def __init__(self):
        self._running = False
        self._risk_engine = None
        self._event_listeners = []

    def start(self):
        self._running = True
        try:
            from app.risk.engine import RiskEngine
            self._risk_engine = RiskEngine()
            logger.info("ExecutionCoordinator started")
        except Exception as e:
            logger.warning(f"RiskEngine init skipped: {e}")
            self._risk_engine = None

    def stop(self):
        self._running = False
        logger.info("ExecutionCoordinator stopped")

    async def validate_and_execute(self, trade_proposal: dict[str, Any]) -> dict[str, Any]:
        if not self._running:
            return {"status": "ERROR", "error": "Coordinator not running"}

        signal_id = trade_proposal.get("signal_id")
        
        async def update_signal_status(status: str, exec_status: str = None, p_trade_id: str = None):
            if not signal_id:
                return
            from sqlalchemy import update
            async for session in get_db_session():
                try:
                    stmt = update(SignalLifecycleModel).where(SignalLifecycleModel.signal_id == signal_id).values(status=status)
                    if exec_status:
                        stmt = stmt.values(execution_status=exec_status)
                    if p_trade_id:
                        stmt = stmt.values(paper_trade_id=p_trade_id)
                    await session.execute(stmt)
                    await session.commit()
                    
                    # Broadcast update to frontend
                    sig_data = await session.execute(
                        from_sqlalchemy_select:=__import__("sqlalchemy").select(SignalLifecycleModel).where(SignalLifecycleModel.signal_id == signal_id)
                    )
                    sig_obj = sig_data.scalars().first()
                    if sig_obj:
                        import json
                        def default_serializer(obj):
                            if isinstance(obj, __import__("datetime").datetime): return obj.isoformat()
                            return str(obj)
                        
                        payload = {
                            c.name: getattr(sig_obj, c.name) for c in sig_obj.__table__.columns
                        }
                        await event_bus.publish("SignalUpdated", payload=json.loads(json.dumps(payload, default=default_serializer)))
                    break
                except Exception as e:
                    logger.error(f"Failed to update signal status: {e}")

        await update_signal_status("RISK CHECK")

        risk_ok = True
        risk_details = {}
        if self._risk_engine:
            try:
                risk_result = self._risk_engine.validate_trade(trade_proposal)
                if isinstance(risk_result, dict):
                    risk_ok = risk_result.get("approved", True)
                    risk_details = risk_result
                else:
                    risk_ok = bool(risk_result)
            except Exception as e:
                logger.warning(f"Risk validation error: {e}")
                risk_details = {"error": str(e)}

        if not risk_ok:
            await update_signal_status("REJECTED", exec_status="RISK_FAILED")
            return {
                "status": "REJECTED",
                "reason": "Risk validation failed",
                "risk_details": risk_details,
            }
            
        from app.execution.failsafe import failsafe_manager

        # Read real account state for failsafe checks (not hardcoded zeros)
        try:
            from app.paper_trading.account_manager import account_manager
            accounts = list(account_manager.accounts.values())
            if accounts:
                acc = accounts[0]
                initial_balance = 100000.0  # matches paper executor default
                daily_loss_pct = max(0.0, (initial_balance - acc.balance) / initial_balance * 100)
                max_equity = max(initial_balance, acc.equity)
                drawdown_pct = ((max_equity - acc.equity) / max_equity * 100) if max_equity > 0 else 0.0
                broker_connected = True  # paper broker is always "connected"
            else:
                daily_loss_pct, drawdown_pct, broker_connected = 0.0, 0.0, True
        except Exception:
            daily_loss_pct, drawdown_pct, broker_connected = 0.0, 0.0, True

        account_state = {
            "daily_loss_pct": daily_loss_pct,
            "drawdown_pct": drawdown_pct,
            "broker_connected": broker_connected,
            "equity": acc.equity if accounts else 100000.0,
        }
        
        can_execute, failsafe_reason = failsafe_manager.evaluate_failsafes(account_state, trade_proposal)
        if not can_execute:
            logger.warning(f"Trade rejected by FailsafeManager: {failsafe_reason}")
            await update_signal_status("REJECTED", exec_status="FAILSAFE_TRIGGERED")
            return {
                "status": "REJECTED",
                "reason": failsafe_reason
            }

        # Phase 74: Fail-closed duplicate signal guard on production execution path
        try:
            from app.core.signal_identity import SignalIdentityGuard
            from app.database.manager import db_manager
            identity_hash = SignalIdentityGuard.build_identity(trade_proposal)
            if db_manager._session_factory:
                async with db_manager.get_session()() as session:
                    is_dup = await SignalIdentityGuard.is_duplicate(session, identity_hash)
                    if is_dup:
                        logger.warning(f"Trade rejected by SignalIdentityGuard: duplicate signal detected ({identity_hash[:16]})")
                        await update_signal_status("REJECTED", exec_status="DUPLICATE_SIGNAL")
                        return {"status": "REJECTED", "reason": "DUPLICATE_SIGNAL"}
        except Exception as e:
            logger.error(f"Duplicate check fail-closed error: {e}")
            await update_signal_status("REJECTED", exec_status="DUPLICATE_CHECK_FAILED")
            return {"status": "REJECTED", "reason": "DUPLICATE_CHECK_FAILED"}

        await update_signal_status("ENTRY CREATED")

        try:
            from app.execution.router import smart_router

            result = await smart_router.execute_trade(
                symbol=trade_proposal.get("symbol", "EURUSD"),
                direction=trade_proposal.get("direction", "BUY"),
                quantity=trade_proposal.get("quantity", 0.1),
                order_type=trade_proposal.get("order_type", "MARKET"),
                price=trade_proposal.get("price"),
            )

            try:
                payload = {
                    "symbol": trade_proposal.get("symbol"),
                    "result": result,
                    "strategy_used": trade_proposal.get("strategy", "Manual")
                }
                # Forward decision card metadata to downstream systems (Journal, Analytics)
                for k, v in trade_proposal.items():
                    if k not in payload:
                        payload[k] = v
                        
                await event_bus.publish("trade_executed", payload)
                await update_signal_status("ACTIVE", exec_status="EXECUTED", p_trade_id=result.get("order_id", ""))
            except Exception:
                pass

            return result
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            await update_signal_status("REJECTED", exec_status=f"EXECUTION_ERROR: {e}")
            return {"status": "ERROR", "error": f"Execution failed: {e}"}

    async def _on_consensus_completed(self, payload: dict, **kwargs):
        payload_data = kwargs.get("payload", payload) if kwargs else payload
        logger.info(f"Coordinator received ConsensusCompleted payload: {payload_data}")
        signal = payload_data.get("signal")
        if signal in ["BUY", "SELL"]:
            logger.info(f"Coordinator received consensus signal: {signal} for {payload_data.get('symbol')}")
            trade_proposal = {
                "symbol": payload_data.get("symbol"),
                "direction": signal,
                "order_type": "MARKET",
                "quantity": 0.01, # Default quantity, can be overridden by risk engine
                "broker_type": "TradingView", # Enforce TradingView
                "price": payload_data.get("entry_price"), # Passed for PaperExecution
                "target": payload_data.get("target"),
                "stop_loss": payload_data.get("stop_loss"),
                "market_regime": payload_data.get("market_regime"),
                "volatility_pct": payload_data.get("volatility_pct"),
                "trend_strength": payload_data.get("trend_strength"),
                "trade_quality": payload_data.get("trade_quality"),
                "news_impact": payload_data.get("news_impact"),
                "historical_similars": payload_data.get("historical_similars"),
                "agents": payload_data.get("agents", [])
            }
            
            # Persist to SignalLifecycle
            async def persist_signal(tp: dict):
                async for session in get_db_session():
                    try:
                        sig_id = str(uuid.uuid4())
                        tp["signal_id"] = sig_id
                        
                        db_signal = SignalLifecycleModel(
                            signal_id=sig_id,
                            asset=tp["symbol"],
                            timeframe="1m", # Default for now
                            direction=tp["direction"],
                            strategy_name="Consensus Engine",
                            confidence=payload_data.get("confidence", 0.0),
                            strength="STRONG" if payload_data.get("confidence", 0.0) > 0.8 else "MODERATE",
                            risk_level="MEDIUM",
                            trade_quality=tp.get("trade_quality", "C"),
                            stop_loss=tp.get("stop_loss"),
                            take_profit_1=tp.get("target"),
                            volatility=tp.get("volatility_pct"),
                            market_trend=tp.get("market_regime"),
                            ai_models_used=[a.get("agent_id") for a in tp.get("agents", []) if isinstance(a, dict)],
                            consensus_pct=payload_data.get("confidence", 0.0),
                            status="GENERATED"
                        )
                        session.add(db_signal)
                        await session.commit()
                        
                        # Pass to execution
                        asyncio.create_task(self.validate_and_execute(tp))
                        break
                    except Exception as e:
                        logger.error(f"Failed to persist SignalLifecycle: {e}")
                        
            asyncio.create_task(persist_signal(trade_proposal))

coordinator = ExecutionCoordinator()

try:
    event_bus.subscribe("ConsensusCompleted", coordinator._on_consensus_completed)
except Exception as e:
    logger.warning(f"Failed to subscribe coordinator to consensus: {e}")