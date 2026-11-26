"""Application Configuration using Pydantic Settings."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Locate the root .env file
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_PATH = ROOT_DIR / ".env"


class Settings(BaseSettings):
    """Central application settings."""
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # PostgreSQL Database settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "asklens"
    POSTGRES_USER: str = "asklens_admin"
    POSTGRES_PASSWORD: str = "asklens_secure_password_123"

    # Read-only warehouse user settings
    POSTGRES_READONLY_USER: str = "warehouse_readonly"
    POSTGRES_READONLY_PASSWORD: str = "readonly_secure_password_123"

    # Full connection URLs
    DATABASE_URL: Optional[str] = None
    WAREHOUSE_READONLY_URL: Optional[str] = None

    # Query Safety Limits
    STATEMENT_TIMEOUT_MS: int = 5000
    MAX_ROW_LIMIT: int = 500
    MAX_QUERY_COST: float = 50000.0

    # LLM Settings
    LLM_PROVIDER: str = "gemini"  # gemini | ollama | openai_compat
    FALLBACK_LLM_PROVIDER: str = "ollama"

    # Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.5-flash"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5-coder:7b"

    # OpenAI-Compatible (Groq / OpenRouter)
    OPENAI_COMPAT_BASE_URL: str = "https://api.groq.com/openai/v1"
    OPENAI_COMPAT_API_KEY: Optional[str] = None
    OPENAI_COMPAT_MODEL: str = "openai/gpt-oss-120b"

    # Security
    JWT_SECRET: str = "super_secret_jwt_key_change_me_in_production_min_32_chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # STT Whisper
    WHISPER_MODEL: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    @property
    def sync_warehouse_readonly_url(self) -> str:
        """PostgreSQL connection string for synchronous psycopg2 execution."""
        if self.WAREHOUSE_READONLY_URL:
            return self.WAREHOUSE_READONLY_URL
        return f"postgresql://{self.POSTGRES_READONLY_USER}:{self.POSTGRES_READONLY_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def sync_admin_url(self) -> str:
        """Admin connection string for migrations, schema crawling, and seeding."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
