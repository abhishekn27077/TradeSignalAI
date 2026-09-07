from typing import Any, Optional, Dict, Tuple
from datetime import datetime, timezone, timedelta
try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

class MarketClockService:
    """
    Authoritative Market Clock Service for Phase 49.
    Provides strict UTC-to-IST conversion, precise formatting, and staleness validation.
    """
    IST_TZ = zoneinfo.ZoneInfo("Asia/Kolkata")

    @classmethod
    def get_current_utc(cls) -> datetime:
        """Returns the current UTC time, tz-aware."""
        return datetime.now(timezone.utc)

    @classmethod
    def get_current_ist(cls) -> datetime:
        """Returns the current IST time, tz-aware."""
        return cls.get_current_utc().astimezone(cls.IST_TZ)

    @classmethod
    def to_ist(cls, dt: datetime) -> datetime:
        """Converts any datetime to IST."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(cls.IST_TZ)

    @classmethod
    def format_ist(cls, dt: datetime) -> str:
        """
        Formats datetime into strict IST format: 
        e.g., 'Friday, 21 August 2026 06:00 PM IST'
        """
        ist_dt = cls.to_ist(dt)
        # Note: Windows might space pad %d. Stripping leading zeros if needed: 
        return ist_dt.strftime("%A, %d %B %Y %I:%M %p IST")

    @classmethod
    def is_data_stale(cls, latest_candle_time: datetime, max_age_seconds: int = 3600) -> bool:
        """
        Validates if the provided market data is stale based on the current UTC time.
        """
        if latest_candle_time.tzinfo is None:
            latest_candle_time = latest_candle_time.replace(tzinfo=timezone.utc)
        
        age = (cls.get_current_utc() - latest_candle_time).total_seconds()
        return age > max_age_seconds

    @classmethod
    def get_ist_day_bounds_utc(cls, days_ago: int = 0) -> tuple[datetime, datetime]:
        """
        Returns the UTC start and end bounds for an IST calendar day.
        """
        now_ist = cls.get_current_ist()
        target_day_ist = (now_ist - timedelta(days=days_ago)).replace(hour=0, minute=0, second=0, microsecond=0)
        next_day_ist = target_day_ist + timedelta(days=1)

        start_utc = target_day_ist.astimezone(timezone.utc)
        end_utc = next_day_ist.astimezone(timezone.utc)
        return start_utc, end_utc

    @classmethod
    def is_target_time_expired(cls, target_time_utc: datetime) -> bool:
        """
        Returns True if the target execution/forecast time has already passed.
        A signal is CURRENT only if: target_time_utc > current_time_utc.
        """
        if target_time_utc.tzinfo is None:
            target_time_utc = target_time_utc.replace(tzinfo=timezone.utc)
        return cls.get_current_utc() >= target_time_utc

    @classmethod
    def compute_entry_window(
        cls,
        target_utc: datetime,
        timeframe: str = "1H",
        atr: float = 0.0,
        volatility_pct: float = 1.0,
    ) -> dict[str, Any]:
        """
        Dynamically computes the entry timing envelope for an actionable trade setup.
        Windows are calculated based on timeframe and volatility, NOT hardcoded fixed constants.
        """
        if target_utc.tzinfo is None:
            target_utc = target_utc.replace(tzinfo=timezone.utc)

        tf_upper = timeframe.upper()
        if "15M" in tf_upper:
            base_lead_mins = 5
            base_lag_mins = 5
            preferred_offset_mins = -2
        elif "30M" in tf_upper:
            base_lead_mins = 10
            base_lag_mins = 10
            preferred_offset_mins = -3
        elif "1H" in tf_upper or "H1" in tf_upper:
            base_lead_mins = 15
            base_lag_mins = 15
            preferred_offset_mins = -5
        elif "4H" in tf_upper or "H4" in tf_upper:
            base_lead_mins = 30
            base_lag_mins = 30
            preferred_offset_mins = -10
        elif "1D" in tf_upper or "D1" in tf_upper or "DAILY" in tf_upper:
            base_lead_mins = 60
            base_lag_mins = 60
            preferred_offset_mins = -15
        else:
            base_lead_mins = 15
            base_lag_mins = 15
            preferred_offset_mins = -5

        # Scale window dynamically with volatility if available (volatility multiplier between 0.8 and 1.5)
        vol_multiplier = max(0.8, min(1.5, volatility_pct if volatility_pct > 0 else 1.0))
        lead_mins = int(base_lead_mins * vol_multiplier)
        lag_mins = int(base_lag_mins * vol_multiplier)

        window_start_utc = target_utc - timedelta(minutes=lead_mins)
        preferred_entry_utc = target_utc + timedelta(minutes=preferred_offset_mins)
        window_end_utc = target_utc + timedelta(minutes=lag_mins)
        expiry_utc = window_end_utc

        return {
            "target_time_utc": target_utc,
            "target_time_ist": cls.format_ist(target_utc),
            "entry_window_start_utc": window_start_utc,
            "entry_window_start_ist": cls.format_ist(window_start_utc),
            "preferred_entry_time_utc": preferred_entry_utc,
            "preferred_entry_time_ist": cls.format_ist(preferred_entry_utc),
            "entry_window_end_utc": window_end_utc,
            "entry_window_end_ist": cls.format_ist(window_end_utc),
            "signal_expiry_time_utc": expiry_utc,
            "signal_expiry_time_ist": cls.format_ist(expiry_utc),
            "lead_minutes": lead_mins,
            "lag_minutes": lag_mins,
        }

    @classmethod
    def compute_holding_window(
        cls,
        timeframe: str = "1H",
        atr: float = 0.0,
        strategy_type: str = "INTRADAY",
    ) -> dict[str, Any]:
        """
        Dynamically computes the expected and maximum holding periods.
        """
        tf_upper = timeframe.upper()
        if "15M" in tf_upper or "30M" in tf_upper:
            expected_min_hours = 0.5
            expected_max_hours = 2.0
            maximum_hold_hours = 3.5
        elif "1H" in tf_upper or "H1" in tf_upper:
            expected_min_hours = 2.0
            expected_max_hours = 4.0
            maximum_hold_hours = 6.0
        elif "4H" in tf_upper or "H4" in tf_upper:
            expected_min_hours = 8.0
            expected_max_hours = 24.0
            maximum_hold_hours = 48.0
        elif "1D" in tf_upper or "D1" in tf_upper:
            expected_min_hours = 24.0
            expected_max_hours = 72.0
            maximum_hold_hours = 120.0
        else:
            expected_min_hours = 2.0
            expected_max_hours = 4.0
            maximum_hold_hours = 6.0

        if strategy_type.upper() == "SWING":
            expected_min_hours = max(expected_min_hours, 12.0)
            expected_max_hours = max(expected_max_hours, 36.0)
            maximum_hold_hours = max(maximum_hold_hours, 72.0)

        return {
            "expected_hold_min_hours": expected_min_hours,
            "expected_hold_max_hours": expected_max_hours,
            "maximum_hold_hours": maximum_hold_hours,
            "holding_description": f"{expected_min_hours:.0f}–{expected_max_hours:.0f} hours (Max: {maximum_hold_hours:.0f}h)",
        }

    @classmethod
    def compute_countdown(cls, target_utc: datetime, current_utc: datetime | None = None) -> dict[str, Any]:
        """
        Calculates exact authoritative countdown in seconds and formatted string (HH:MM:SS).
        """
        if target_utc.tzinfo is None:
            target_utc = target_utc.replace(tzinfo=timezone.utc)
        now = current_utc or cls.get_current_utc()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        delta_seconds = (target_utc - now).total_seconds()
        is_passed = delta_seconds <= 0

        abs_sec = int(abs(delta_seconds))
        hours, remainder = divmod(abs_sec, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        return {
            "seconds_remaining": max(0.0, delta_seconds),
            "is_passed": is_passed,
            "countdown_formatted": formatted_str,
            "direction_label": "ago" if is_passed else "remaining",
        }

    @classmethod
    def get_market_session(cls, asset: str = "EURUSD", dt_utc: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Determines the current market session, session overlaps, and market open/close status.
        """
        now = dt_utc or cls.get_current_utc()
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        weekday = now.weekday()  # 0=Monday, 4=Friday, 5=Saturday, 6=Sunday
        hour = now.hour
        is_crypto = "BTC" in asset or "ETH" in asset

        # Weekend Check (Forex / Indices close Friday 21:00 UTC to Sunday 21:00 UTC)
        is_weekend = False
        if not is_crypto:
            if weekday == 4 and hour >= 21:
                is_weekend = True
            elif weekday == 5:
                is_weekend = True
            elif weekday == 6 and hour < 21:
                is_weekend = True

        # Major Global Sessions (UTC)
        # Sydney: 21:00 - 06:00 UTC
        # Tokyo: 00:00 - 09:00 UTC
        # London: 07:00 - 16:00 UTC
        # New York: 12:00 - 21:00 UTC
        active_sessions = []
        if hour >= 21 or hour < 6:
            active_sessions.append("SYDNEY")
        if 0 <= hour < 9:
            active_sessions.append("TOKYO")
        if 7 <= hour < 16:
            active_sessions.append("LONDON")
        if 12 <= hour < 21:
            active_sessions.append("NEW_YORK")

        is_london_ny_overlap = ("LONDON" in active_sessions) and ("NEW_YORK" in active_sessions)
        is_market_open = is_crypto or (not is_weekend)

        return {
            "asset": asset,
            "is_crypto": is_crypto,
            "is_market_open": is_market_open,
            "is_weekend": is_weekend,
            "active_sessions": active_sessions,
            "is_london_ny_overlap": is_london_ny_overlap,
            "current_utc": now.isoformat(),
            "current_ist": cls.to_ist(now).isoformat(),
        }

    @classmethod
    def validate_candle_timestamp(
        cls,
        candle_ts: datetime,
        wall_clock_ts: Optional[datetime] = None,
        max_drift_seconds: int = 120,
        max_staleness_seconds: int = 7200
    ) -> Dict[str, Any]:
        """
        Validates candle timestamp integrity:
        - Future timestamp detection (FAIL CLOSED)
        - Clock drift detection
        - Stale feed detection
        """
        now = wall_clock_ts or cls.get_current_utc()
        if candle_ts.tzinfo is None:
            candle_ts = candle_ts.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        diff_seconds = (candle_ts - now).total_seconds()
        
        # 1. Future timestamp check
        is_future = diff_seconds > max_drift_seconds

        # 2. Staleness check
        age_seconds = (now - candle_ts).total_seconds()
        is_stale = age_seconds > max_staleness_seconds

        status = "VALID"
        if is_future:
            status = "FUTURE_TIMESTAMP_VIOLATION"
        elif is_stale:
            status = "STALE_DATA_WARNING"

        return {
            "status": status,
            "candle_timestamp_utc": candle_ts.isoformat(),
            "wall_clock_timestamp_utc": now.isoformat(),
            "diff_seconds": round(diff_seconds, 2),
            "age_seconds": round(age_seconds, 2),
            "is_future": is_future,
            "is_stale": is_stale,
            "is_valid": not is_future,
        }


# Canonical Alias
MarketClock = MarketClockService
market_clock = MarketClockService()
