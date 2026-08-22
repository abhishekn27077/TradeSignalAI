from typing import Any

from fastapi import APIRouter

from app.portfolio_intelligence.ai_insights import ai_insights_generator
from app.portfolio_intelligence.capital_allocation import capital_allocation_engine
from app.portfolio_intelligence.correlation import correlation_engine
from app.portfolio_intelligence.currency_strength import currency_strength_engine
from app.portfolio_intelligence.exposure_monitor import exposure_monitor
from app.portfolio_intelligence.market_rotation import market_rotation_engine
from app.portfolio_intelligence.portfolio_manager import ai_portfolio_manager
from app.portfolio_intelligence.research_analytics import research_analytics

router = APIRouter()

@router.get("/currency-strength", response_model=dict[str, Any])
async def get_currency_strength():
    return currency_strength_engine.calculate()

@router.get("/correlation", response_model=dict[str, Any])
async def get_correlation():
    return correlation_engine.calculate()

@router.get("/exposure", response_model=dict[str, Any])
async def get_exposure():
    # Stub active trades for now
    active_trades = [{"symbol": "EURUSD", "risk": 1.0}, {"symbol": "GBPUSD", "risk": 1.0}]
    return exposure_monitor.evaluate(active_trades)

@router.get("/allocation", response_model=dict[str, Any])
async def get_allocation():
    # Stub total capital and opportunities
    return capital_allocation_engine.recommend_allocation(100000.0, 2.0, 5)

@router.get("/market-rotation", response_model=dict[str, Any])
async def get_market_rotation():
    return market_rotation_engine.analyze()

@router.get("/portfolio", response_model=dict[str, Any])
async def get_portfolio():
    # Stub opportunities
    opportunities = [{"symbol": "BTCUSD", "score": 95}, {"symbol": "ETHUSD", "score": 92}]
    return ai_portfolio_manager.rank_opportunities(opportunities)

@router.get("/insights/{session}", response_model=dict[str, str])
async def get_insights(session: str):
    return {"session": session, "insight": ai_insights_generator.generate_brief(session)}

@router.get("/analytics", response_model=dict[str, Any])
async def get_analytics():
    return research_analytics.get_accuracy_metrics()
