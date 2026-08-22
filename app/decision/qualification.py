from typing import Any


class TradeQualificationSystem:
    def qualify(self, factors: dict[str, Any]) -> dict[str, Any]:
        """
        Calculates Trade Qualification Score (0-100) and assigns Trade Grade (A+, A, B, C, D)
        """
        conf = factors.get("confidence", 0.0)
        rr = factors.get("rr_ratio", 1.0)
        session = factors.get("session_score", 0.5)
        entry = factors.get("entry_quality_score", 0.5)
        agree = factors.get("model_agreement_pct", 0.0)

        # Weighted score out of 100
        score = (
            (conf * 30) + 
            (min(rr / 3.0, 1.0) * 20) + # Cap RR contribution at 3.0
            (session * 10) +
            (entry * 20) +
            (agree * 20)
        )
        
        # Determine Grade
        if score >= 90:
            grade = "A+"
        elif score >= 80:
            grade = "A"
        elif score >= 70:
            grade = "B"
        elif score >= 50:
            grade = "C"
        else:
            grade = "D"
            
        # Is approved logic: Strictly A+ or A
        is_approved = grade in ("A+", "A")
        
        return {
            "qualification_score": round(score, 2),
            "trade_grade": grade,
            "is_approved": is_approved
        }

trade_qualification_system = TradeQualificationSystem()
