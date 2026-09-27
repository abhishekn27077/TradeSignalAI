import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Structure.models import Direction
from app.strategies.Structure.strength import StructureStrengthEngine
from app.strategies.Technical.technical_evidence_engine import TechnicalEvidenceEngine


class AlignmentState(str, Enum):
    FULLY_ALIGNED_BULLISH = "FULLY_ALIGNED_BULLISH"
    FULLY_ALIGNED_BEARISH = "FULLY_ALIGNED_BEARISH"
    PARTIALLY_ALIGNED_BULLISH = "PARTIALLY_ALIGNED_BULLISH"
    PARTIALLY_ALIGNED_BEARISH = "PARTIALLY_ALIGNED_BEARISH"
    COUNTER_TREND = "COUNTER_TREND"
    CONFLICTING = "CONFLICTING"


@dataclass
class MTFAlignment:
    asset: str
    htf_timeframe: str
    htf_bias: Direction
    mtf_timeframe: str
    mtf_bias: Direction
    ltf_timeframe: str
    ltf_bias: Direction
    alignment_state: AlignmentState
    alignment_score: float  # 0.0 to 1.0
    recommended_direction: Direction
    is_counter_trend: bool
    timestamp_utc: datetime
    timestamp_ist: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "htf_timeframe": self.htf_timeframe,
            "htf_bias": self.htf_bias.value if hasattr(self.htf_bias, 'value') else str(self.htf_bias),
            "mtf_timeframe": self.mtf_timeframe,
            "mtf_bias": self.mtf_bias.value if hasattr(self.mtf_bias, 'value') else str(self.mtf_bias),
            "ltf_timeframe": self.ltf_timeframe,
            "ltf_bias": self.ltf_bias.value if hasattr(self.ltf_bias, 'value') else str(self.ltf_bias),
            "alignment_state": self.alignment_state.value if hasattr(self.alignment_state, 'value') else str(self.alignment_state),
            "alignment_score": float(self.alignment_score),
            "recommended_direction": self.recommended_direction.value if hasattr(self.recommended_direction, 'value') else str(self.recommended_direction),
            "is_counter_trend": self.is_counter_trend,
            "timestamp_utc": self.timestamp_utc.isoformat() if isinstance(self.timestamp_utc, datetime) else str(self.timestamp_utc),
            "timestamp_ist": self.timestamp_ist,
            "details": self.details,
        }


class MTFEngine:
    """
    Multi-Timeframe Hierarchy Engine.
    Coordinates HTF Bias (1D/4H), MTF Structure (1H), and LTF Precision Execution (15M/5M).
    """

    def __init__(self):
        self.strength_engine = StructureStrengthEngine()
        self.technical_engine = TechnicalEvidenceEngine()

    def evaluate_mtf(
        self,
        df_htf: Optional[pd.DataFrame],
        df_mtf: Optional[pd.DataFrame],
        df_ltf: Optional[pd.DataFrame],
        asset: str = "UNKNOWN",
        htf_tf: str = "1D",
        mtf_tf: str = "1H",
        ltf_tf: str = "15M"
    ) -> MTFAlignment:
        now_utc = MarketClockService.get_current_utc()
        now_ist = MarketClockService.format_ist(now_utc)

        htf_bias = self._evaluate_timeframe_bias(df_htf, asset, htf_tf)
        mtf_bias = self._evaluate_timeframe_bias(df_mtf, asset, mtf_tf)
        ltf_bias = self._evaluate_timeframe_bias(df_ltf, asset, ltf_tf)

        # Calculate alignment
        bull_votes = sum([1 for b in [htf_bias, mtf_bias, ltf_bias] if b == Direction.BULLISH])
        bear_votes = sum([1 for b in [htf_bias, mtf_bias, ltf_bias] if b == Direction.BEARISH])

        is_counter = False
        if htf_bias != Direction.NEUTRAL and ltf_bias != Direction.NEUTRAL and htf_bias != ltf_bias:
            is_counter = True

        if bull_votes == 3:
            state = AlignmentState.FULLY_ALIGNED_BULLISH
            score = 1.0
            rec_dir = Direction.BULLISH
        elif bear_votes == 3:
            state = AlignmentState.FULLY_ALIGNED_BEARISH
            score = 1.0
            rec_dir = Direction.BEARISH
        elif bull_votes == 2:
            state = AlignmentState.PARTIALLY_ALIGNED_BULLISH
            score = 0.70
            rec_dir = Direction.BULLISH
        elif bear_votes == 2:
            state = AlignmentState.PARTIALLY_ALIGNED_BEARISH
            score = 0.70
            rec_dir = Direction.BEARISH
        elif is_counter:
            state = AlignmentState.COUNTER_TREND
            score = 0.40
            rec_dir = ltf_bias
        else:
            state = AlignmentState.CONFLICTING
            score = 0.30
            rec_dir = Direction.NEUTRAL

        return MTFAlignment(
            asset=asset,
            htf_timeframe=htf_tf,
            htf_bias=htf_bias,
            mtf_timeframe=mtf_tf,
            mtf_bias=mtf_bias,
            ltf_timeframe=ltf_tf,
            ltf_bias=ltf_bias,
            alignment_state=state,
            alignment_score=score,
            recommended_direction=rec_dir,
            is_counter_trend=is_counter,
            timestamp_utc=now_utc,
            timestamp_ist=now_ist,
            details={"bull_votes": bull_votes, "bear_votes": bear_votes}
        )

    def _evaluate_timeframe_bias(self, df: Optional[pd.DataFrame], asset: str, tf: str) -> Direction:
        if df is None or len(df) < 15:
            return Direction.NEUTRAL

        tech = self.technical_engine.evaluate_evidence(df, asset=asset, timeframe=tf)
        st = tech.get("SUPERTREND")
        adx = tech.get("ADX")
        rsi = tech.get("RSI")

        scores = 0
        if st and st.direction == Direction.BULLISH:
            scores += 1
        elif st and st.direction == Direction.BEARISH:
            scores -= 1

        if adx and adx.direction == Direction.BULLISH:
            scores += 1
        elif adx and adx.direction == Direction.BEARISH:
            scores -= 1

        if rsi and rsi.direction == Direction.BULLISH:
            scores += 1
        elif rsi and rsi.direction == Direction.BEARISH:
            scores -= 1

        if scores > 0:
            return Direction.BULLISH
        elif scores < 0:
            return Direction.BEARISH
        return Direction.NEUTRAL
