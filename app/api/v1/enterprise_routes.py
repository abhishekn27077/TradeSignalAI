from typing import Any

from fastapi import APIRouter, Depends

from app.auth.security import verify_role
from app.core.config_manager import config_manager
from app.operations.audit import audit_trail
from app.operations.backup import backup_manager
from app.operations.health import system_health
from app.orchestration.scheduler import task_scheduler
from app.plugins.loader import plugin_loader

router = APIRouter()

@router.get("/health", response_model=dict[str, Any])
async def get_health():
    return system_health.get_status()

@router.get("/audit", response_model=list, dependencies=[Depends(verify_role("admin"))])
async def get_audit_logs():
    return audit_trail.get_logs()

@router.post("/backup", response_model=dict[str, Any], dependencies=[Depends(verify_role("admin"))])
async def trigger_backup():
    return backup_manager.trigger_backup()

@router.get("/plugins", response_model=dict[str, Any])
async def get_plugins():
    return plugin_loader.get_status()

@router.get("/tasks", response_model=dict[str, Any])
async def get_tasks():
    return task_scheduler.get_status()

@router.get("/config", response_model=dict[str, Any])
async def get_config():
    return config_manager.get_all()
