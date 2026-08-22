import json
import logging
from typing import Optional

from app.agents.providers.router import model_router
from app.intelligence.schemas import RiskAssessment

logger = logging.getLogger(__name__)

class LLMRiskAnalyst:
    """
    Phase 11: LLM as a Risk Analyst
    Dedicated task: "Find reasons why this trade should NOT be taken."
    """
    
    async def analyze_risk(self, asset: str, quant_signal: str, kronos_signal: str, 
                           regime: str, news_sentiment: str, macro_context: str, 
                           event_risk: str) -> Optional[RiskAssessment]:
        
        prompt = f"""
        You are the Master Risk Analyst for {asset}.
        
        Your ONLY job is to find reasons why this trade should NOT be taken (Devil's Advocate).
        
        Inputs:
        - Quant Signal: {quant_signal}
        - Kronos Foundation Model: {kronos_signal}
        - Regime: {regime}
        - News Sentiment: {news_sentiment}
        - Macro Context: {macro_context}
        - Event Risk: {event_risk}
        
        Task:
        1. List specific risk flags (e.g. major economic event approaching, countertrend setup, negative news).
        2. Determine if these risks warrant a full VETO (veto_trade: true or false).
        """
        
        try:
            response_text = await model_router.generate(
                prompt=prompt,
                target="RISK_ANALYST",
                response_format={"type": "json_schema", "json_schema": {"name": "RiskAssessment", "schema": RiskAssessment.model_json_schema()}}
            )
            
            if response_text:
                analysis_dict = json.loads(response_text)
                return RiskAssessment(**analysis_dict)
            else:
                logger.warning("RISK_ANALYST returned no response.")
                return None
        except Exception as e:
            logger.error(f"Error in LLM Risk Analyst: {e}")
            return None

llm_risk_analyst = LLMRiskAnalyst()
