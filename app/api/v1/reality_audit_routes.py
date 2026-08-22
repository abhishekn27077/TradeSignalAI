"""
Phase 44 — Reality Audit & Evidence Provenance REST API Routes.

Exposes endpoints for:
  - 4-Tier Dataset Separation (Historical, OOS, Live Shadow, Real Money)
  - Critical Numbers Audit (A-H verification of 11 core metrics)
  - Live Shadow Pipeline Trace Inspection
  - Database Integrity Verification
  - Sample Size & Statistical Claim Governance
"""
import json
import os
from fastapi import APIRouter, HTTPException

from app.analytics.evidence_provenance_engine import evidence_provenance_engine
from app.analytics.reality_audit_engine import reality_audit_engine
from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/validation/phase44", tags=["Phase 44 Reality & Evidence Audit"])


@router.get("/provenance", summary="Complete Evidence Provenance Summary")
async def get_provenance_summary():
    """Returns dataset tier separation, critical number audits, and claim governance status."""
    try:
        tiers = evidence_provenance_engine.get_dataset_tiers_summary()
        gov = evidence_provenance_engine.get_governance_verdict()
        return {"success": True, "dataset_tiers": tiers, "governance": gov}
    except Exception as e:
        logger.error(f"Provenance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/critical-numbers", summary="Critical Number Audit (A-H Analysis)")
async def get_critical_numbers():
    """Returns granular provenance audit for the 11 key metrics claimed in Phase 43."""
    try:
        audit_list = evidence_provenance_engine.get_critical_numbers_audit()
        return {"success": True, "total_metrics_audited": len(audit_list), "audit_records": audit_list}
    except Exception as e:
        logger.error(f"Critical numbers audit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets", summary="4-Tier Dataset Separation Matrix")
async def get_dataset_tiers():
    """Returns isolated metrics for Historical Backtest, Walk-Forward OOS, Live Shadow, and Real Money."""
    try:
        return {"success": True, **evidence_provenance_engine.get_dataset_tiers_summary()}
    except Exception as e:
        logger.error(f"Dataset tiers error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/live-trace", summary="Real-Time Shadow Pipeline Execution Trace")
async def get_live_shadow_trace():
    """Executes live shadow pipeline on real market data and returns the end-to-end trace."""
    try:
        trace_data = reality_audit_engine.execute_live_pipeline_audit()
        return {"success": True, **trace_data}
    except Exception as e:
        logger.error(f"Live trace error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database-integrity", summary="SQLite Database Integrity Audit")
async def get_database_integrity():
    """Returns verification metrics for duplicate predictions, missing hashes, and impossible timestamps."""
    try:
        integrity = reality_audit_engine.audit_database_integrity()
        return {"success": True, **integrity}
    except Exception as e:
        logger.error(f"DB integrity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/governance", summary="Statistical Claim & Sample Governance")
async def get_claim_governance():
    """Returns strict policy status on whether statistical edge or profitability claims are permitted."""
    try:
        return {"success": True, **evidence_provenance_engine.get_governance_verdict()}
    except Exception as e:
        logger.error(f"Governance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
