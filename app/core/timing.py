import math
from datetime import datetime, timedelta, timezone

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo


class ISTConverter:
    """Converts UTC to Asia/Kolkata (IST)."""
    IST_TZ = zoneinfo.ZoneInfo("Asia/Kolkata")

    @classmethod
    def to_ist(cls, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(cls.IST_TZ)

    @classmethod
    def to_ist_string(cls, dt: datetime) -> str:
        return cls.to_ist(dt).strftime("%Y-%m-%d %H:%M:%S IST")


class CandleClock:
    """Calculates canonical candle boundaries and countdowns."""
    
    # Mapping timeframe string to minutes
    TF_MAP = {
        "M1": 1, "1M": 1,
        "M5": 5, "5M": 5,
        "M15": 15, "15M": 15,
        "M30": 30, "30M": 30,
        "H1": 60, "1H": 60,
        "H4": 240, "4H": 240,
        "D1": 1440, "1D": 1440,
        "W1": 10080, "1W": 10080
    }

    @classmethod
    def get_candle_status(cls, timeframe: str, reference_time: datetime = None) -> dict:
        """
        Returns exact UTC and IST boundaries for the current candle.
        """
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)
            
        if reference_time.tzinfo is None:
            reference_time = reference_time.replace(tzinfo=timezone.utc)
            
        minutes = cls.TF_MAP.get(timeframe.upper())
        if not minutes:
            raise ValueError(f"Unsupported timeframe: {timeframe}")

        # Base anchoring at Unix epoch
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        
        # W1 starts on Monday 00:00 UTC (Unix epoch was Thursday)
        # So we adjust by 3 days for weekly.
        delta_seconds = int((reference_time - epoch).total_seconds())
        
        if minutes == 10080:  # Weekly
            offset_seconds = 3 * 24 * 3600 # Adjust to Monday
            current_period_start = delta_seconds - ((delta_seconds - offset_seconds) % (minutes * 60))
        else:
            current_period_start = delta_seconds - (delta_seconds % (minutes * 60))
            
        current_candle_open = epoch + timedelta(seconds=current_period_start)
        current_candle_close = current_candle_open + timedelta(minutes=minutes)
        next_candle_open = current_candle_close
        
        remaining_seconds = int((current_candle_close - reference_time).total_seconds())
        remaining_hours = remaining_seconds // 3600
        remaining_minutes = (remaining_seconds % 3600) // 60
        remaining_sec = remaining_seconds % 60
        countdown = f"{remaining_hours:02d}:{remaining_minutes:02d}:{remaining_sec:02d}"

        return {
            "timeframe": timeframe,
            "reference_time_utc": reference_time.isoformat(),
            "reference_time_ist": ISTConverter.to_ist_string(reference_time),
            
            "current_candle_open_utc": current_candle_open.isoformat(),
            "current_candle_open_ist": ISTConverter.to_ist_string(current_candle_open),
            
            "current_candle_close_utc": current_candle_close.isoformat(),
            "current_candle_close_ist": ISTConverter.to_ist_string(current_candle_close),
            
            "next_candle_open_utc": next_candle_open.isoformat(),
            "next_candle_open_ist": ISTConverter.to_ist_string(next_candle_open),
            
            "remaining_seconds": remaining_seconds,
            "countdown": countdown
        }
