from datetime import datetime, timezone
from app.core.timing import CandleClock

class NextSignalEngine:
    """Calculates countdowns to the next valid evaluation window per asset and timeframe."""

    @classmethod
    def get_next_opportunity(cls, asset: str, timeframe: str) -> dict:
        try:
            status = CandleClock.get_candle_status(timeframe)
            return {
                "asset": asset,
                "timeframe": timeframe,
                "next_evaluation_utc": status["current_candle_close_utc"],
                "next_evaluation_ist": status["current_candle_close_ist"],
                "countdown": status["countdown"],
                "status": "WAITING FOR CANDLE CLOSE"
            }
        except Exception as e:
            return {
                "asset": asset,
                "timeframe": timeframe,
                "error": str(e)
            }
