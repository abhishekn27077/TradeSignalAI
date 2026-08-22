from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ReplayRequest(BaseModel):
    start_date: str
    end_date: str
    speed: float = 1.0

@router.post("/start", summary="Start Historical Replay")
async def start_replay(req: ReplayRequest):
    from app.research.replay_engine import replay_engine
    replay_engine.start_replay(req.start_date, req.end_date, req.speed)
    return {"success": True, "message": f"Replay started at {req.speed}x"}

@router.post("/pause", summary="Pause Historical Replay")
async def pause_replay():
    from app.research.replay_engine import replay_engine
    replay_engine.pause_replay()
    return {"success": True, "message": "Replay paused"}

@router.post("/resume", summary="Resume Historical Replay")
async def resume_replay():
    from app.research.replay_engine import replay_engine
    replay_engine.resume_replay()
    return {"success": True, "message": "Replay resumed"}

@router.post("/speed", summary="Set Replay Speed")
async def set_speed(speed: float):
    from app.research.replay_engine import replay_engine
    replay_engine.set_speed(speed)
    return {"success": True, "message": f"Speed set to {speed}x"}
