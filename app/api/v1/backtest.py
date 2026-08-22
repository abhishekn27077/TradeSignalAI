
from fastapi import APIRouter, Body

from app.logs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("/run", summary="Run Backtest")
async def run_backtest(
    symbol: str = Body(default="EURUSD"),
    timeframe: str = Body(default="1h"),
    strategy: str = Body(default=""),
    capital: float = Body(default=10000.0),
):
    try:
        from app.backtesting.core import BacktestEngine
        engine = BacktestEngine()
        result = await engine.run(symbol=symbol, timeframe=timeframe, strategy_name=strategy, capital=capital)
        return {"success": True, "result": result}
    except Exception as e:
        logger.warning(f"Backtest error: {e}")
        return {"success": False, "message": str(e), "result": {}}


@router.get("/history", summary="Get Backtest History")
async def get_backtest_history(limit: int = 20):
    try:
        from app.backtesting.core import BacktestEngine
        engine = BacktestEngine()
        history = engine.get_history() if hasattr(engine, "get_history") else []
        return {"success": True, "history": history[:limit]}
    except Exception as e:
        logger.warning(f"Backtest history error: {e}")
        return {"success": True, "history": []}