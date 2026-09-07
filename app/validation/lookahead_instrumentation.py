"""
app/validation/lookahead_instrumentation.py
===========================================
Lookahead Detection & Timestamp Guard Instrumentation (Phase 71).

Asserts that no model, indicator, or signal decision accesses any candle data
with timestamp strictly greater than the decision timestamp (T0).
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional, Union
import pandas as pd


class LookaheadViolationError(AssertionError):
    """Raised when an algorithm accesses a future candle timestamp beyond decision time T0."""
    pass


class LookaheadGuard:
    """
    Instruments data access to guarantee zero future-leakage.
    """

    @staticmethod
    def assert_no_lookahead(
        input_data: Union[pd.DataFrame, List[dict], List[str]],
        decision_timestamp: datetime,
        component_name: str = "UnknownComponent"
    ):
        """
        Validates that all input timestamps are <= decision_timestamp.
        """
        if isinstance(input_data, pd.DataFrame):
            if 'timestamp' in input_data.columns:
                ts_series = pd.to_datetime(input_data['timestamp'], utc=True, format='mixed')
            elif isinstance(input_data.index, pd.DatetimeIndex):
                ts_series = input_data.index.tz_convert(timezone.utc) if input_data.index.tz else input_data.index.tz_localize(timezone.utc)
            else:
                return

            max_ts = ts_series.max()
            if max_ts > decision_timestamp:
                raise LookaheadViolationError(
                    f"LOOKAHEAD VIOLATION in {component_name}! "
                    f"Max input timestamp {max_ts.isoformat()} > Decision timestamp {decision_timestamp.isoformat()}"
                )
        elif isinstance(input_data, list) and len(input_data) > 0 and isinstance(input_data[0], dict):
            for item in input_data:
                ts_val = item.get("timestamp") or item.get("created_at")
                if ts_val:
                    parsed = pd.to_datetime(ts_val, utc=True, format='mixed')
                    if parsed > decision_timestamp:
                        raise LookaheadViolationError(
                            f"LOOKAHEAD VIOLATION in {component_name}! "
                            f"Input timestamp {parsed.isoformat()} > Decision timestamp {decision_timestamp.isoformat()}"
                        )


lookahead_guard = LookaheadGuard()
