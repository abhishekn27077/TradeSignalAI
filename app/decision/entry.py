from typing import Any


class EntryQualityAnalyzer:
    def analyze(self, symbol: str, direction: str, current_price: float, forecast_data: dict[str, Any]) -> dict[str, Any]:
        """
        Evaluate current price, late entry risk, pullback probability.
        For stub purposes, returns a mock quality score.
        """
        return {
            "entry_quality_score": 0.85,
            "late_entry_risk": "Low",
            "pullback_probability": 0.25,
            "breakout_probability": 0.60
        }

entry_quality_analyzer = EntryQualityAnalyzer()
