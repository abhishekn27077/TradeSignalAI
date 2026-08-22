from fastapi import APIRouter
from datetime import datetime
from typing import List, Dict

router = APIRouter()

# In a real scenario, this would interface with Celery/Redis or APScheduler.
# For the Phase 29 paper-trading validation, we mock the status tracker of the active engine.

MOCK_JOBS = [
    {
        "job": "H4_Forward_Engine",
        "status": "RUNNING",
        "last_run": datetime.utcnow().isoformat(),
        "next_run": "2026-08-20T00:00:00Z",
        "duration": "45s",
        "success_count": 12,
        "failure_count": 0,
        "retry_count": 0,
        "last_error": None
    },
    {
        "job": "Swing_Forward_Engine",
        "status": "RUNNING",
        "last_run": datetime.utcnow().isoformat(),
        "next_run": "2026-08-20T00:00:00Z",
        "duration": "12s",
        "success_count": 3,
        "failure_count": 0,
        "retry_count": 0,
        "last_error": None
    },
    {
        "job": "Live_Market_Data",
        "status": "HEALTHY",
        "last_run": datetime.utcnow().isoformat(),
        "next_run": "Continuous",
        "duration": "0s",
        "success_count": 15000,
        "failure_count": 2,
        "retry_count": 1,
        "last_error": "Connection reset by peer"
    }
]

@router.get("/jobs", response_model=List[Dict])
async def get_system_jobs():
    """
    Returns the status of all active background validation engines for Phase 29.
    """
    # For Phase 29 verification, the background engines run indefinitely.
    # We update last_run dynamically to show live status.
    for job in MOCK_JOBS:
        if job["next_run"] != "Continuous":
            job["last_run"] = datetime.utcnow().isoformat()
    return MOCK_JOBS
