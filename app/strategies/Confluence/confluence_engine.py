import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.core.market_clock import MarketClockService
from app.strategies.Structure.models import Direction
from app.strategies.Regime.regime_classifier import MarketRegime, RegimeClassifier


@dataclass
class ConfluenceScore:
    asset: str
    timeframe: str
    total_score: float  # 0.0 to 100.0
    direction: Direction
    confidence: float   # 0.0 to 1.0
    is_actionable: bool
    structure_score: float
    smc_score: float
    liquidity_score: float
    session_score: float
    smt_score: float
    technical_score: float
    collinearity_penalty_applied: float
    regime: str
    timestamp_utc: datetime
    timestamp_ist: str
    breakdown: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "timeframe": self.timeframe,
            "total_score": round(float(self.total_score), 2),
            "direction": self.direction.value if hasattr(self.direction, 'value') else str(self.direction),
            "confidence": round(float(self.confidence), 2),
            "is_actionable": self.is_actionable,
            "layer_scores": {
                "structure": round(float(self.structure_score), 2),
                "smc": round(float(self.smc_score), 2),
                "liquidity": round(float(self.liquidity_score), 2),
                "session": round(float(self.session_score), 2),
                "smt": round(float(self.smt_score), 2),
                "technical": round(float(self.technical_score), 2),
            },
            "collinearity_penalty_applied": round(float(self.collinearity_penalty_applied), 2),
            "regime": self.regime,
            "timestamp_utc": self.timestamp_utc.isoformat() if isinstance(self.timestamp_utc, datetime) else str(self.timestamp_utc),
            "timestamp_ist": self.timestamp_ist,
            "breakdown": self.breakdown,
        }


