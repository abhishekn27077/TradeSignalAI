from dataclasses import dataclass

from app.logs.logger import get_logger

logger = get_logger(__name__)


@dataclass
class HoldingDecision:
    action: str = "HOLD"
    reason: str = ""
    extend_minutes: int = 0
    remaining_minutes: int = 0

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "reason": self.reason,
            "extend_minutes": self.extend_minutes,
            "remaining_minutes": self.remaining_minutes,
        }


class AdaptiveHoldingLogic:
    def __init__(self):
        self.fixed_hold_minutes: int = 60
        self.forex_min_hold_minutes: int = 60
        self.forex_max_hold_minutes: int = 240
        self.extend_window_minutes: int = 30
        self.max_extend_minutes: int = 60

    def evaluate(
        self,
        direction: str,
        asset_type: str,
        elapsed_minutes: int,
        trend_valid: bool | None = None,
        momentum_valid: bool | None = None,
        ai_agrees: bool | None = None,
        risk_acceptable: bool | None = None,
    ) -> HoldingDecision:
        if asset_type == "forex":
            return self._evaluate_forex_mode(
                direction, elapsed_minutes, trend_valid, momentum_valid, ai_agrees, risk_acceptable
            )
        return self._evaluate_fixed_time_mode(elapsed_minutes)

    def _evaluate_fixed_time_mode(self, elapsed_minutes: int) -> HoldingDecision:
        remaining = max(0, self.fixed_hold_minutes - elapsed_minutes)
        if elapsed_minutes >= self.fixed_hold_minutes:
            return HoldingDecision(
                action="CLOSE",
                reason=f"Fixed holding time of {self.fixed_hold_minutes} minutes reached",
                remaining_minutes=0,
            )
        return HoldingDecision(
            action="HOLD",
            reason=f"Holding for {elapsed_minutes}/{self.fixed_hold_minutes} minutes",
            remaining_minutes=remaining,
        )

    def _evaluate_forex_mode(
        self,
        direction: str,
        elapsed_minutes: int,
        trend_valid: bool | None,
        momentum_valid: bool | None,
        ai_agrees: bool | None,
        risk_acceptable: bool | None,
    ) -> HoldingDecision:
        if elapsed_minutes < self.forex_min_hold_minutes:
            remaining = self.forex_min_hold_minutes - elapsed_minutes
            return HoldingDecision(
                action="HOLD",
                reason=f"Minimum hold of {self.forex_min_hold_minutes} minutes not yet reached ({elapsed_minutes}m elapsed)",
                extend_minutes=0,
                remaining_minutes=remaining,
            )

        if elapsed_minutes >= self.forex_max_hold_minutes:
            return HoldingDecision(
                action="CLOSE",
                reason=f"Maximum holding time of {self.forex_max_hold_minutes} minutes reached",
                remaining_minutes=0,
            )

        extend_reasons = []
        close_reasons = []

        if trend_valid is True:
            extend_reasons.append("Trend still valid")
        elif trend_valid is False:
            close_reasons.append("Trend reversed")

        if momentum_valid is True:
            extend_reasons.append("Momentum still valid")
        elif momentum_valid is False:
            close_reasons.append("Momentum weakened")

        if ai_agrees is True:
            extend_reasons.append("AI still agrees")
        elif ai_agrees is False:
            close_reasons.append("AI disagrees now")

        if risk_acceptable is True:
            extend_reasons.append("Risk acceptable")
        elif risk_acceptable is False:
            close_reasons.append("Risk no longer acceptable")

        if close_reasons and len(close_reasons) >= 2:
            return HoldingDecision(
                action="CLOSE",
                reason="; ".join(close_reasons),
                remaining_minutes=0,
            )

        if extend_reasons and len(extend_reasons) >= 2:
            extend = self.extend_window_minutes
            new_elapsed = elapsed_minutes + extend
            if new_elapsed >= self.forex_max_hold_minutes:
                extend = self.forex_max_hold_minutes - elapsed_minutes
            remaining = self.forex_max_hold_minutes - (elapsed_minutes + extend)
            return HoldingDecision(
                action="EXTEND",
                reason="; ".join(extend_reasons),
                extend_minutes=extend,
                remaining_minutes=max(0, remaining),
            )

        if extend_reasons and not close_reasons:
            extend = self.extend_window_minutes
            return HoldingDecision(
                action="HOLD",
                reason="Borderline conditions - monitoring",
                extend_minutes=0,
                remaining_minutes=self.forex_max_hold_minutes - elapsed_minutes,
            )

        return HoldingDecision(
            action="CLOSE",
            reason="Insufficient conditions to continue holding: " + ("; ".join(close_reasons) if close_reasons else "no confirming factors"),
            remaining_minutes=0,
        )


adaptive_holding = AdaptiveHoldingLogic()
