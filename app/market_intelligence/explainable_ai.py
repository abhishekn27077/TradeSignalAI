from typing import Dict, Any

class ExplainableAI:
    """
    Generates human-readable, institutional-grade explanations for AI trading signals.
    Phase 10: Explainable AI with Consensus & Pattern Memory.
    """
    
    @staticmethod
    def generate_explanation(consensus_result: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates the structured reasoning for a trade based on the Consensus Engine output.
        """
        direction = consensus_result.get("signal", "NEUTRAL")
        confidence = consensus_result.get("confidence_score", 0.0)
        agreement = consensus_result.get("agreement_percentage", 0.0)
        breakdown = consensus_result.get("breakdown", {})
        memory_narrative = consensus_result.get("memory_narrative", "")
        
        reasons = []
        
        if direction in ["BULLISH", "BEARISH"]:
            reasons.append(f"Institutional AI Consensus generated a strong {direction} forecast with {confidence:.1f}% confidence.")
            reasons.append(f"Model Agreement is at {agreement:.1f}%.")
            
            # Breakdown
            xgb = breakdown.get("xgboost", 0.0)
            rf = breakdown.get("random_forest", 0.0)
            hgb = breakdown.get("hist_gb", 0.0)
            
            reasons.append(f"XGBoost expected return: {xgb*100:.2f}%.")
            reasons.append(f"RandomForest expected return: {rf*100:.2f}%.")
            reasons.append(f"HistGradientBoosting expected return: {hgb*100:.2f}%.")
            
            reasons.append("Historical Market Memory Output:")
            reasons.append(memory_narrative)
            
            # Additional context from current features
            regime = features.get("Regime", 0)
            regime_str = "Neutral/Ranging"
            if regime == 1:
                regime_str = "Bull Trend"
            elif regime == -1:
                regime_str = "Bear Trend"
            elif regime == 2:
                regime_str = "High Volatility Expansion"
                
            reasons.append(f"Current Market Regime: {regime_str}.")
            
            if features.get("FVG_Bullish", 0) == 1 and direction == "BULLISH":
                reasons.append("Structure alignment: Bullish Fair Value Gap present.")
            if features.get("FVG_Bearish", 0) == 1 and direction == "BEARISH":
                reasons.append("Structure alignment: Bearish Fair Value Gap present.")
                
        else:
            reasons.append("Consensus Models are NEUTRAL. Not enough directional agreement or expected volatility.")

        return {
            "why_direction": "\n".join(reasons),
            "regime_context": features.get("Regime", 0),
            "consensus_data": breakdown
        }

xai_engine = ExplainableAI()
