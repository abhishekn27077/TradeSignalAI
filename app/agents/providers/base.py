from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class LLMResponse(BaseModel):
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM Providers (OpenAI, Anthropic, OpenRouter).
    Ensures that switching between providers requires zero changes to Agent logic.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def generate_response(self, prompt: str, system_prompt: str = "", tools: list[dict[str, Any]] = None) -> LLMResponse:
        """
        Sends a prompt to the LLM and returns the structured response.
        """
