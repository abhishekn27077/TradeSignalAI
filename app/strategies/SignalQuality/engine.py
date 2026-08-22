import numpy as np
from typing import Dict, Any, Optional, List

from app.strategies.SignalQuality.models import SignalGrade, NoTradeReason, SignalQualityEvaluation
from app.market_data.quality.models import DataQualityState


class SignalQualityEngine:
    """
    Institutional Signal Quality & NO-TRADE Gating Engine.
    Strictly grades setups (A+, A, B, C) and emits explicit NO_TRADE rejection reasons.
    """

    def __init__(
        self,
        min_rr_ratio: float = 1.2,
        min_confluence_score: float = 50.0,
        max_allowed_spread_pips: float = 4.0
    ):
        self.min_rr_ratio = min_rr_ratio
        self.min_confluence_score = min_confluence_score
        self.max_allowed_spread_pips = max_allowed_spread_pips

    def evaluate_signal_quality(
        self,
        asset: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        confluence_score: float,
        data_quality_state: DataQualityState = DataQualityState.DATA_QUALITY_GOOD,
        htf_aligned: bool = True,
        is_event_risk: bool = False,
        current_spread_pips: float = 1.5,
        portfolio_exposure_blocked: bool = False,
        structure_bias: str = "NEUTRAL"
    ) -> SignalQualityEvaluation:
        rejections: List[NoTradeReason] = []
        messages: List[str] = []

        # 1. Data Quality Gate
        data_healthy = True
        if data_quality_state == DataQualityState.DATA_STALE:
            rejections.append(NoTradeReason.DATA_STALE)
            messages.append("Signal rejected: Market data feed is stale.")
            data_healthy = False
        elif data_quality_state == DataQualityState.DATA_UNAVAILABLE:
            rejections.append(NoTradeReason.DATA_UNAVAILABLE)
            messages.append("Signal rejected: Market data feed is unavailable.")
            data_healthy = False
        elif data_quality_state == DataQualityState.DATA_CORRUPTED:
            rejections.append(NoTradeReason.DATA_CORRUPTED)
            messages.append("Signal rejected: Market data corruption detected.")
            data_healthy = False

        # 2. Neutral Direction Check
        if direction.upper() not in ["BUY", "SELL"]:
            rejections.append(NoTradeReason.INSUFFICIENT_EVIDENCE)
            messages.append("Signal rejected: No directional consensus (NEUTRAL).")

        # 3. Risk-to-Reward (R:R) Calculation
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        rr_ratio = (reward / risk) if risk > 1e-6 else 0.0

        if rr_ratio < self.min_rr_ratio:
            rejections.append(NoTradeReason.POOR_RR)
            messages.append(f"Signal rejected: R:R ratio {rr_ratio:.2f} is below minimum {self.min_rr_ratio:.2f}.")

        # 4. Confluence Score Gate
        if confluence_score < self.min_confluence_score:
            rejections.append(NoTradeReason.LOW_CONFLUENCE)
            messages.append(f"Signal rejected: Confluence score {confluence_score:.1f} is below threshold {self.min_confluence_score:.1f}.")

        # 5. Macroeconomic Event Risk Gate
        if is_event_risk:
            rejections.append(NoTradeReason.EVENT_RISK)
            messages.append("Signal rejected: High-impact economic news window active.")

        # 6. Spread Filter Gate
        if current_spread_pips > self.max_allowed_spread_pips:
            rejections.append(NoTradeReason.HIGH_SPREAD)
            messages.append(f"Signal rejected: Current spread {current_spread_pips:.1f} pips exceeds maximum {self.max_allowed_spread_pips:.1f} pips.")

        # 7. HTF Structure Alignment Gate
        if not htf_aligned:
            rejections.append(NoTradeReason.NO_HTF_ALIGNMENT)
            messages.append("Signal warning/rejected: Higher timeframe trend is opposing.")

        # 8. Portfolio Exposure Gate
        if portfolio_exposure_blocked:
            rejections.append(NoTradeReason.PORTFOLIO_RISK)
            messages.append("Signal rejected: Maximum correlated portfolio currency exposure reached.")

        # 9. Structure Conflict
        if (direction == "BUY" and structure_bias == "BEARISH") or (direction == "SELL" and structure_bias == "BULLISH"):
            rejections.append(NoTradeReason.CONFLICTING_STRUCTURE)
            messages.append(f"Signal rejected: Direction {direction} conflicts with structural bias {structure_bias}.")

        # Calculate Final Grade
        is_actionable = (len(rejections) == 0)
        quality_score = max(0.0, min(100.0, confluence_score * (rr_ratio / 2.0) if is_actionable else 0.0))

        if not is_actionable:
            grade = SignalGrade.NO_TRADE
        elif confluence_score >= 85.0 and rr_ratio >= 1.5 and htf_aligned:
            grade = SignalGrade.A_PLUS
        elif confluence_score >= 75.0 and rr_ratio >= 1.3:
            grade = SignalGrade.A
        elif confluence_score >= 60.0 and rr_ratio >= 1.2:
            grade = SignalGrade.B
        else:
            grade = SignalGrade.C

        return SignalQualityEvaluation(
            asset=asset,
            grade=grade,
            is_actionable=is_actionable,
            quality_score=quality_score,
            rejection_reasons=rejections,
            rejection_messages=messages,
            risk_reward_ratio=rr_ratio,
            confluence_score=confluence_score,
            htf_aligned=htf_aligned,
            data_quality_healthy=data_healthy,
            details={
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_pips": round(risk * 10000, 1),
                "reward_pips": round(reward * 10000, 1),
            }
        )
