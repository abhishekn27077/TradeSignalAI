from typing import Any

from fastapi import APIRouter, HTTPException

from app.logs.logger import get_logger
from app.qualification import qualification_manager, reporter

logger = get_logger(__name__)
router = APIRouter(prefix="/qualification", tags=["qualification"])

@router.post("/start")
async def start_qualification(payload: dict[str, Any]):
    mode = payload.get("mode")
    config = payload.get("config", {})
    if mode not in ["synthetic", "historical", "live"]:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    await qualification_manager.start_mode(mode, config)
    return {"success": True, "message": f"Qualification mode {mode} started"}

@router.post("/stop")
async def stop_qualification():
    await qualification_manager.stop()
    return {"success": True, "message": "Qualification mode stopped"}

@router.get("/status")
async def get_status():
    return qualification_manager.get_status()

@router.get("/report")
async def get_report():
    if qualification_manager.is_running:
        return {"success": False, "message": "Qualification is still running"}
    report = reporter.generate_report()
    return {"success": True, "report": report}
