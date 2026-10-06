"""Typed application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration.

    Values are read from environment variables and, when present, the local
    ``.env`` file. Empty defaults keep the foundation runnable before external
    services are configured; real credentials must only be supplied at runtime.
    """

    app_name: str = "AI Knowledge Chatbot"
    environment: str = "development"
    debug: bool = False
    secret_key: str = ""

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    # Retained for compatibility with existing environment files. User tokens
    # are verified by Supabase Auth, which supports current signing algorithms.
    supabase_jwt_secret: str = ""

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:4b"
    # Concise grounded answers keep CPU generation responsive on the target
    # machine. Increase these only when a workflow genuinely needs it.
    ollama_num_predict: int = Field(default=256, ge=64, le=8192)
    ollama_context_window: int = Field(default=4096, ge=2048, le=32768)
    ollama_thinking: bool = False
    ollama_keep_alive: str = "10m"

    model_config = SettingsConfigDict(
        # Resolve from the repository, independent of the shell's directory.
        # Backend-specific values override the shared root environment file.
        env_file=(
            Path(__file__).resolve().parents[3] / ".env",
            Path(__file__).resolve().parents[2] / ".env",
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""

    return Settings()


settings = get_settings()
