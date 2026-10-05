"""Typed application settings loaded from environment variables."""

from functools import lru_cache

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
    # Optional legacy HS256 secret for local JWT verification. Modern Supabase
    # projects can leave this empty and use Supabase Auth token verification.
    supabase_jwt_secret: str = ""

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:4b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""

    return Settings()


settings = get_settings()
