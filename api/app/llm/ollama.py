"""Ollama Local Model Provider (e.g. qwen2.5-coder or llama3.1)."""

from typing import Optional
import httpx
from app.llm.base import BaseLLMProvider
from app.core.config import settings


class OllamaProvider(BaseLLMProvider):
    """Local Ollama LLM provider running completely on-device without cloud calls."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL or "qwen2.5-coder:7b"

    def is_available(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048
    ) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(f"{self.base_url}/api/generate", json=payload)
                res.raise_for_status()
                data = res.json()
                return data.get("response", "")
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {e}") from e
