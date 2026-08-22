from fastapi import APIRouter
from app.analytics.ablation_tracker import ablation_tracker
import json
from pathlib import Path

router = APIRouter(prefix="/phase35", tags=["Phase 35"])

@router.get("/daily")
async def get_daily_report():
    report_path = ablation_tracker.generate_daily_report()
    if not Path(report_path).exists():
        return {"status": "error", "message": "Failed to generate report"}
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/weekly")
async def get_weekly_report():
    report_path = ablation_tracker.generate_weekly_report()
    if not Path(report_path).exists():
        return {"status": "error", "message": "Failed to generate report"}
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/final")
async def get_final_certification():
    report_path = ablation_tracker.generate_final_certification()
    if not Path(report_path).exists():
        return {"status": "error", "message": "Failed to generate report"}
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)
