"""
app/core/market_session.py
==========================
Authoritative Market Session & Asset Trading Calendar Service.

Manages market open/closed state, session windows, weekend gating, and next-open/next-close calculations
for all 9 core assets:
  - Crypto (BTCUSD, ETHUSD): 24/7 continuous trading.
  - Forex (EURUSD, GBPUSD, USDJPY, AUDUSD): Sun 22:00 UTC to Fri 21:00 UTC (Closed weekends).
  - Metals (XAUUSD): Mon-Fri 00:00–21:00 UTC (Daily break 21:00–22:00 UTC, Closed weekends).
  - Indices (NAS100, SPX500): Mon-Fri 22:00–21:00 UTC (Closed weekends).

Absolute Invariant:
  Actionable BUY/SELL trade signals MUST NEVER be generated when the underlying asset's market is closed.
"""

from datetime import datetime, timezone, timedelta, time
from typing import Dict, Any, List, Optional, Tuple

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

from app.logs.logger import get_logger

logger = get_logger(__name__)

IST_TZ = zoneinfo.ZoneInfo("Asia/Kolkata")


class AssetTradingCalendar:
    """
    Detailed trading schedule rules per asset class.
    """
    ASSET_SCHEDULES = {
        "BTCUSD": {"class": "CRYPTO", "venue": "CRYPTO_24_7", "open_all_week": True},
        "ETHUSD": {"class": "CRYPTO", "venue": "CRYPTO_24_7", "open_all_week": True},
        "EURUSD": {"class": "FOREX", "venue": "FX_INTERBANK", "open_all_week": False},
        "GBPUSD": {"class": "FOREX", "venue": "FX_INTERBANK", "open_all_week": False},
        "USDJPY": {"class": "FOREX", "venue": "FX_INTERBANK", "open_all_week": False},
        "AUDUSD": {"class": "FOREX", "venue": "FX_INTERBANK", "open_all_week": False},
        "XAUUSD": {"class": "METALS", "venue": "COMEX_METALS", "open_all_week": False},
        "NAS100": {"class": "INDEX_CFD", "venue": "CME_GLOBEX", "open_all_week": False},
        "SPX500": {"class": "INDEX_CFD", "venue": "CME_GLOBEX", "open_all_week": False},
    }


