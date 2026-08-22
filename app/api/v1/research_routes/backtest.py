
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class BacktestRequest(BaseModel):
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    strategy: str
    capital: float = 10000.0

@router.post("/run", summary="Run Enterprise Backtest")
async def run_backtest(req: BacktestRequest):
    # Stub: Delegate to EnterpriseBacktestEngine
    from app.backtesting.enterprise_engine import EnterpriseBacktestEngine
    engine = EnterpriseBacktestEngine()
    result = engine.run_backtest(
        symbol=req.symbol,
        timeframe=req.timeframe,
        start_date=req.start_date,
        end_date=req.end_date,
        strategy_or_model=req.strategy
    )
    return {"success": True, "data": result}