class ConfluenceEngine:
    """
    Multi-Factor Dynamic Confluence Scoring Engine (0-100).
    Integrates Structure, SMC, Liquidity, Sessions, SMT, and Technicals with collinearity attenuation and dynamic regime weights.
    """

    # Baseline layer weight allocations (Sum = 100.0)
    BASE_WEIGHTS = {
        "structure": 25.0,
        "smc": 20.0,
        "liquidity": 15.0,
        "session": 10.0,
        "smt": 10.0,
        "technical": 20.0,
    }

    ACTIONABLE_SCORE_THRESHOLD = 65.0

    def compute_confluence(
        self,
        asset: str,
        timeframe: str,
        structure_data: Dict[str, Any],
        smc_data: Dict[str, Any],
        liquidity_data: Dict[str, Any],
        session_data: Dict[str, Any],
        smt_data: Dict[str, Any],
        technical_data: Dict[str, Any],
        regime: MarketRegime = MarketRegime.STRONG_TREND
    ) -> ConfluenceScore:
        now_utc = MarketClockService.get_current_utc()
        now_ist = MarketClockService.format_ist(now_utc)

        # 1. Adapt weights dynamically based on market regime
        weights = self._get_regime_weights(regime)

        # 2. Evaluate Layer 1: Market Structure (0.0 to 1.0)
        struct_dir = structure_data.get("bias", "NEUTRAL")
        struct_raw = structure_data.get("score", 50.0) / 100.0  # normalize
        struct_points = weights["structure"] * struct_raw

        # 3. Evaluate Layer 2: SMC (OB + FVG + Dealing Range)
        ob_active = smc_data.get("has_active_ob", False)
        fvg_active = smc_data.get("has_active_fvg", False)
        in_discount = smc_data.get("in_discount", False)
        in_premium = smc_data.get("in_premium", False)

        smc_ratio = 0.0
        if ob_active:
            smc_ratio += 0.4
        if fvg_active:
            smc_ratio += 0.3
        if in_discount or in_premium:
            smc_ratio += 0.3
        smc_points = weights["smc"] * min(1.0, smc_ratio)

        # 4. Evaluate Layer 3: Liquidity & Sweeps
        has_sweep = liquidity_data.get("has_sweep", False)
        sweep_confirmed = liquidity_data.get("sweep_confirmed", False)
        liq_ratio = 0.0
        if has_sweep:
            liq_ratio += 0.6
        if sweep_confirmed:
            liq_ratio += 0.4
        liq_points = weights["liquidity"] * min(1.0, liq_ratio)

        # 5. Evaluate Layer 4: Sessions & Killzones
        is_killzone = session_data.get("is_killzone", False)
        asian_swept = session_data.get("asian_swept", False)
        session_ratio = 0.0
        if is_killzone:
            session_ratio += 0.6
        if asian_swept:
            session_ratio += 0.4
        session_points = weights["session"] * min(1.0, session_ratio)

        # 6. Evaluate Layer 5: SMT & Correlation Divergence
        smt_state = smt_data.get("state", "NO_SMT")
        smt_strength = smt_data.get("strength", 0.0)
        smt_points = weights["smt"] * smt_strength if "BULLISH_SMT" in smt_state or "BEARISH_SMT" in smt_state else 0.0

        # 7. Evaluate Layer 6: Technical Indicators with Collinearity Attenuation
        # Technicals: SuperTrend, UT_Bot, MACD, RSI, ADX, SMA200, VWAP
        tech_votes = technical_data.get("indicator_votes", [])  # list of (name, dir, strength)
        bull_tech = [v for v in tech_votes if v.get("direction") == "BULLISH"]
        bear_tech = [v for v in tech_votes if v.get("direction") == "BEARISH"]

        dominant_tech_votes = bull_tech if len(bull_tech) >= len(bear_tech) else bear_tech
        dominant_tech_dir = Direction.BULLISH if len(bull_tech) >= len(bear_tech) else Direction.BEARISH

        # Apply collinearity attenuation dampeners: [1.0, 0.7, 0.5, 0.3, 0.2, 0.1]
        attenuation = [1.0, 0.7, 0.5, 0.3, 0.2, 0.1, 0.05]
        attenuated_tech_score = 0.0
        max_possible_tech = sum(attenuation[:len(dominant_tech_votes)]) if dominant_tech_votes else 1.0

        for idx, vote in enumerate(dominant_tech_votes):
            att = attenuation[idx] if idx < len(attenuation) else 0.05
            attenuated_tech_score += (vote.get("strength", 0.8) * att)

        tech_normalized = min(1.0, attenuated_tech_score / (max_possible_tech + 1e-6))
        tech_points = weights["technical"] * tech_normalized
        collinearity_penalty = (len(dominant_tech_votes) * 0.25) - attenuated_tech_score

        # 8. Total Score Aggregation
        total_score = struct_points + smc_points + liq_points + session_points + smt_points + tech_points
        total_score = max(0.0, min(100.0, total_score))

        # Determine Primary Direction
        if struct_dir == "BULLISH" or dominant_tech_dir == Direction.BULLISH:
            direction = Direction.BULLISH
        elif struct_dir == "BEARISH" or dominant_tech_dir == Direction.BEARISH:
            direction = Direction.BEARISH
        else:
            direction = Direction.NEUTRAL

        is_actionable = (total_score >= self.ACTIONABLE_SCORE_THRESHOLD) and (direction != Direction.NEUTRAL)
        confidence = min(1.0, max(0.2, total_score / 100.0))

        return ConfluenceScore(
            asset=asset,
            timeframe=timeframe,
            total_score=total_score,
            direction=direction,
            confidence=confidence,
            is_actionable=is_actionable,
            structure_score=struct_points,
            smc_score=smc_points,
            liquidity_score=liq_points,
            session_score=session_points,
            smt_score=smt_points,
            technical_score=tech_points,
            collinearity_penalty_applied=max(0.0, float(collinearity_penalty)),
            regime=regime.value if hasattr(regime, 'value') else str(regime),
            timestamp_utc=now_utc,
            timestamp_ist=now_ist,
            breakdown={
                "weights_used": weights,
                "dominant_tech_count": len(dominant_tech_votes),
            }
        )

    def _get_regime_weights(self, regime: MarketRegime) -> Dict[str, float]:
        w = dict(self.BASE_WEIGHTS)
        if regime in [MarketRegime.STRONG_TREND, MarketRegime.WEAK_TREND]:
            w["structure"] = 30.0
            w["technical"] = 25.0
            w["smc"] = 20.0
            w["liquidity"] = 10.0
            w["session"] = 5.0
            w["smt"] = 10.0
        elif regime in [MarketRegime.RANGE, MarketRegime.LOW_VOLATILITY]:
            w["liquidity"] = 25.0
            w["smc"] = 25.0
            w["structure"] = 15.0
            w["session"] = 15.0
            w["technical"] = 10.0
            w["smt"] = 10.0
        elif regime in [MarketRegime.BREAKOUT, MarketRegime.HIGH_VOLATILITY]:
            w["structure"] = 30.0
            w["technical"] = 25.0
            w["session"] = 15.0
            w["liquidity"] = 15.0
            w["smc"] = 10.0
            w["smt"] = 5.0
        return w
