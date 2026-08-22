from dataclasses import dataclass
from typing import Any

from app.logs.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AIValidationResult:
    decision: str = "APPROVE"
    confidence_adjustment: float = 0.0
    reasoning: str = ""
    risk_summary: str = ""
    alternative_scenario: str = ""

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "confidence_adjustment": self.confidence_adjustment,
            "reasoning": self.reasoning,
            "risk_summary": self.risk_summary,
            "alternative_scenario": self.alternative_scenario,
        }


class AIValidationLayer:
    def __init__(self, min_confidence: float = 0.50):
        self.min_confidence = min_confidence

    def validate(self, signal: dict, market_data: dict[str, Any] | None = None) -> AIValidationResult:
        direction = signal.get("direction", "WAIT")
        confidence = signal.get("confidence", 0.5)
        if isinstance(confidence, (int, float)):
            pass
        else:
            confidence = 0.5

        if direction == "WAIT" or confidence < self.min_confidence:
            return AIValidationResult(
                decision="REJECT",
                reasoning=f"Signal direction is {direction} or confidence {confidence:.2f} below minimum {self.min_confidence}",
                risk_summary="Signal does not meet minimum confidence threshold",
                alternative_scenario="Wait for stronger confirmation",
            )

        issues = []
        positives = []

        if confidence < 0.65:
            issues.append(f"Confidence {confidence:.2f} is below ideal threshold of 0.65")
        else:
            positives.append(f"Confidence {confidence:.2f} meets threshold")

        if not signal.get("stop_loss_suggestion"):
            issues.append("No stop loss defined")
        if not signal.get("take_profit_suggestion"):
            issues.append("No take profit defined")

        if direction == "BUY":
            positives.append("Long direction aligns with bullish bias")
            alternative = "Consider partial position if uncertain"
        else:
            positives.append("Short direction aligns with bearish bias")
            alternative = "Consider partial position if uncertain"

        if issues:
            adjustment = -0.05 * len(issues)
        else:
            adjustment = 0.05 if confidence < 0.8 else 0.0

        risk_parts = []
        if signal.get("risk_level") == "HIGH":
            risk_parts.append("High risk level detected")
            adjustment -= 0.05
        elif signal.get("risk_level") == "MEDIUM":
            risk_parts.append("Medium risk - standard position sizing")
        else:
            risk_parts.append("Low risk profile")

        sl = signal.get("stop_loss_suggestion")
        price = signal.get("price") or signal.get("entry_zone", [0])[0]
        if sl and price:
            risk_pct = abs(price - sl) / price * 100
            risk_parts.append(f"Risk per trade: {risk_pct:.2f}%")
            if risk_pct > 2.0:
                issues.append(f"Risk per trade ({risk_pct:.2f}%) exceeds 2%")
                adjustment -= 0.05

        decision = "APPROVE"
        if len(issues) >= 3:
            decision = "REJECT"
        elif len(issues) >= 1:
            decision = "REDUCE_CONFIDENCE"

        if decision == "REDUCE_CONFIDENCE" and confidence >= 0.8:
            decision = "APPROVE"
        if decision == "APPROVE" and confidence > 0.7 and adjustment > 0:
            decision = "INCREASE_CONFIDENCE"

        reasoning = " | ".join(positives + issues) if positives or issues else "Signal passes validation checks"

        return AIValidationResult(
            decision=decision,
            confidence_adjustment=round(adjustment, 3),
            reasoning=reasoning,
            risk_summary="; ".join(risk_parts),
            alternative_scenario=alternative,
        )


ai_validation_layer = AIValidationLayer()
