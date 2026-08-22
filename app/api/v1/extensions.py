
from fastapi import APIRouter

from app.agents.learning.learning_engine import ai_learning_engine
from app.risk.advanced_risk_manager import advanced_risk_manager
from app.strategies.indicators.regime import market_regime_engine

router = APIRouter(prefix="/extensions", tags=["extensions"])

@router.get("/regime")
async def get_market_regime():
    """
    Returns current market regime status (Mocked for API structure)
    """
    import numpy as np
    import pandas as pd
    
    # Mock some data for the API response
    dates = pd.date_range("2026-01-01", periods=100)
    closes = np.linspace(100, 200, 100)
    df = pd.DataFrame({"high": closes+2, "low": closes-2, "close": closes}, index=dates)
    
    regime = market_regime_engine.analyze(df)
    return regime

@router.get("/learning")
async def get_ai_learning_stats():
    """
    Returns current AI dynamic weights and performance stats
    """
    return ai_learning_engine.strategy_performance

@router.get("/risk")
async def get_advanced_risk():
    """
    Returns risk configurations
    """
    return {
        "max_daily_drawdown_pct": advanced_risk_manager.max_daily_drawdown_pct,
        "max_consecutive_losses": advanced_risk_manager.max_consecutive_losses,
        "max_sector_exposure_pct": advanced_risk_manager.max_sector_exposure_pct
    }
