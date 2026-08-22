from typing import Any
import os

import httpx

from app.agents.providers.base import BaseLLMProvider, LLMResponse
from app.config.settings import get_settings
from app.logs.logger import get_logger
from dotenv import load_dotenv

load_dotenv()
logger = get_logger(__name__)


class GeminiProvider(BaseLLMProvider):
    @property
    def name(self) -> str:
        return "gemini"

    def __init__(self):
        self._settings = get_settings()
        # Read from environment directly since it was just added to .env and might not be in settings model yet
        self._api_key = os.getenv("GEMINI_API_KEY")
        self._base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
        self._model = "gemini-1.5-flash"
        self._client = httpx.AsyncClient(timeout=30.0)
        self._healthy = False

    async def health_check(self) -> bool:
        if not self._api_key:
            self._healthy = False
            return False
            
        try:
            health_url = f"{self._base_url}/models"
            res = await self._client.get(
                health_url, 
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=5.0
            )
            self._healthy = res.status_code == 200
            return self._healthy
        except Exception:
            self._healthy = False
            return False

    async def generate(self, prompt: str, context: list[dict[str, Any]] | None = None, **kwargs) -> str | None:
        if not self._api_key:
            logger.warning("Gemini API key not configured")
            return None

        messages = []
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": prompt})

        max_retries = kwargs.get("max_retries", 3)
        for attempt in range(max_retries):
            try:
                json_body = {
                    "model": kwargs.get("model", self._model),
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 1000),
                }

                res = await self._client.post(
                    f"{self._base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json=json_body,
                    timeout=kwargs.get("timeout", 60.0)
                )
                if res.status_code == 200:
                    data = res.json()
                    self._healthy = True
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "")
                elif res.status_code >= 500 or res.status_code == 429:
                    logger.warning(f"Gemini server error ({res.status_code}), attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        import asyncio
                        await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    logger.warning(f"Gemini returned {res.status_code}: {res.text}")
                    return None
            except httpx.TimeoutException:
                logger.warning(f"Gemini timeout, attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                continue
            except Exception as e:
                logger.warning(f"Gemini request error: {e}")
                return None

        logger.warning(f"Gemini failed after {max_retries} attempts")
        return None

    async def generate_response(self, prompt: str, system_prompt: str = "", tools: list[dict[str, Any]] = None) -> LLMResponse:
        context = []
        if system_prompt:
            context.append({"role": "system", "content": system_prompt})
        content = await self.generate(prompt, context=context)
        return LLMResponse(
            content=content or "",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
        )

    async def close(self):
        await self._client.aclose()
