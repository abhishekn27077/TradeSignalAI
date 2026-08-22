import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Structure.models import SwingPoint, SwingType, Direction
from app.strategies.Structure.swing import SwingDetector


class SMTState(str, Enum):
    BULLISH_SMT = "BULLISH_SMT"
    BEARISH_SMT = "BEARISH_SMT"
    NO_SMT = "NO_SMT"
    CORRELATION_UNAVAILABLE = "CORRELATION_UNAVAILABLE"


@dataclass
class SMTResult:
    asset_a: str
    asset_b: str
    timeframe: str
    state: SMTState
    direction: Direction
    strength: float
    timestamp_utc: datetime
    timestamp_ist: str
    asset_a_swing: Optional[str] = None
    asset_b_swing: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_a": self.asset_a,
            "asset_b": self.asset_b,
            "timeframe": self.timeframe,
            "state": self.state.value if hasattr(self.state, 'value') else str(self.state),
            "direction": self.direction.value if hasattr(self.direction, 'value') else str(self.direction),
            "strength": float(self.strength),
            "timestamp_utc": self.timestamp_utc.isoformat() if isinstance(self.timestamp_utc, datetime) else str(self.timestamp_utc),
            "timestamp_ist": self.timestamp_ist,
            "asset_a_swing": self.asset_a_swing,
            "asset_b_swing": self.asset_b_swing,
            "details": self.details,
        }