class MarketSessionService:
    """
    Authoritative service to evaluate real-time market open/closed status for any symbol.
    """

    @classmethod
    def get_market_status(cls, symbol: str, dt_utc: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Returns complete market session status for a specific symbol at a given UTC time.
        """
        now_utc = dt_utc or datetime.now(timezone.utc)
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)

        sym_upper = symbol.upper()
        sched = AssetTradingCalendar.ASSET_SCHEDULES.get(sym_upper, {
            "class": "FX", "venue": "FX_INTERBANK", "open_all_week": False
        })

        asset_class = sched["class"]

        # 1. Crypto is always 24/7 open
        if sched.get("open_all_week", False):
            return {
                "symbol": sym_upper,
                "asset_class": asset_class,
                "venue": sched["venue"],
                "is_market_open": True,
                "current_session": "24/7_CONTINUOUS",
                "status_label": "OPEN",
                "reason": "CRYPTO_24_7",
                "next_open_utc": None,
                "next_close_utc": None,
                "evaluated_at_utc": now_utc.isoformat(),
                "evaluated_at_ist": now_utc.astimezone(IST_TZ).strftime("%A, %d %B %Y %I:%M %p IST"),
            }

        # 2. Traditional Markets (Forex, Metals, Indices)
        # Weekday: 0 = Mon, 1 = Tue, 2 = Wed, 3 = Thu, 4 = Fri, 5 = Sat, 6 = Sun
        weekday = now_utc.weekday()
        hour = now_utc.hour
        minute = now_utc.minute
        time_decimal = hour + (minute / 60.0)

        is_open = False
        reason = "NORMAL_HOURS"
        session_name = "CLOSED"

        if asset_class == "FOREX":
            # Forex Opens Sunday 22:00 UTC and closes Friday 21:00 UTC
            if weekday == 5:  # Saturday -> always closed
                is_open = False
                reason = "WEEKEND_SATURDAY"
            elif weekday == 6:  # Sunday -> open only after 22:00 UTC
                if time_decimal >= 22.0:
                    is_open = True
                    session_name = "SYDNEY_OPEN"
                else:
                    is_open = False
                    reason = "WEEKEND_SUNDAY_PRE_MARKET"
            elif weekday == 4:  # Friday -> closes at 21:00 UTC
                if time_decimal < 21.0:
                    is_open = True
                    session_name = "NEW_YORK_SESSION"
                else:
                    is_open = False
                    reason = "WEEKEND_FRIDAY_CLOSE"
            else:  # Monday to Thursday -> open 24 hours
                is_open = True
                if 0 <= time_decimal < 7:
                    session_name = "ASIAN_SESSION"
                elif 7 <= time_decimal < 12:
                    session_name = "LONDON_SESSION"
                elif 12 <= time_decimal < 16:
                    session_name = "LONDON_NY_OVERLAP"
                elif 16 <= time_decimal < 21:
                    session_name = "NEW_YORK_SESSION"
                else:
                    session_name = "PACIFIC_SESSION"

        elif asset_class == "METALS":
            # Metals (XAUUSD): Mon-Fri 00:00 - 21:00 UTC (Daily break 21:00 - 22:00 UTC)
            if weekday in (5, 6):  # Weekend
                is_open = False
                reason = "WEEKEND_METALS_CLOSED"
            elif 21.0 <= time_decimal < 22.0:
                is_open = False
                reason = "DAILY_MAINTENANCE_BREAK"
            elif weekday == 4 and time_decimal >= 21.0:
                is_open = False
                reason = "WEEKEND_METALS_CLOSED"
            else:
                is_open = True
                session_name = "METALS_TRADING"

        elif asset_class in ("INDEX_CFD", "INDEX"):
            # Indices (NAS100, SPX500): Mon-Fri with weekend closed
            if weekday in (5, 6):
                is_open = False
                reason = "WEEKEND_INDEX_CLOSED"
            elif 21.15 <= time_decimal < 22.0:
                is_open = False
                reason = "DAILY_SETTLEMENT_BREAK"
            elif weekday == 4 and time_decimal >= 21.0:
                is_open = False
                reason = "WEEKEND_INDEX_CLOSED"
            else:
                is_open = True
                session_name = "GLOBEX_SESSION"

        # Calculate next open / next close
        next_open_utc = None
        next_close_utc = None

        if not is_open:
            # If closed on weekend, next open is Sunday 22:00 UTC (for FX) or Monday 00:00 UTC (for Metals)
            if weekday == 5:  # Saturday
                days_to_sun = 1
                next_open_dt = (now_utc + timedelta(days=days_to_sun)).replace(hour=22, minute=0, second=0, microsecond=0)
            elif weekday == 6 and time_decimal < 22.0:  # Sunday pre-market
                next_open_dt = now_utc.replace(hour=22, minute=0, second=0, microsecond=0)
            elif weekday == 4 and time_decimal >= 21.0:  # Friday post-market
                next_open_dt = (now_utc + timedelta(days=2)).replace(hour=22, minute=0, second=0, microsecond=0)
            else:
                # Daily break
                next_open_dt = now_utc.replace(hour=22, minute=0, second=0, microsecond=0)
                if next_open_dt <= now_utc:
                    next_open_dt += timedelta(days=1)
            next_open_utc = next_open_dt.isoformat()
        else:
            # If currently open, next close is either 21:00 UTC today (if Friday) or daily break
            if weekday == 4:
                next_close_dt = now_utc.replace(hour=21, minute=0, second=0, microsecond=0)
            else:
                next_close_dt = now_utc.replace(hour=21, minute=0, second=0, microsecond=0)
                if next_close_dt <= now_utc:
                    next_close_dt += timedelta(days=1)
            next_close_utc = next_close_dt.isoformat()

        return {
            "symbol": sym_upper,
            "asset_class": asset_class,
            "venue": sched["venue"],
            "is_market_open": is_open,
            "current_session": session_name if is_open else "CLOSED",
            "status_label": "OPEN" if is_open else "CLOSED",
            "reason": reason if not is_open else "MARKET_OPEN",
            "next_open_utc": next_open_utc,
            "next_close_utc": next_close_utc,
            "evaluated_at_utc": now_utc.isoformat(),
            "evaluated_at_ist": now_utc.astimezone(IST_TZ).strftime("%A, %d %B %Y %I:%M %p IST"),
        }

    @classmethod
    def is_market_open(cls, symbol: str, dt_utc: Optional[datetime] = None) -> bool:
        """Helper returning boolean whether the symbol is currently open for active trading."""
        status = cls.get_market_status(symbol, dt_utc)
        return bool(status.get("is_market_open", False))

    @classmethod
    def get_all_market_statuses(cls, dt_utc: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Returns status list for all 9 core assets."""
        symbols = list(AssetTradingCalendar.ASSET_SCHEDULES.keys())
        return [cls.get_market_status(sym, dt_utc) for sym in symbols]


market_session_service = MarketSessionService()
