import json
import logging
from typing import Optional

from app.agents.providers.router import model_router
from app.intelligence.schemas import MarketContextAssessment

logger = logging.getLogger(__name__)

class SynthesisEngine:
    """
    Phase 8: Multi-LLM Debate
    Synthesizes output from various engines.
    """
    
    async def synthesize(self, asset: str, quant_signal: str, kronos_signal: str, 
                         regime: str, news_sentiment: str, macro_context: str, 
                         event_risk: str) -> Optional[MarketContextAssessment]:
        
        prompt = f"""
        You are the Master Synthesis Analyst for {asset}.
        
        Synthesize the following market intelligence into a structured MarketContextAssessment.
        
        Inputs:
        - Quant Signal: {quant_signal}
        - Kronos Foundation Model: {kronos_signal}
        - Regime: {regime}
        - News Sentiment: {news_sentiment}
        - Macro Context: {macro_context}
        - Event Risk: {event_risk}
        
        Task:
        1. Determine the overall directional bias (BULLISH, BEARISH, NEUTRAL).
        2. Identify supporting factors.
        3. Identify contradicting factors.
        4. Provide a recommendation (SUPPORT, CAUTION, NO_TRADE). Do not use BUY/SELL.
        """
        
        try:
            response_text = await model_router.generate(
                prompt=prompt,
                target="SYNTHESIS_ANALYST",
                response_format={"type": "json_schema", "json_schema": {"name": "MarketContextAssessment", "schema": MarketContextAssessment.model_json_schema()}}
            )
            
            if response_text:
                analysis_dict = json.loads(response_text)
                
                # Enforce minimum scores / critical limits
                if analysis_dict.get("sentiment", 1.0) < 0.4:
                    analysis_dict["recommendation"] = "NO_TRADE"
                    analysis_dict["contradicting_factors"].append("Sentiment below 0.4 threshold.")
                if analysis_dict.get("event_risk") == "CRITICAL":
                    analysis_dict["recommendation"] = "NO_TRADE"
                    analysis_dict["contradicting_factors"].append("Critical event risk blocks trading.")
                    
                return MarketContextAssessment(**analysis_dict)
            else:
                logger.warning("SYNTHESIS_ANALYST returned no response.")
                return None
        except Exception as e:
            logger.error(f"Error in Synthesis Engine: {e}")
            return None

synthesis_engine = SynthesisEngine()
