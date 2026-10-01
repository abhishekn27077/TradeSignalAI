from typing import Any

from app.agents.providers.base import BaseLLMProvider
from app.agents.providers.openrouter import OpenRouterProvider
from app.agents.providers.openai_provider import OpenAIProvider
from app.config.settings import get_settings
from app.logs.logger import get_logger

logger = get_logger(__name__)


class ModelRouter:
    def __init__(self):
        self._providers: dict[str, BaseLLMProvider] = {}

    def register(self, name: str, provider: BaseLLMProvider):
        self._providers[name] = provider
        logger.info(f"LLM provider registered: {name}")

    async def generate(
        self, prompt: str, target: str | None = None, context: list[dict[str, Any]] | None = None, **kwargs
    ) -> str | None:
        if not self._providers:
            logger.warning("No LLM providers registered")
            return None

        # Map roles to specific providers if configured, otherwise default to openrouter
        role_to_provider = {
            "NEWS_ANALYST": "openrouter",
            "MACRO_ANALYST": "openrouter",
            "SENTIMENT_ANALYST": "openrouter",
            "RISK_ANALYST": "openrouter",
            "SYNTHESIS_ANALYST": "openrouter"
        }

        resolved_target = role_to_provider.get(target, target)

        if resolved_target and resolved_target in self._providers:
            provider = self._providers[resolved_target]
        else:
            # Default to openrouter if available, else first registered
            provider = self._providers.get("openrouter", list(self._providers.values())[0])

        # Strict mapping to ensure only guaranteed free models are used, 
        # as requested. openrouter/free automatically routes to the best available free model.
        if provider.name == "openrouter":
            kwargs["model"] = "openrouter/free"

        try:
            if hasattr(provider, "health_check"):
                healthy = await provider.health_check()
                if not healthy:
                    logger.warning(f"Provider {target or 'default'} unhealthy, trying fallback")
                    for fallback_name, fallback in self._providers.items():
                        if fallback is provider:
                            continue
                        if hasattr(fallback, "health_check") and not await fallback.health_check():
                            continue
                        result = await fallback.generate(prompt, context, **kwargs)
                        if result:
                            return result
                    return None
            
            result = await provider.generate(prompt, context, **kwargs)
            if not result:
                # Silently fallback without spamming the console
                for fallback_name, fallback in self._providers.items():
                    if fallback is provider:
                        continue
                    if hasattr(fallback, "health_check") and not await fallback.health_check():
                        continue
                    fallback_result = await fallback.generate(prompt, context, **kwargs)
                    if fallback_result:
                        return fallback_result
                return None
            return result
        except Exception as e:
            logger.warning(f"LLM generation failed: {e}")
            return None

    async def health_check_all(self) -> dict[str, bool]:
        results = {}
        for name, provider in self._providers.items():
            try:
                if hasattr(provider, "health_check"):
                    results[name] = await provider.health_check()
                else:
                    results[name] = True
            except Exception:
                results[name] = False
        return results

    async def health_check_provider(self, name: str) -> bool:
        provider = self._providers.get(name)
        if not provider:
            return False
        try:
            if hasattr(provider, "health_check"):
                return await provider.health_check()
            return True
        except Exception:
            return False


model_router = ModelRouter()

try:
    from app.agents.providers.gemini_provider import GeminiProvider
    gemini_provider = GeminiProvider()
    model_router.register("gemini", gemini_provider)
except Exception as e:
    logger.warning(f"Gemini provider not available: {e}")

try:
    openrouter_provider = OpenRouterProvider()
    model_router.register("openrouter", openrouter_provider)
except Exception as e:
    logger.warning(f"OpenRouter provider not available: {e}")

try:
    openai_provider = OpenAIProvider()
    model_router.register("openai", openai_provider)
except Exception as e:
    logger.warning(f"OpenAI provider not available: {e}")

settings = get_settings()
if settings.EXECUTION_MODE == "DEMO" or settings.ENVIRONMENT == "development":
    from app.agents.providers.heuristic import HeuristicProvider
    try:
        heuristic_engine = HeuristicProvider()
        model_router.register("heuristic_engine", heuristic_engine)
    except Exception as e:
        logger.warning(f"Heuristic Engine not available: {e}")