"""LLM Provider Factory with retry, exponential backoff, and automatic fallback."""

import logging
import time
from typing import Optional
from app.llm.base import BaseLLMProvider
from app.llm.gemini import GeminiProvider
from app.llm.ollama import OllamaProvider
from app.llm.openai_compat import OpenAICompatibleProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class ResilientLLMService:
    """Orchestrates primary and fallback LLM providers with automatic retry."""

    def __init__(self):
        self.providers = {
            "gemini": GeminiProvider(),
            "ollama": OllamaProvider(),
            "openai_compat": OpenAICompatibleProvider()
        }
        self.primary_name = settings.LLM_PROVIDER.lower()
        self.fallback_name = settings.FALLBACK_LLM_PROVIDER.lower()

    def get_provider(self, name: str) -> BaseLLMProvider:
        return self.providers.get(name, self.providers["gemini"])

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_retries: int = 1
    ) -> str:
        """Attempts generation with primary provider, then retries with backoff, then falls back."""
        attempt_providers = [self.primary_name]
        if self.fallback_name != self.primary_name and self.fallback_name in self.providers:
            attempt_providers.append(self.fallback_name)

        last_error = None

        for prov_name in attempt_providers:
            provider = self.get_provider(prov_name)
            logger.info(f"Attempting LLM generation using provider: {prov_name}")

            for attempt in range(max_retries + 1):
                try:
                    return provider.generate_text(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=temperature
                    )
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"LLM Provider {prov_name} attempt {attempt + 1} failed: {e}"
                    )
                    if attempt < max_retries:
                        time.sleep(0.5 * (attempt + 1))  # Short backoff on transient 503/429

        raise RuntimeError(f"All configured LLM providers failed. Last error: {last_error}")


# Global instance
llm_service = ResilientLLMService()
