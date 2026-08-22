
from fastapi import APIRouter

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/initialize", summary="Initialize AI Crew")
async def initialize_crew():
    try:
        from app.agents.manager import agent_registry, lifecycle_manager
        if not agent_registry._agents:
            lifecycle_manager.start()
        agents = []
        for agent_id, agent in agent_registry._agents.items():
            agents.append({
                "id": agent.agent_id,
                "name": agent.agent_id.replace("_001", "").title() + " Analyst",
                "role": getattr(agent.role, "value", str(agent.role)),
                "status": "waiting",
                "confidence": 0,
                "decision": "WAIT",
                "performanceScore": 95
            })
        return {"success": True, "agents": agents}
    except Exception as e:
        logger.warning(f"Agent initialize error: {e}")
        return {"success": False, "error": str(e)}

@router.get("/status", summary="Get Agent Status")
async def get_agent_status():
    try:
        from app.agents.manager import agent_registry
        agents = []
        for agent_id, agent in agent_registry._agents.items():
            agents.append({
                "id": agent.agent_id,
                "name": agent.agent_id.replace("_001", "").title() + " Analyst",
                "role": getattr(agent.role, "value", str(agent.role)),
                "status": "waiting",
                "confidence": 0,
                "decision": "WAIT",
                "performanceScore": 95
            })
        return {"success": True, "agents": agents}
    except Exception as e:
        logger.warning(f"Agent status error: {e}")
        return {"success": True, "agents": []}


@router.get("/consensus", summary="Get Current Consensus")
async def get_consensus():
    try:
        from app.agents.consensus.engine import consensus_engine
        consensus = await consensus_engine.get_current_consensus() if hasattr(consensus_engine, "get_current_consensus") else {}
        return {"success": True, "consensus": consensus}
    except Exception as e:
        logger.warning(f"Consensus error: {e}")
        return {"success": True, "consensus": {}}


@router.post("/consensus/trigger", summary="Trigger Consensus Round")
async def trigger_consensus(symbol: str = "EURUSD"):
    try:
        from app.agents.consensus.engine import consensus_engine
        if hasattr(consensus_engine, "run_consensus"):
            result = await consensus_engine.run_consensus(symbol)
            return {"success": True, "result": result}
        return {"success": True, "result": {"status": "not_available"}}
    except Exception as e:
        logger.warning(f"Consensus trigger error: {e}")
        return {"success": True, "result": {"status": "failed", "error": str(e)}}


@router.get("/health", summary="Get AI Engine Health")
async def ai_health():
    try:
        from app.agents.providers.router import model_router
        health = await model_router.health_check_all()
        return {"success": True, "providers": health}
    except Exception as e:
        logger.warning(f"AI health error: {e}")
        return {"success": True, "providers": {}}
