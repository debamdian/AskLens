"""OpenAI-Compatible Free Endpoint Provider (Groq, OpenRouter, etc.)."""

from typing import Optional
import httpx
from app.llm.base import BaseLLMProvider
from app.core.config import settings


class OpenAICompatibleProvider(BaseLLMProvider):
    """Provider for any OpenAI-compatible completions endpoint."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.base_url = (base_url or settings.OPENAI_COMPAT_BASE_URL).rstrip("/")
        self.api_key = api_key or settings.OPENAI_COMPAT_API_KEY
        self.model = model or settings.OPENAI_COMPAT_MODEL or "openai/gpt-oss-120b"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"OpenAI-compatible LLM error: {e}") from e