class SMTDivergenceDetector:
    """
    Detects Smart Money Technique (SMT) divergences across correlated asset pairs.
    Positively Correlated Pairs:
      - e.g. BTCUSD vs ETHUSD, EURUSD vs GBPUSD
      - Bullish SMT: Asset A forms Lower Low while Asset B forms Higher Low.
      - Bearish SMT: Asset A forms Higher High while Asset B forms Lower High.

    Inversely Correlated Pairs:
      - e.g. EURUSD vs DXY, XAUUSD vs DXY
      - Bullish SMT: Asset A forms Lower Low while Inverse Asset B fails to form Higher High (forms Lower High).
      - Bearish SMT: Asset A forms Higher High while Inverse Asset B fails to form Lower Low (forms Higher Low).
    """

    INVERSE_PAIRS = {
        ("EURUSD", "DXY"), ("DXY", "EURUSD"),
        ("GBPUSD", "DXY"), ("DXY", "GBPUSD"),
        ("XAUUSD", "DXY"), ("DXY", "XAUUSD"),
        ("AUDUSD", "DXY"), ("DXY", "AUDUSD"),
    }

    def __init__(self, swing_len: int = 5):
        self.swing_detector = SwingDetector(left_len=swing_len, right_len=swing_len)

    def detect_smt(
        self,
        df_a: pd.DataFrame,
        df_b: Optional[pd.DataFrame],
        asset_a: str,
        asset_b: str = "DXY",
        timeframe: str = "1H"
    ) -> SMTResult:
        now_utc = MarketClockService.get_current_utc()
        now_ist = MarketClockService.format_ist(now_utc)

        if df_a is None or df_b is None or len(df_a) < 15 or len(df_b) < 15:
            return SMTResult(
                asset_a=asset_a,
                asset_b=asset_b,
                timeframe=timeframe,
                state=SMTState.CORRELATION_UNAVAILABLE,
                direction=Direction.NEUTRAL,
                strength=0.0,
                timestamp_utc=now_utc,
                timestamp_ist=now_ist
            )

        is_inverse = (asset_a, asset_b) in self.INVERSE_PAIRS or (asset_b, asset_a) in self.INVERSE_PAIRS

        swings_a = self.swing_detector.detect_swings(df_a, asset=asset_a, timeframe=timeframe)
        swings_b = self.swing_detector.detect_swings(df_b, asset=asset_b, timeframe=timeframe)

        highs_a = [s for s in swings_a if s.swing_type == SwingType.SWING_HIGH]
        lows_a = [s for s in swings_a if s.swing_type == SwingType.SWING_LOW]

        highs_b = [s for s in swings_b if s.swing_type == SwingType.SWING_HIGH]
        lows_b = [s for s in swings_b if s.swing_type == SwingType.SWING_LOW]

        if is_inverse:
            # For Inverse Bullish SMT: need 2 lows in A and 2 highs in B
            # For Inverse Bearish SMT: need 2 highs in A and 2 lows in B
            if (len(lows_a) < 2 or len(highs_b) < 2) and (len(highs_a) < 2 or len(lows_b) < 2):
                return SMTResult(
                    asset_a=asset_a,
                    asset_b=asset_b,
                    timeframe=timeframe,
                    state=SMTState.NO_SMT,
                    direction=Direction.NEUTRAL,
                    strength=0.0,
                    timestamp_utc=now_utc,
                    timestamp_ist=now_ist
                )
        else:
            if (len(lows_a) < 2 or len(lows_b) < 2) and (len(highs_a) < 2 or len(highs_b) < 2):
                return SMTResult(
                    asset_a=asset_a,
                    asset_b=asset_b,
                    timeframe=timeframe,
                    state=SMTState.NO_SMT,
                    direction=Direction.NEUTRAL,
                    strength=0.0,
                    timestamp_utc=now_utc,
                    timestamp_ist=now_ist
                )

        # 1. Positively Correlated Pairs
        if not is_inverse:
            # Bullish SMT: A makes LL, B makes HL
            a_made_ll = lows_a[-1].price < lows_a[-2].price
            b_made_hl = lows_b[-1].price > lows_b[-2].price
            if a_made_ll and b_made_hl:
                return SMTResult(
                    asset_a=asset_a,
                    asset_b=asset_b,
                    timeframe=timeframe,
                    state=SMTState.BULLISH_SMT,
                    direction=Direction.BULLISH,
                    strength=0.85,
                    timestamp_utc=now_utc,
                    timestamp_ist=now_ist,
                    asset_a_swing=f"LL ({lows_a[-1].price:.4f} < {lows_a[-2].price:.4f})",
                    asset_b_swing=f"HL ({lows_b[-1].price:.4f} > {lows_b[-2].price:.4f})",
                    details={"correlation_type": "POSITIVE"}
                )

            # Bearish SMT: A makes HH, B makes LH
            a_made_hh = highs_a[-1].price > highs_a[-2].price
            b_made_lh = highs_b[-1].price < highs_b[-2].price
            if a_made_hh and b_made_lh:
                return SMTResult(
                    asset_a=asset_a,
                    asset_b=asset_b,
                    timeframe=timeframe,
                    state=SMTState.BEARISH_SMT,
                    direction=Direction.BEARISH,
                    strength=0.85,
                    timestamp_utc=now_utc,
                    timestamp_ist=now_ist,
                    asset_a_swing=f"HH ({highs_a[-1].price:.4f} > {highs_a[-2].price:.4f})",
                    asset_b_swing=f"LH ({highs_b[-1].price:.4f} < {highs_b[-2].price:.4f})",
                    details={"correlation_type": "POSITIVE"}
                )

        # 2. Inversely Correlated Pairs (e.g. EURUSD vs DXY)
        else:
            # Bullish SMT: A makes LL, B fails to make HH (makes LH)
            a_made_ll = lows_a[-1].price < lows_a[-2].price
            b_made_lh = highs_b[-1].price < highs_b[-2].price
            if a_made_ll and b_made_lh:
                return SMTResult(
                    asset_a=asset_a,
                    asset_b=asset_b,
                    timeframe=timeframe,
                    state=SMTState.BULLISH_SMT,
                    direction=Direction.BULLISH,
                    strength=0.90,
                    timestamp_utc=now_utc,
                    timestamp_ist=now_ist,
                    asset_a_swing=f"LL ({lows_a[-1].price:.4f} < {lows_a[-2].price:.4f})",
                    asset_b_swing=f"LH ({highs_b[-1].price:.4f} < {highs_b[-2].price:.4f})",
                    details={"correlation_type": "INVERSE"}
                )

            # Bearish SMT: A makes HH, B fails to make LL (makes HL)
            a_made_hh = highs_a[-1].price > highs_a[-2].price
            b_made_hl = lows_b[-1].price > lows_b[-2].price
            if a_made_hh and b_made_hl:
                return SMTResult(
                    asset_a=asset_a,
                    asset_b=asset_b,
                    timeframe=timeframe,
                    state=SMTState.BEARISH_SMT,
                    direction=Direction.BEARISH,
                    strength=0.90,
                    timestamp_utc=now_utc,
                    timestamp_ist=now_ist,
                    asset_a_swing=f"HH ({highs_a[-1].price:.4f} > {highs_a[-2].price:.4f})",
                    asset_b_swing=f"HL ({lows_b[-1].price:.4f} > {lows_b[-2].price:.4f})",
                    details={"correlation_type": "INVERSE"}
                )

        return SMTResult(
            asset_a=asset_a,
            asset_b=asset_b,
            timeframe=timeframe,
            state=SMTState.NO_SMT,
            direction=Direction.NEUTRAL,
            strength=0.0,
            timestamp_utc=now_utc,
            timestamp_ist=now_ist
        )
