"""Google Gemini Provider using official google-genai library."""

import os
from typing import Optional
from app.llm.base import BaseLLMProvider
from app.core.config import settings

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider using free tier API key."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self.model_name = model or settings.GEMINI_MODEL or "gemini-3.5-flash"
        self._client = None
        if self.api_key and genai is not None:
            self._client = genai.Client(api_key=self.api_key)

    def is_available(self) -> bool:
        return bool(self.api_key and self._client is not None)

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048
    ) -> str:
        if not self._client:
            raise RuntimeError("Gemini API key is missing or google-genai library is not installed.")

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_prompt if system_prompt else None
        )

        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config
        )
        return response.text or ""
