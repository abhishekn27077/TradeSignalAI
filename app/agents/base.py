from typing import Any

from app.agents.prompts import get_prompt
from app.agents.providers.router import model_router
from app.agents.types import AgentRole
from app.logs.logger import get_logger

logger = get_logger(__name__)


class BaseAIAgent:
    def __init__(self, agent_id: str, role: AgentRole, context_events: list[dict[str, Any]] | None = None):
        self.agent_id = agent_id
        self.role = role
        self.context_events = context_events or []

    async def analyze(self, data: dict[str, Any], context_events: list[str] | None = None) -> dict[str, Any]:
        prompt_template = get_prompt(self.role.value if hasattr(self.role, 'value') else str(self.role))
        if not prompt_template:
            return {"agent": self.agent_id, "signal": "HOLD", "confidence": 0.0, "reasoning": f"No prompt for role {self.role}"}

        prompt = f"{prompt_template}\n\nInput Data: {data}"
        try:
            response = await model_router.generate(prompt=prompt, target="openrouter")
            if response:
                import json
                try:
                    # If response is an object with content attribute
                    content = response.content if hasattr(response, "content") else response
                    
                    # LLMs sometimes output markdown JSON blocks, clean it
                    if isinstance(content, str):
                        content = content.strip()
                        if content.startswith("```json"):
                            content = content.replace("```json", "", 1).rstrip("```")
                        elif content.startswith("```"):
                            content = content.replace("```", "", 1).rstrip("```")

                    parsed = json.loads(content)
                    
                    # Merge base fields with all parsed fields for detailed reasoning
                    result = {
                        "agent": self.agent_id,
                        "signal": parsed.get("signal", "HOLD"),
                        "confidence": parsed.get("confidence", 0.5),
                        "reasoning": parsed.get("reason", content)
                    }
                    result.update(parsed) # Inject all specific JSON keys (regime, liquidity, etc.)
                    return result
                    
                except Exception:
                    return {"agent": self.agent_id, "signal": "HOLD", "confidence": 0.5, "reasoning": str(response)}
            return {"agent": self.agent_id, "signal": "HOLD", "confidence": 0.0, "reasoning": "No response from LLM"}
        except Exception as e:
            logger.warning(f"Agent {self.agent_id} analysis failed: {e}")
            return {"agent": self.agent_id, "signal": "HOLD", "confidence": 0.0, "reasoning": str(e)}