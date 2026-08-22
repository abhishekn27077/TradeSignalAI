from typing import Any

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_features() -> list[dict[str, Any]]:
    """
    Returns feature importance scoring.
    """
    return [
        {"feature": "Market Regime (Trend)", "importance": 0.88},
        {"feature": "RSI", "importance": 0.65},
        {"feature": "Order Blocks", "importance": 0.72},
        {"feature": "ATR", "importance": 0.55},
        {"feature": "MACD", "importance": 0.45}
    ]
