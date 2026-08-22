from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)


class TradeQualityEngine:
    def __init__(self, min_threshold: int = 60):
        self.min_threshold = min_threshold
        self.weights = {
            "trend": 12,
            "momentum": 10,
            "volatility": 8,
            "volume": 8,
            "liquidity": 8,
            "market_structure": 12,
            "support_resistance": 8,
            "ai_agreement": 14,
            "risk_reward": 12,
            "filters": 8,
        }

    def evaluate(self, context: dict[str, Any]) -> tuple[int, str, dict[str, Any]]:
        score = 0
        breakdown = {}

        trend_score = 0
        if context.get("trend_aligned", False):
            trend_score = self.weights["trend"]
        elif context.get("trend_neutral", False):
            trend_score = self.weights["trend"] // 2
        score += trend_score
        breakdown["trend"] = trend_score

        momentum_score = 0
        mom_val = context.get("momentum_strength", 50)
        if isinstance(mom_val, (int, float)):
            momentum_score = int(self.weights["momentum"] * min(mom_val / 100, 1.0))
        score += momentum_score
        breakdown["momentum"] = momentum_score

        vol_val = context.get("volatility_quality", 50)
        vol_score = 0
        if isinstance(vol_val, (int, float)):
            if vol_val >= 70:
                vol_score = self.weights["volatility"]
            elif vol_val >= 50:
                vol_score = self.weights["volatility"] // 2
        score += vol_score
        breakdown["volatility"] = vol_score

        volume_score = 0
        if context.get("volume_confirmed", False):
            volume_score = self.weights["volume"]
        score += volume_score
        breakdown["volume"] = volume_score

        liquidity_score = 0
        if context.get("liquidity_sweep", False):
            liquidity_score = self.weights["liquidity"]
        score += liquidity_score
        breakdown["liquidity"] = liquidity_score

        ms_score = 0
        if context.get("bos", False):
            ms_score += 6
        if context.get("choch", False):
            ms_score += 6
        ms_score = min(self.weights["market_structure"], ms_score)
        score += ms_score
        breakdown["market_structure"] = ms_score

        sr_score = 0
        if context.get("at_support", False) or context.get("at_resistance", False):
            sr_score = self.weights["support_resistance"]
        score += sr_score
        breakdown["support_resistance"] = sr_score

        ai_val = context.get("ai_agreement", 0)
        if isinstance(ai_val, (int, float)):
            ai_score = int(self.weights["ai_agreement"] * min(ai_val / 100, 1.0))
        else:
            ai_score = 0
        score += ai_score
        breakdown["ai_agreement"] = ai_score

        rr = context.get("risk_reward", 0)
        rr_score = 0
        if isinstance(rr, (int, float)):
            if rr >= 3.0:
                rr_score = self.weights["risk_reward"]
            elif rr >= 2.0:
                rr_score = int(self.weights["risk_reward"] * 0.7)
            elif rr >= 1.5:
                rr_score = int(self.weights["risk_reward"] * 0.4)
        score += rr_score
        breakdown["risk_reward"] = rr_score

        filter_score = self.weights["filters"]
        if context.get("high_impact_news", False):
            filter_score -= 4
        if context.get("bad_session", False):
            filter_score -= 4
        if context.get("high_spread", False):
            filter_score -= 3
        filter_score = max(0, filter_score)
        score += filter_score
        breakdown["filters"] = filter_score

        score = max(0, min(100, score))
        grade = self.get_grade(score)
        verdict = "ACCEPT" if score >= self.min_threshold else "REJECT"

        return score, grade, {
            "score": score,
            "grade": grade,
            "verdict": verdict,
            "breakdown": breakdown,
            "min_threshold": self.min_threshold,
        }

    def get_grade(self, score: int) -> str:
        if score >= 95:
            return "A+"
        if score >= 85:
            return "A"
        if score >= 75:
            return "B+"
        if score >= 65:
            return "B"
        if score >= 50:
            return "C"
        return "D"

    def evaluate_from_signal(self, signal: dict, context: dict[str, Any] | None = None) -> tuple[int, str, dict[str, Any]]:
        if context is None:
            context = {}
        context.setdefault("trend_aligned", signal.get("direction") in ("BUY", "SELL"))
        context.setdefault("momentum_strength", signal.get("confidence", 0.5) * 100 if isinstance(signal.get("confidence"), (int, float)) else 50)
        context.setdefault("volatility_quality", 60)
        context.setdefault("volume_confirmed", True)
        context.setdefault("risk_reward", 2.0)
        ai_val = signal.get("ai_confidence", signal.get("confidence", 0.5))
        if isinstance(ai_val, (int, float)):
            context.setdefault("ai_agreement", ai_val * 100 if ai_val <= 1 else ai_val)
        return self.evaluate(context)


trade_quality_engine = TradeQualityEngine()
