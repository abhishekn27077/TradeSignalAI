import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, time

from app.core.market_clock import MarketClockService


class SessionName(str, Enum):
    ASIA = "ASIA"
    LONDON = "LONDON"
    NEW_YORK_AM = "NEW_YORK_AM"
    NEW_YORK_PM = "NEW_YORK_PM"
    OFF_HOURS = "OFF_HOURS"


@dataclass
class SessionProfile:
    session_name: SessionName
    is_active: bool
    is_killzone: bool
    session_start_utc: str
    session_end_utc: str
    session_high: float
    session_low: float
    session_range: float
    session_volatility: float
    asian_high_swept: bool = False
    asian_low_swept: bool = False
    timestamp_utc: str = ""
    timestamp_ist: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_name": self.session_name.value if hasattr(self.session_name, 'value') else str(self.session_name),
            "is_active": self.is_active,
            "is_killzone": self.is_killzone,
            "session_start_utc": self.session_start_utc,
            "session_end_utc": self.session_end_utc,
            "session_high": float(self.session_high),
            "session_low": float(self.session_low),
            "session_range": float(self.session_range),
            "session_volatility": float(self.session_volatility),
            "asian_high_swept": self.asian_high_swept,
            "asian_low_swept": self.asian_low_swept,
            "timestamp_utc": self.timestamp_utc,
            "timestamp_ist": self.timestamp_ist,
            "details": self.details,
        }


class SessionEngine:
    """
    ICT Killzones and Multi-Session Profiler.
    Uses MarketClockService for timezone-aware calculations.
    Tracks session highs, lows, ranges, volatility, and Asian range sweeps.
    """

    # UTC Killzone definition windows
    SESSION_WINDOWS = {
        SessionName.ASIA: (time(0, 0), time(8, 0), False),
        SessionName.LONDON: (time(7, 0), time(10, 0), True),      # London Open Killzone
        SessionName.NEW_YORK_AM: (time(12, 0), time(15, 0), True), # NY AM Killzone
        SessionName.NEW_YORK_PM: (time(18, 0), time(20, 0), True), # NY PM Killzone
    }

    def __init__(self):
        pass

    def evaluate_session(self, df: Optional[pd.DataFrame] = None, current_time: Optional[datetime] = None) -> SessionProfile:
        now_utc = current_time or MarketClockService.get_current_utc()
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)
        now_ist_str = MarketClockService.format_ist(now_utc)

        curr_time = now_utc.time()

        # Identify active session
        active_session = SessionName.OFF_HOURS
        is_killzone = False
        start_str = "00:00 UTC"
        end_str = "00:00 UTC"

        for s_name, (s_start, s_end, is_kz) in self.SESSION_WINDOWS.items():
            if s_start <= curr_time <= s_end:
                active_session = s_name
                is_killzone = is_kz
                start_str = s_start.strftime("%H:%M UTC")
                end_str = s_end.strftime("%H:%M UTC")
                break

        # Compute price metrics if DataFrame provided
        session_high = 0.0
        session_low = 0.0
        session_range = 0.0
        session_vol = 0.0
        asian_high_swept = False
        asian_low_swept = False

        if df is not None and len(df) > 0:
            ts_col = 'timestamp' if 'timestamp' in df.columns else ('date' if 'date' in df.columns else None)
            if ts_col:
                try:
                    temp_df = df.copy()
                    temp_df['dt'] = pd.to_datetime(temp_df[ts_col], utc=True)
                    today_utc = now_utc.date()
                    today_candles = temp_df[temp_df['dt'].dt.date == today_utc]

                    if len(today_candles) > 0:
                        session_high = float(today_candles['high'].max())
                        session_low = float(today_candles['low'].min())
                        session_range = session_high - session_low
                        session_vol = float(today_candles['high'].std()) if len(today_candles) > 1 else 0.0

                    # Asian Range Reference (00:00 - 08:00 UTC today)
                    asian_candles = temp_df[(temp_df['dt'].dt.date == today_utc) & (temp_df['dt'].dt.hour < 8)]
                    if len(asian_candles) > 0:
                        asian_high = float(asian_candles['high'].max())
                        asian_low = float(asian_candles['low'].min())

                        # Check if later candles swept Asian extremes
                        later_candles = temp_df[(temp_df['dt'].dt.date == today_utc) & (temp_df['dt'].dt.hour >= 8)]
                        if len(later_candles) > 0:
                            if later_candles['high'].max() > asian_high:
                                asian_high_swept = True
                            if later_candles['low'].min() < asian_low:
                                asian_low_swept = True
                except Exception:
                    pass

        return SessionProfile(
            session_name=active_session,
            is_active=(active_session != SessionName.OFF_HOURS),
            is_killzone=is_killzone,
            session_start_utc=start_str,
            session_end_utc=end_str,
            session_high=session_high,
            session_low=session_low,
            session_range=session_range,
            session_volatility=session_vol,
            asian_high_swept=asian_high_swept,
            asian_low_swept=asian_low_swept,
            timestamp_utc=now_utc.isoformat(),
            timestamp_ist=now_ist_str
        )
