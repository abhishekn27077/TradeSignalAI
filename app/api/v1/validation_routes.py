from typing import Any

from fastapi import APIRouter

from app.validation.ab_testing import ab_testing_framework
from app.validation.benchmarking import benchmarking_lab
from app.validation.calibration import confidence_calibration
from app.validation.drift import model_drift_detection
from app.validation.hold_time import hold_time_analysis
from app.validation.improvement import continuous_improvement_engine
from app.validation.pair_analysis import pair_analysis
from app.validation.regime import regime_validation
from app.validation.reports import validation_reports
from app.validation.session import session_validation
from app.validation.walk_forward import walk_forward_validation

router = APIRouter()

@router.get("/benchmark", response_model=dict[str, Any])
async def get_benchmark():
    return benchmarking_lab.compare_models()

@router.get("/ab-test", response_model=dict[str, Any])
async def get_ab_test(config_a: str = "A", config_b: str = "B"):
    return ab_testing_framework.run_test(config_a, config_b)

@router.get("/walk-forward", response_model=dict[str, Any])
async def get_walk_forward():
    return walk_forward_validation.execute_split()

@router.get("/regime", response_model=dict[str, Any])
async def get_regime():
    return regime_validation.evaluate()

@router.get("/session", response_model=dict[str, Any])
async def get_session():
    return session_validation.evaluate()

@router.get("/hold-time", response_model=dict[str, Any])
async def get_hold_time():
    return hold_time_analysis.analyze()

@router.get("/pair-analysis", response_model=list[dict[str, Any]])
async def get_pair_analysis():
    return pair_analysis.rank_symbols()

@router.get("/drift", response_model=dict[str, Any])
async def get_drift():
    return model_drift_detection.check_drift()

@router.get("/calibration", response_model=dict[str, Any])
async def get_calibration():
    return confidence_calibration.verify()

@router.get("/improvement", response_model=dict[str, Any])
async def get_improvement():
    return continuous_improvement_engine.generate_recommendations()

@router.get("/reports/{period}", response_model=dict[str, Any])
async def get_reports(period: str):
    return await validation_reports.generate(period)
