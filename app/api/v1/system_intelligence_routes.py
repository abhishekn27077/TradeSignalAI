from fastapi import APIRouter, Query, HTTPException, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.market_data.health_service import MarketDataHealthService
from app.market_data.quality.models import DataQualityState
from app.market_data.providers.consensus import ProviderConsensusEngine
from app.strategies.Ensemble.models import StrategyFamily, StrategyVote
from app.strategies.Ensemble.ensemble_engine import StrategyEnsembleEngine
from app.strategies.SignalQuality.engine import SignalQualityEngine
from app.portfolio.currency_exposure_engine import CurrencyExposureEngine
from app.portfolio.risk_budget_engine import RiskBudgetEngine
from app.execution.simulator import ExecutionSimulator, SimulatedOrder, OrderSide, OrderType, ExecutionMode
from app.analytics.calibration_engine import ConfidenceCalibrationEngine

router = APIRouter(prefix="/system-intelligence", tags=["Phase 52 System Intelligence & Quantitative Integrity"])


# Request Schemas
class StrategyVoteRequest(BaseModel):
    family: str
    direction: str  # BUY, SELL, NEUTRAL
    confidence: float
    quality: float
    regime_suitability: float
    evidence: List[str] = []


class EnsembleEvalRequest(BaseModel):
    regime: str = "STRONG_TREND"
    votes: List[StrategyVoteRequest]


class SignalQualityRequest(BaseModel):
    asset: str = "EURUSD"
    direction: str = "BUY"
    entry_price: float
    stop_loss: float
    take_profit: float
    confluence_score: float
    data_quality_state: str = "DATA_QUALITY_GOOD"
    htf_aligned: bool = True
    is_event_risk: bool = False
    current_spread_pips: float = 1.5


class ExecutionSimRequest(BaseModel):
    asset: str = "EURUSD"
    side: str = "BUY"
    order_type: str = "MARKET"
    requested_price: float
    stop_loss: float
    take_profit: float
    requested_lots: float = 1.0
    mode: str = "PAPER"


# 1. Market Data Health
@router.get("/market-data-health")
async def get_market_data_health():
    health_svc = MarketDataHealthService.get_instance()
    return health_svc.get_system_health()


# 2. Portfolio Exposure
@router.get("/portfolio-exposure")
async def get_portfolio_exposure():
    engine = CurrencyExposureEngine(max_single_currency_lots=3.0)
    # Default active portfolio demonstration
    mock_positions = [
        {"asset": "EURUSD", "direction": "BUY", "lots": 1.0},
        {"asset": "GBPUSD", "direction": "BUY", "lots": 0.5},
        {"asset": "USDJPY", "direction": "BUY", "lots": 0.5},
    ]
    report = engine.evaluate_exposure(mock_positions)
    return report.to_dict()


# 3. Strategy Ensemble Evaluation
@router.post("/ensemble/evaluate")
async def evaluate_ensemble(req: EnsembleEvalRequest):
    engine = StrategyEnsembleEngine()
    votes = [
        StrategyVote(
            family=StrategyFamily(v.family) if v.family in StrategyFamily.__members__ else StrategyFamily.MARKET_STRUCTURE,
            direction=v.direction,
            confidence=v.confidence,
            quality=v.quality,
            regime_suitability=v.regime_suitability,
            evidence=v.evidence
        )
        for v in req.votes
    ]
    decision = engine.evaluate_ensemble(votes, regime=req.regime)
    return decision.to_dict()


# 4. Signal Quality & NO-TRADE Gating
@router.post("/signal-quality/evaluate")
async def evaluate_signal_quality(req: SignalQualityRequest):
    engine = SignalQualityEngine()
    dq_state = DataQualityState(req.data_quality_state) if req.data_quality_state in DataQualityState.__members__ else DataQualityState.DATA_QUALITY_GOOD

    eval_result = engine.evaluate_signal_quality(
        asset=req.asset,
        direction=req.direction,
        entry_price=req.entry_price,
        stop_loss=req.stop_loss,
        take_profit=req.take_profit,
        confluence_score=req.confluence_score,
        data_quality_state=dq_state,
        htf_aligned=req.htf_aligned,
        is_event_risk=req.is_event_risk,
        current_spread_pips=req.current_spread_pips
    )
    return eval_result.to_dict()


# 5. Execution Simulator
@router.post("/execution/simulate")
async def simulate_execution(req: ExecutionSimRequest):
    sim = ExecutionSimulator(mode=ExecutionMode(req.mode) if req.mode in ExecutionMode.__members__ else ExecutionMode.PAPER)
    order = SimulatedOrder(
        order_id="ord_demo_01",
        asset=req.asset,
        side=OrderSide.BUY if req.side.upper() == "BUY" else OrderSide.SELL,
        order_type=OrderType.MARKET if req.order_type.upper() == "MARKET" else OrderType.LIMIT,
        requested_price=req.requested_price,
        stop_loss=req.stop_loss,
        take_profit=req.take_profit,
        requested_lots=req.requested_lots,
        mode=sim.mode
    )
    fill = sim.simulate_execution(order, current_market_price=req.requested_price)
    return fill.to_dict()
