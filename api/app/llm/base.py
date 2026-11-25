"""Base LLM Provider Interface."""

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMProvider(ABC):
    """Abstract class defining the contract for all LLM providers."""

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048
    ) -> str:
        """Generates a text completion synchronously or raises an exception on failure."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is configured and reachable."""
        pass
