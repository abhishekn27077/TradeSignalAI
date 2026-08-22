import logging

logger = logging.getLogger(__name__)

class NoTradeEngine:
    """
    Phase 12: No-Trade Engine
    A trade should be rejected if specific contextual or quantitative thresholds are violated.
    """
    
    def evaluate(self, expected_move: float, event_risk: str, model_agreement: float,
                 contradiction_score: float, veto_flag: bool) -> dict:
        
        reasons = []
        
        if expected_move <= 0.001:  # Assuming 0.1% transaction cost minimum
            reasons.append("Expected move <= transaction cost.")
            
        if event_risk == "CRITICAL":
            reasons.append("Critical event risk imminent.")
            
        if model_agreement < 0.60:
            reasons.append("Model disagreement is extreme.")
            
        if contradiction_score > 0.5:
            reasons.append("LLM/context layer detects severe contradiction.")
            
        if veto_flag:
            reasons.append("LLM Risk Analyst vetoed the trade.")
            
        if len(reasons) > 0:
            return {
                "decision": "NO_TRADE",
                "reasons": reasons
            }
            
        return {
            "decision": "PROCEED",
            "reasons": []
        }

no_trade_engine = NoTradeEngine()
