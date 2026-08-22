from datetime import datetime
from typing import Any


class MarketConditionFilters:
    """
    Phase 2: Market Filters (Spread, Holiday, Weekend, Market Open/Close)
    """
    def __init__(self, max_spread: float = 2.0):
        self.max_spread = max_spread
        # Extremely simplified US holiday set for example purposes
        self.holidays = ["01-01", "07-04", "12-25"]

    def is_weekend(self, timestamp: datetime) -> bool:
        """Returns True if it's Saturday or Sunday"""
        return timestamp.weekday() >= 5

    def is_holiday(self, timestamp: datetime) -> bool:
        """Returns True if it matches a known holiday"""
        date_str = timestamp.strftime("%m-%d")
        return date_str in self.holidays

    def check_spread(self, spread: float) -> bool:
        """Returns True if spread is acceptable"""
        return spread <= self.max_spread

    def check_all(self, context: dict[str, Any]) -> dict[str, bool]:
        """
        Takes context (including timestamp and spread) and returns validation results.
        """
        dt = context.get("timestamp", datetime.now())
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except ValueError:
                dt = datetime.now()

        spread = context.get("spread", 0.0)

        weekend_fail = self.is_weekend(dt)
        holiday_fail = self.is_holiday(dt)
        spread_fail = not self.check_spread(spread)

        is_valid = not (weekend_fail or holiday_fail or spread_fail)

        return {
            "is_valid": is_valid,
            "weekend_fail": weekend_fail,
            "holiday_fail": holiday_fail,
            "spread_fail": spread_fail
        }

market_condition_filters = MarketConditionFilters()
