
from fastapi import APIRouter, Path, Query

from app.api.exceptions import provider_offline_response
from app.logs.logger import get_logger
from app.market_data.service import market_service

logger = get_logger(__name__)

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/price/{symbol:path}")
async def get_price(symbol: str = Path(..., min_length=1)):
    try:
        ticker = await market_service.get_ticker(symbol)
        if ticker is None:
            return provider_offline_response("market_data", f"No data available for {symbol}")
        return {"success": True, "symbol": symbol, "data": ticker}
    except Exception as e:
        logger.warning(f"Market price error for {symbol}: {e}")
        return provider_offline_response("market_data", str(e))


@router.get("/rates/{symbol:path}/{timeframe}")
async def get_rates(
    symbol: str = Path(..., min_length=1),
    timeframe: str = Path(...),
    count: int = Query(default=100, le=500),
):
    try:
        rates = await market_service.get_rates(symbol, timeframe, count)
        return {"success": True, "symbol": symbol, "timeframe": timeframe, "count": len(rates), "data": rates}
    except Exception as e:
        logger.warning(f"Market rates error: {e}")
        return {"success": False, "symbol": symbol, "timeframe": timeframe, "data": []}


@router.get("/ticker/{symbol:path}")
async def get_ticker(symbol: str = Path(..., min_length=1)):
    try:
        ticker = await market_service.get_ticker(symbol)
        if ticker is None:
            return provider_offline_response("market_data")
        return {"success": True, "symbol": symbol, "data": ticker}
    except Exception as e:
        logger.warning(f"Ticker error: {e}")
        return provider_offline_response("market_data", str(e))


@router.get("/candle-clock/{timeframe}")
async def get_candle_clock(timeframe: str = Path(...)):
    try:
        from app.core.timing import CandleClock
        status = CandleClock.get_candle_status(timeframe)
        return {"success": True, "data": status}
    except ValueError as ve:
        return {"success": False, "message": str(ve)}
    except Exception as e:
        logger.warning(f"CandleClock error: {e}")
        return {"success": False, "message": str(e)}


@router.get("/status", summary="Get Live Market Status for All Assets")
async def get_all_market_status():
    """
    Returns real-time open/closed status, current trading session,
    next open/close timestamps, and session reasons across all 9 assets.
    """
    try:
        from app.core.market_session import market_session_service
        statuses = market_session_service.get_all_market_statuses()
        open_count = sum(1 for s in statuses if s["is_market_open"])
        closed_count = sum(1 for s in statuses if not s["is_market_open"])
        return {
            "success": True,
            "total_assets": len(statuses),
            "open_count": open_count,
            "closed_count": closed_count,
            "statuses": statuses,
        }
    except Exception as e:
        logger.error(f"Error fetching market statuses: {e}")
        return {"success": False, "error": str(e), "statuses": []}


@router.get("/status/{symbol:path}", summary="Get Live Market Status for Specific Asset")
async def get_symbol_market_status(symbol: str = Path(..., min_length=1)):
    """Returns market open/closed status for a single symbol."""
    try:
        from app.core.market_session import market_session_service
        status = market_session_service.get_market_status(symbol)
        return {"success": True, "data": status}
    except Exception as e:
        logger.error(f"Error fetching status for {symbol}: {e}")
        return {"success": False, "error": str(e)}