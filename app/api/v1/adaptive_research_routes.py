"""
app/api/v1/adaptive_research_routes.py
======================================
REST API endpoints for Phase 66 Adaptive Signal Intelligence & Open-Source Quant Research.
"""

from __future__ import annotations
from fastapi import APIRouter, Query, Body, HTTPException
from typing import Dict, Any, Optional, List

from app.core.unified_research_bus import unified_research_bus, ResearchEventType
from app.agents.research_council import research_council_engine
from app.analytics.vector_research_engine import vector_research_engine
from app.analytics.research_memory_engine import research_memory_engine
from app.analytics.regime_matrix_engine import regime_matrix_engine
from app.analytics.research_benchmark_engine import research_benchmark_engine
from app.core.execution_abstraction import paper_broker_adapter

router = APIRouter(prefix="/research", tags=["Quantitative Research"])


@router.get("/runs")
def get_research_runs(limit: int = Query(50, ge=1, le=200)) -> Dict[str, Any]:
    """Returns chronological list of persistent research run cards."""
    cards = research_memory_engine.get_all_run_cards(limit=limit)
    return {
        "status": "success",
        "data": {
            "total_runs": len(cards),
            "runs": cards,
        }
    }


@router.post("/sweep")
def trigger_vector_parameter_sweep(payload: Optional[Dict[str, Any]] = Body(None)) -> Dict[str, Any]:
    """Executes fast vectorized parameter sweep with walk-forward purge and embargo windows."""
    p = payload or {}
    asset = p.get("asset", "EURUSD")
    timeframe = p.get("timeframe", "1H")
    purge_bars = p.get("purge_bars", 5)
    embargo_bars = p.get("embargo_bars", 10)

    report = vector_research_engine.run_parameter_sweep(
        asset=asset,
        timeframe=timeframe,
        purge_bars=purge_bars,
        embargo_bars=embargo_bars,
    )

    unified_research_bus.emit(
        event_type=ResearchEventType.RESEARCH_RUN_COMPLETED,
        asset=asset,
        timeframe=timeframe,
        payload={"sweep_id": report.sweep_id, "combinations": report.total_combinations_evaluated},
    )

    return {
        "status": "success",
        "data": report.to_dict(),
    }


@router.get("/council/{asset}/{timeframe}")
def get_research_council_synthesis(
    asset: str,
    timeframe: str,
    price: float = Query(1.0850, gt=0),
    event_risk: str = Query("LOW"),
) -> Dict[str, Any]:
    """Returns 11-perspective Research Council debate and quantitative fusion."""
    synthesis = research_council_engine.evaluate_council(
        asset=asset.upper(),
        timeframe=timeframe,
        current_price=price,
        event_risk=event_risk,
    )
    return {
        "status": "success",
        "data": synthesis.to_dict(),
    }


@router.get("/regime-matrix")
def get_regime_matrix(asset: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Returns 8-regime conditional performance matrix and edge classification."""
    matrix_data = regime_matrix_engine.compute_regime_matrix(asset=asset)
    return {
        "status": "success",
        "data": matrix_data,
    }


@router.get("/benchmarks")
def get_research_benchmarks(
    asset: str = Query("EURUSD"),
    timeframe: str = Query("1H"),
) -> Dict[str, Any]:
    """Returns fair comparative benchmarks under identical out-of-sample data and friction."""
    bench_data = research_benchmark_engine.evaluate_all_benchmarks(asset=asset, timeframe=timeframe)
    return {
        "status": "success",
        "data": bench_data,
    }


@router.get("/events")
def get_research_events(
    event_type: Optional[str] = Query(None),
    asset: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
) -> Dict[str, Any]:
    """Queries immutable research bus event telemetry."""
    events = unified_research_bus.get_events(event_type=event_type, asset=asset, limit=limit)
    return {
        "status": "success",
        "data": {
            "total_events": len(events),
            "events": events,
        }
    }


@router.get("/portfolio-state")
def get_paper_portfolio_state() -> Dict[str, Any]:
    """Returns paper simulation broker portfolio state."""
    return {
        "status": "success",
        "data": paper_broker_adapter.get_portfolio_state(),
    }


@router.get("/prospective-learning")
def get_prospective_learning_dataset() -> Dict[str, Any]:
    """Returns isolated training/research dataset containing strictly fully resolved signals."""
    from app.analytics.prospective_learning_ledger import prospective_learning_ledger
    ds = prospective_learning_ledger.extract_resolved_dataset()
    return {
        "status": "success",
        "data": ds,
    }

