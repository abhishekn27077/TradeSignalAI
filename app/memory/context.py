import json
from typing import Any


class ContextManager:
    """
    Manages the formatting and truncation of prompt contexts.
    Ensures that context doesn't exceed LLM token limits.
    """
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        
    def build_context(self, system_prompt: str, historical_data: list[Any], recent_events: list[Any]) -> str:
        """
        Builds the final prompt string, managing the inclusion of historical data based on token limits.
        """
        # Very naive implementation: Just JSON dump everything.
        # In production, this would use a tokenizer (e.g., tiktoken) to accurately measure and truncate.
        context = f"SYSTEM_PROMPT:\n{system_prompt}\n\n"
        
        hist_str = json.dumps(historical_data, default=str)
        # Naive truncation
        if len(hist_str) > self.max_tokens * 2: # Very rough heuristic
            hist_str = hist_str[:self.max_tokens * 2] + "... [TRUNCATED]"
            
        context += f"MARKET_DATA:\n{hist_str}\n\n"
        
        event_str = json.dumps(recent_events, default=str)
        context += f"RECENT_EVENTS:\n{event_str}\n"
        
        return context

context_manager = ContextManager()
