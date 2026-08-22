from typing import Any


class DecisionExplanationGenerator:
    def generate(self, score: float, grade: str, is_approved: bool, factors: dict[str, Any]) -> dict[str, Any]:
        """
        Generates textual reasons and warnings based on factors.
        """
        reasons = []
        warnings = []
        
        conf = factors.get("confidence", 0)
        rr = factors.get("rr_ratio", 0)
        
        if conf >= 0.8:
            reasons.append(f"High forecast confidence ({conf*100:.1f}%).")
        else:
            warnings.append(f"Moderate/Low confidence ({conf*100:.1f}%).")
            
        if rr >= 2.0:
            reasons.append(f"Favorable Risk/Reward ratio ({rr:.2f}).")
        elif rr < 1.0 and rr > 0:
            warnings.append(f"Poor Risk/Reward ratio ({rr:.2f}).")
            
        session = factors.get("session_score", 0)
        if session >= 0.8:
            reasons.append("Optimal market session volume.")
            
        explanation = "Trade Approved." if is_approved else "Trade Rejected."
        if is_approved:
            explanation += f" Meets institutional criteria with a grade of {grade}."
        else:
            explanation += f" Did not meet minimum quality threshold. Grade: {grade}."

        return {
            "explanation": explanation,
            "reasons": reasons,
            "warnings": warnings,
            "rejection_reasons": warnings if not is_approved else []
        }

explanation_generator = DecisionExplanationGenerator()
