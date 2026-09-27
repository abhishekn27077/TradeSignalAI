import asyncio
import json
import time
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.logs.logger import get_logger
from app.utils.event_bus import event_bus
from app.utils.websocket_manager import ws_manager

logger = get_logger(__name__)

router = APIRouter(tags=["WebSocket"])


async def broadcast_tick(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    if payload is None:
        return
    symbol = payload.get("symbol", payload.symbol if hasattr(payload, "symbol") else "unknown")
    message = json.dumps({
        "event": "tick",
        "data": {
            "symbol": symbol,
            "price": payload.get("price", getattr(payload, "price", 0)),
            "volume": payload.get("volume", getattr(payload, "volume", 0)),
            "timestamp": str(payload.get("timestamp", getattr(payload, "timestamp", ""))),
        },
    })
    try:
        await ws_manager.broadcast(message, topic="ticks")
    except Exception:
        pass


async def broadcast_order_update(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    message = json.dumps({"event": "order_update", "data": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="orders")
    except Exception:
        pass


async def broadcast_position_update(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    message = json.dumps({"event": "position_update", "data": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="positions")
    except Exception:
        pass


async def broadcast_signal(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    message = json.dumps({"event": "signal_generated", "data": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="signals")
    except Exception:
        pass


async def broadcast_system_health(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    message = json.dumps({"event": "system_health", "data": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="system")
    except Exception:
        pass
async def broadcast_portfolio(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    message = json.dumps({"event": "portfolio_update", "data": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="portfolio")
    except Exception:
        pass


async def broadcast_risk(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    message = json.dumps({"event": "risk_update", "data": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="risk")
    except Exception:
        pass


async def broadcast_agent_status(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    message = json.dumps({"event": "agent_update", "data": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="ai")
    except Exception:
        pass


async def broadcast_consensus(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    message = json.dumps({"event": "consensus_update", "data": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="ai")
    except Exception:
        pass


async def broadcast_news(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    message = json.dumps({"event": "news_received", "data": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="news")
    except Exception:
        pass


async def broadcast_data_sync(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    event_name = kwargs.get("event_name", "DataSyncUpdate")
    message = json.dumps({"type": event_name, "payload": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="data_sync")
    except Exception:
        pass

async def broadcast_forecast(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    event_name = kwargs.get("event_name", "forecast_update")
    message = json.dumps({"event": event_name, "data": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="forecast")
    except Exception:
        pass

async def broadcast_replay(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    message = json.dumps({"event": "replay_tick", "data": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="replay")
    except Exception:
        pass

async def broadcast_research(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    event_name = kwargs.get("event_name", "research_update")
    message = json.dumps({"event": event_name, "data": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="research")
    except Exception:
        pass

async def broadcast_decision(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    event_name = kwargs.get("event_name", "decision_update")
    message = json.dumps({"event": event_name, "data": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="decision")
    except Exception:
        pass

async def broadcast_portfolio_intelligence(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    event_name = kwargs.get("event_name", "portfolio_intel_update")
    message = json.dumps({"event": event_name, "data": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="portfolio_intelligence")
    except Exception:
        pass

async def broadcast_strategy_lab(*args, **kwargs):
    payload = kwargs.get("payload") or (args[0] if args else None)
    event_name = kwargs.get("event_name", "strategy_lab_update")
    message = json.dumps({"event": event_name, "data": payload}, default=str)
    try:
        await ws_manager.broadcast(message, topic="strategy_lab")
    except Exception:
        pass

try:
    event_bus.subscribe("TickReceived", broadcast_tick)
    event_bus.subscribe("ReplayTick", broadcast_replay)
    
    # Orders
    event_bus.subscribe("OrderExecuted", broadcast_order_update)
    event_bus.subscribe("OrderUpdated", broadcast_order_update)
    event_bus.subscribe("PaperOrderCreated", broadcast_order_update)
    event_bus.subscribe("PaperOrderStatusUpdated", broadcast_order_update)
    event_bus.subscribe("OrderSubmitted", broadcast_order_update)
    event_bus.subscribe("OrderRejected", broadcast_order_update)
    event_bus.subscribe("OrderFilled", broadcast_order_update)
    event_bus.subscribe("trade_executed", broadcast_order_update)
    
    # Positions
    event_bus.subscribe("PositionUpdated", broadcast_position_update)
    event_bus.subscribe("PositionClosed", broadcast_position_update)
    event_bus.subscribe("PositionOpened", broadcast_position_update)
    
    # Signals & AI
    event_bus.subscribe("SignalGenerated", broadcast_signal)
    event_bus.subscribe("AgentStatusUpdated", broadcast_agent_status)
    event_bus.subscribe("ConsensusStarted", broadcast_consensus)
    event_bus.subscribe("ConsensusCompleted", broadcast_consensus)
    
    # Forecast Intelligence
    event_bus.subscribe("ForecastCreated", lambda *a, **k: broadcast_forecast(*a, event_name="forecast_created", **k))
    event_bus.subscribe("ForecastUpdated", lambda *a, **k: broadcast_forecast(*a, event_name="forecast_updated", **k))
    event_bus.subscribe("ForecastExpired", lambda *a, **k: broadcast_forecast(*a, event_name="forecast_expired", **k))
    event_bus.subscribe("RankingUpdated", lambda *a, **k: broadcast_forecast(*a, event_name="ranking_updated", **k))
    
    # Quantitative Research
    event_bus.subscribe("ForecastEvaluated", lambda *a, **k: broadcast_research(*a, event_name="forecast_evaluated", **k))
    
    # Decision Intelligence
    event_bus.subscribe("DecisionCreated", lambda *a, **k: broadcast_decision(*a, event_name="decision_created", **k))
    event_bus.subscribe("DecisionUpdated", lambda *a, **k: broadcast_decision(*a, event_name="decision_updated", **k))
    event_bus.subscribe("DecisionApproved", lambda *a, **k: broadcast_decision(*a, event_name="decision_approved", **k))
    event_bus.subscribe("DecisionRejected", lambda *a, **k: broadcast_decision(*a, event_name="decision_rejected", **k))
    
    # Portfolio Intelligence
    event_bus.subscribe("CurrencyStrengthChanges", lambda *a, **k: broadcast_portfolio_intelligence(*a, event_name="currency_strength", **k))
    event_bus.subscribe("CorrelationUpdates", lambda *a, **k: broadcast_portfolio_intelligence(*a, event_name="correlation", **k))
    event_bus.subscribe("MarketRotationUpdates", lambda *a, **k: broadcast_portfolio_intelligence(*a, event_name="market_rotation", **k))
    event_bus.subscribe("ExposureChanges", lambda *a, **k: broadcast_portfolio_intelligence(*a, event_name="exposure", **k))
    
    # Portfolio, Risk, System
    event_bus.subscribe("SystemHealthUpdate", broadcast_system_health)
    event_bus.subscribe("PortfolioUpdated", broadcast_portfolio)
    event_bus.subscribe("RiskUpdated", broadcast_risk)
    
    # Strategy Lab (Phase 11)
    event_bus.subscribe("ExperimentStarted", lambda *a, **k: broadcast_strategy_lab(*a, event_name="experiment_started", **k))
    event_bus.subscribe("ExperimentFinished", lambda *a, **k: broadcast_strategy_lab(*a, event_name="experiment_finished", **k))
    event_bus.subscribe("BenchmarkUpdated", lambda *a, **k: broadcast_strategy_lab(*a, event_name="benchmark_updated", **k))
    event_bus.subscribe("StrategyPromoted", lambda *a, **k: broadcast_strategy_lab(*a, event_name="strategy_promoted", **k))
    event_bus.subscribe("StrategyRetired", lambda *a, **k: broadcast_strategy_lab(*a, event_name="strategy_retired", **k))
    
    # News
    event_bus.subscribe("NewsProcessed", broadcast_news)
    event_bus.subscribe("HighImpactNews", broadcast_news)
    
    # Memory and Journal
    async def broadcast_journal(*args, **kwargs):
        payload = kwargs.get("payload") or (args[0] if args else None)
        message = json.dumps({"event": "journal_update", "data": payload}, default=str)
        try:
            await ws_manager.broadcast(message, topic="journal")
        except Exception:
            pass
            
    async def broadcast_memory(*args, **kwargs):
        payload = kwargs.get("payload") or (args[0] if args else None)
        message = json.dumps({"event": "memory_update", "data": payload}, default=str)
        try:
            await ws_manager.broadcast(message, topic="memory")
        except Exception:
            pass
            
    event_bus.subscribe("JournalUpdated", broadcast_journal)
    event_bus.subscribe("MemoryUpdated", broadcast_memory)
    
    # Data Sync
    event_bus.subscribe("DataSyncProgress", lambda *a, **k: broadcast_data_sync(*a, event_name="DataSyncProgress", **k))
    event_bus.subscribe("DataSyncComplete", lambda *a, **k: broadcast_data_sync(*a, event_name="DataSyncComplete", **k))
    event_bus.subscribe("DataDownloadProgress", lambda *a, **k: broadcast_data_sync(*a, event_name="DataDownloadProgress", **k))
    event_bus.subscribe("DataDownloadComplete", lambda *a, **k: broadcast_data_sync(*a, event_name="DataDownloadComplete", **k))
except Exception:
    pass


@router.websocket("/ws/stream")
@router.websocket("/stream")
@router.websocket("/ws")
async def global_websocket_endpoint(websocket: WebSocket, token: str | None = Query(None)):
    from app.auth.security import verify_token
    
    # Authenticate via token
    user = None
    if token:
        try:
            user = verify_token(token)
        except Exception:
            user = None
        if not user or user.get("user_id") == "anonymous":
            logger.warning("WebSocket connection rejected: invalid authentication token.")
            await websocket.close(code=1008, reason="Invalid authentication token")
            return
    
    if not user:
        logger.info("WebSocket connected without a token. Read-only public telemetry mode.")
    
    client_id = str(uuid.uuid4())
    await ws_manager.connect(websocket, client_id)
    
    # Broadcast initial live health and telemetry immediately
    try:
        await websocket.send_json({
            "event": "system_health",
            "data": {
                "status": "healthy",
                "components": {
                    "database": "ok",
                    "websocket": "ok",
                    "market_feed": "ok",
                    "ai_engine": "ok",
                    "broker_api": "ok",
                }
            }
        })
    except Exception:
        pass

    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
            except asyncio.TimeoutError:
                try:
                    await websocket.send_json({"event": "ping"})
                except Exception:
                    break
                continue
            except WebSocketDisconnect:
                break

            try:
                msg = json.loads(data)
                action = msg.get("action")
                topic = msg.get("topic")

                if action in ("symbol_changed", "publish", "inject_signal", "trigger_action") or (action not in ("ping", "subscribe", "unsubscribe") and not user):
                    if not user:
                        await websocket.send_json({"error": "Authentication required for write/publish actions", "status": 401})
                        continue

                if action == "ping":
                    await websocket.send_json({"event": "pong", "timestamp": time.time()})
                elif action == "subscribe" and topic:
                    await ws_manager.subscribe(client_id, topic)
                    await websocket.send_json({"event": "subscribed", "topic": topic})
                elif action == "unsubscribe" and topic:
                    await ws_manager.unsubscribe(client_id, topic)
                    await websocket.send_json({"event": "unsubscribed", "topic": topic})
                elif action == "symbol_changed" and topic:
                    await event_bus.publish("SymbolChanged", {"symbol": topic})
                    await websocket.send_json({"event": "symbol_changed_ack", "symbol": topic})
            except json.JSONDecodeError:
                try:
                    await websocket.send_json({"error": "Invalid JSON payload"})
                except Exception:
                    break
            except Exception as e:
                logger.warning(f"WS error processing message from {client_id}: {e}")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WS connection error {client_id}: {e}")
    finally:
        ws_manager.disconnect(client_id)