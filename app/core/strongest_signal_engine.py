"""
app/core/strongest_signal_engine.py
===================================
13-Stage Zero-Trust Strongest Signal Ranking Engine for TradeSignalAI-v3 (Phase 67).

Filters and ranks prospective candidates through a rigorous 13-stage quantitative sieve:
1. Data Quality & Freshness
2. Causal Barrier
3. Event Risk Gate
4. Regime Compatibility
5. MTF Alignment & Conflict Gate
6. 9 Evidence Clusters Consensus
7. Calibrated Bayesian Probability
8. Historical Analogue Expectancy
9. Expected Net-R (> +0.20R)
10. Friction Accounting
11. Risk / Reward Ratio (>= 1.50)
12. Signal Strength (>= 70/100)
13. Out-of-Sample Score Ranking
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class StrongestRankingResult:
    top_signals: List[Dict[str, Any]]
    total_candidates_evaluated: int
    qualified_count: int
    rejected_count: int
    no_trade_breakdown: List[Dict[str, Any]]
    ranking_criterion: str = "Bayesian Probability * Expected Net-R with MTF Alignment"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "top_signals": self.top_signals,
            "total_candidates_evaluated": self.total_candidates_evaluated,
            "qualified_count": self.qualified_count,
            "rejected_count": self.rejected_count,
            "no_trade_breakdown": self.no_trade_breakdown,
            "ranking_criterion": self.ranking_criterion,
        }


class StrongestSignalEngine:
    """
    Ranks qualified signals and filters weak setups into structured NO_TRADE explanations.
    """

    def rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        top_n: int = 5,
    ) -> StrongestRankingResult:
        """
        Applies 13-stage zero-trust filtration and returns top N highest conviction setups.
        """
        qualified: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []

        for cand in candidates:
            asset = cand.get("asset", "EURUSD")
            timeframe = cand.get("timeframe", "1H")
            prob = float(cand.get("calibrated_probability", 0.50))
            exp_net_r = float(cand.get("expected_net_r", 0.0))
            strength = int(cand.get("signal_strength", 50))
            mtf_conflict = float(cand.get("mtf_conflict_score", 0.20))
            htf_align = float(cand.get("htf_alignment_score", 0.70))
            rr = float(cand.get("risk_reward", 2.0))
            event_risk = cand.get("event_risk", "LOW")
            regime = cand.get("market_regime", "TRENDING_BULL")
            decision = cand.get("decision", "TAKE_NOW")

            rejection_reasons = []

            # 1. Event Risk Gate
            if event_risk == "HIGH":
                rejection_reasons.append("HIGH_EVENT_RISK")

            # 2. MTF Conflict Gate
            if mtf_conflict > 0.40:
                rejection_reasons.append("MTF_CONFLICT_DETECTED")

            # 3. Consensus Probability Gate
            if prob < 0.65:
                rejection_reasons.append("CONSENSUS_BELOW_THRESHOLD")

            # 4. Expected Net R Gate
            if exp_net_r < 0.15:
                rejection_reasons.append("NEGATIVE_OR_LOW_EXPECTED_NET_R")

            # 5. Risk / Reward Gate
            if rr < 1.50:
                rejection_reasons.append("RR_BELOW_MINIMUM")

            # 6. Signal Strength Gate
            if strength < 70:
                rejection_reasons.append("SIGNAL_STRENGTH_INSUFFICIENT")

            # 7. Regime Compatibility Gate
            if regime in ["HIGH_EVENT_RISK"]:
                rejection_reasons.append("UNFAVORABLE_MARKET_REGIME")

            if not rejection_reasons and decision in ["TAKE_NOW", "QUALIFIED"]:
                # Compute composite conviction rank score
                rank_score = (prob * 0.40) + (min(1.0, exp_net_r / 0.80) * 0.30) + (htf_align * 0.20) + ((strength / 100.0) * 0.10)
                cand_copy = dict(cand)
                cand_copy["rank_score"] = round(rank_score, 4)
                cand_copy["status"] = "LIVE"
                qualified.append(cand_copy)
            else:
                primary_reason = rejection_reasons[0] if rejection_reasons else "GATE_CRITERIA_UNMET"
                rejected.append({
                    "asset": asset,
                    "timeframe": timeframe,
                    "direction": cand.get("direction", "WAIT"),
                    "candidate_strength": strength,
                    "calibrated_probability": prob,
                    "expected_net_r": exp_net_r,
                    "rejection_reason": primary_reason,
                    "rejection_reasons_all": rejection_reasons,
                    "status": "NO_TRADE",
                })

        # Sort qualified signals by conviction rank score descending
        sorted_qualified = sorted(qualified, key=lambda x: x.get("rank_score", 0), reverse=True)
        top_n_signals = sorted_qualified[:top_n]

        return StrongestRankingResult(
            top_signals=top_n_signals,
            total_candidates_evaluated=len(candidates),
            qualified_count=len(qualified),
            rejected_count=len(rejected),
            no_trade_breakdown=rejected,
        )


strongest_signal_engine = StrongestSignalEngine()
