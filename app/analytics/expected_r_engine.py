"""
app/analytics/expected_r_engine.py
==================================
Expected-R & Multi-Tier Signal Quality Engine for TradeSignalAI-v3.

Calculates:
1. Calibrated Probability from Raw Model Confidence
2. Path Probabilities: P(TP First), P(SL First), P(Time Exit)
3. Asset Friction Modeling: Spread, Slippage, Broker Fees (converted to R-multiples)
4. Expected Gross R and Expected Net R
5. Signal Quality Tier: A+, A, B, C, WATCH, REJECTED
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import math


@dataclass
class ExpectedRReport:
    raw_confidence: float
    calibrated_probability: float
    p_tp_first: float
    p_sl_first: float
    p_time_exit: float
    reward_risk_ratio: float
    spread_cost_r: float
    slippage_cost_r: float
    fees_cost_r: float
    total_frictions_r: float
    expected_gross_r: float
    expected_net_r: float
    quality_grade: str  # "A+", "A", "B", "C", "WATCH", "REJECTED"
    decision: str       # "QUALIFIED", "WATCHLIST", "NO_TRADE"
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_confidence": round(self.raw_confidence, 4),
            "calibrated_probability": round(self.calibrated_probability, 4),
            "p_tp_first": round(self.p_tp_first, 4),
            "p_sl_first": round(self.p_sl_first, 4),
            "p_time_exit": round(self.p_time_exit, 4),
            "reward_risk_ratio": round(self.reward_risk_ratio, 2),
            "spread_cost_r": round(self.spread_cost_r, 4),
            "slippage_cost_r": round(self.slippage_cost_r, 4),
            "fees_cost_r": round(self.fees_cost_r, 4),
            "total_frictions_r": round(self.total_frictions_r, 4),
            "expected_gross_r": round(self.expected_gross_r, 4),
            "expected_net_r": round(self.expected_net_r, 4),
            "quality_grade": self.quality_grade,
            "decision": self.decision,
            "reason": self.reason,
        }


class ExpectedREngine:
    """
    Computes mathematical expected value and assigns evidence-based quality ratings.
    """

    # Asset class friction defaults (in R units for typical 1R = 1.5x ATR stop)
    ASSET_FRICTION_DEFAULTS = {
        "EURUSD": {"spread_r": 0.03, "slippage_r": 0.02, "fee_r": 0.01},
        "GBPUSD": {"spread_r": 0.04, "slippage_r": 0.02, "fee_r": 0.01},
        "USDJPY": {"spread_r": 0.03, "slippage_r": 0.02, "fee_r": 0.01},
        "AUDUSD": {"spread_r": 0.04, "slippage_r": 0.02, "fee_r": 0.01},
        "BTCUSD": {"spread_r": 0.05, "slippage_r": 0.04, "fee_r": 0.02},
        "ETHUSD": {"spread_r": 0.05, "slippage_r": 0.04, "fee_r": 0.02},
        "XAUUSD": {"spread_r": 0.06, "slippage_r": 0.03, "fee_r": 0.01},
        "NAS100": {"spread_r": 0.04, "slippage_r": 0.03, "fee_r": 0.01},
        "SPX500": {"spread_r": 0.03, "slippage_r": 0.02, "fee_r": 0.01},
    }

    def calibrate_probability(self, raw_confidence: float) -> float:
        """
        Applies empirical isotonic / sigmoid calibration.
        Raw 80% confidence maps to realistic ~70% calibrated probability.
        """
        # Sigmoid calibration centered around 0.60
        calibrated = 1.0 / (1.0 + math.exp(-3.5 * (raw_confidence - 0.58)))
        return max(0.40, min(0.85, calibrated))

    def evaluate_expected_value(
        self,
        asset: str,
        raw_confidence: float,
        reward_risk_ratio: float = 2.0,
        analogue_p_tp: Optional[float] = None,
        analogue_p_sl: Optional[float] = None,
        consensus_agreement_pct: float = 75.0,
        mtf_aligned: bool = True,
        event_risk: str = "LOW",
    ) -> ExpectedRReport:
        """
        Computes expected net R and assigns quality tier.
        """
        calibrated_prob = self.calibrate_probability(raw_confidence)

        # Path probabilities: blend calibrated probability with historical analogue estimates
        if analogue_p_tp is not None and analogue_p_sl is not None:
            p_tp = (calibrated_prob * 0.6) + (analogue_p_tp * 0.4)
            p_sl = ((1.0 - calibrated_prob) * 0.6) + (analogue_p_sl * 0.4)
        else:
            p_tp = calibrated_prob * 0.90
            p_sl = (1.0 - calibrated_prob) * 0.85
        
        p_time = max(0.0, 1.0 - (p_tp + p_sl))
        total_p = p_tp + p_sl + p_time
        p_tp /= total_p
        p_sl /= total_p
        p_time /= total_p

        # Frictions
        frictions = self.ASSET_FRICTION_DEFAULTS.get(
            asset, {"spread_r": 0.04, "slippage_r": 0.03, "fee_r": 0.01}
        )
        spread_r = frictions["spread_r"]
        slip_r = frictions["slippage_r"]
        fee_r = frictions["fee_r"]
        total_frictions = spread_r + slip_r + fee_r

        # Expected Value Math:
        # Gross = P(TP) * RR - P(SL) * 1.0 + P(Time) * 0.0
        expected_gross = (p_tp * reward_risk_ratio) - (p_sl * 1.0)
        expected_net = expected_gross - total_frictions

        # Quality Grade Classification
        if event_risk == "HIGH":
            quality = "REJECTED"
            decision = "NO_TRADE"
            reason = "HIGH_EVENT_RISK_GATED"
        elif expected_net <= 0.0:
            quality = "REJECTED"
            decision = "NO_TRADE"
            reason = "NEGATIVE_EXPECTED_NET_R"
        elif calibrated_prob >= 0.70 and expected_net >= 0.30 and mtf_aligned and consensus_agreement_pct >= 70.0:
            quality = "A+"
            decision = "QUALIFIED"
            reason = "HIGH_EDGE_A_PLUS_SETUP"
        elif calibrated_prob >= 0.65 and expected_net >= 0.20 and consensus_agreement_pct >= 60.0:
            quality = "A"
            decision = "QUALIFIED"
            reason = "ROBUST_EDGE_A_SETUP"
        elif calibrated_prob >= 0.60 and expected_net >= 0.10:
            quality = "B"
            decision = "QUALIFIED"
            reason = "MODERATE_EDGE_B_SETUP"
        elif expected_net > 0.0:
            quality = "C"
            decision = "WATCHLIST"
            reason = "MARGINAL_EDGE_WATCHLIST"
        else:
            quality = "WATCH"
            decision = "WATCHLIST"
            reason = "PENDING_CONFIRMATION"

        return ExpectedRReport(
            raw_confidence=raw_confidence,
            calibrated_probability=calibrated_prob,
            p_tp_first=p_tp,
            p_sl_first=p_sl,
            p_time_exit=p_time,
            reward_risk_ratio=reward_risk_ratio,
            spread_cost_r=spread_r,
            slippage_cost_r=slip_r,
            fees_cost_r=fee_r,
            total_frictions_r=total_frictions,
            expected_gross_r=expected_gross,
            expected_net_r=expected_net,
            quality_grade=quality,
            decision=decision,
            reason=reason,
        )


# Global Singleton
expected_r_engine = ExpectedREngine()
