from typing import List, Dict, Any
from app.intelligence.schemas import ContradictionAssessment

class ContradictionDetector:
    """
    Phase 10: Contradiction Detector
    Detects if the quant models and market context are heavily contradicting each other.
    """
    
    def detect_contradictions(self, quant_signal: str, kronos_signal: str, 
                              news_sentiment: str, macro_context: str, 
                              event_risk: str) -> ContradictionAssessment:
        
        reasons = []
        contradiction_score = 0.0
        
        signals = [quant_signal, kronos_signal]
        contexts = [news_sentiment, macro_context]
        
        # Normalize everything to BULLISH, BEARISH, NEUTRAL
        normalized_signals = []
        for s in signals:
            s_upper = s.upper() if isinstance(s, str) else ""
            if "BUY" in s_upper or "BULLISH" in s_upper:
                normalized_signals.append("BULLISH")
            elif "SELL" in s_upper or "BEARISH" in s_upper:
                normalized_signals.append("BEARISH")
            else:
                normalized_signals.append("NEUTRAL")
                
        # Are quants aligned?
        quants_bullish = normalized_signals.count("BULLISH")
        quants_bearish = normalized_signals.count("BEARISH")
        
        quant_consensus = "NEUTRAL"
        if quants_bullish > 0 and quants_bearish == 0:
            quant_consensus = "BULLISH"
        elif quants_bearish > 0 and quants_bullish == 0:
            quant_consensus = "BEARISH"
            
        # Is context aligned with quants?
        if quant_consensus == "BULLISH" and ("BEARISH" in contexts):
            reasons.append("Quant models are BULLISH but Market Context has BEARISH elements.")
            contradiction_score += 0.5
            
        if quant_consensus == "BEARISH" and ("BULLISH" in contexts):
            reasons.append("Quant models are BEARISH but Market Context has BULLISH elements.")
            contradiction_score += 0.5
            
        if event_risk in ["HIGH", "CRITICAL"]:
            reasons.append(f"Event risk is {event_risk}, making quant signals unreliable.")
            contradiction_score += 0.5
            
        agreement_score = max(0.0, 1.0 - contradiction_score)
        
        return ContradictionAssessment(
            agreement_score=min(1.0, agreement_score),
            contradiction_score=min(1.0, contradiction_score),
            reasons=reasons
        )

contradiction_detector = ContradictionDetector()
