"""Lazy Supabase clients used by repositories and authentication services."""

from functools import lru_cache
from typing import Any

from app.core.config import settings


class SupabaseServiceError(RuntimeError):
    """Raised when Supabase cannot be configured or reached."""


class SupabaseSchemaError(SupabaseServiceError):
    """Raised when the required public application tables are absent."""


def _create_client(url: str, key: str) -> Any:
    """Import the optional SDK lazily so the backend can start without secrets."""

    try:
        from supabase import create_client
    except ImportError as exc:  # pragma: no cover - exercised in deployment
        raise SupabaseServiceError("The supabase package is not installed") from exc

    try:
        return create_client(url, key)
    except Exception as exc:  # pragma: no cover - provider-specific failures
        raise SupabaseServiceError("Unable to create the Supabase client") from exc


@lru_cache(maxsize=1)
def get_supabase_client() -> Any:
    """Return the cached service-role client for server-side data operations."""

    if not settings.supabase_url or not settings.supabase_service_key:
        raise SupabaseServiceError("Supabase service credentials are not configured")
    return _create_client(settings.supabase_url, settings.supabase_service_key)


@lru_cache(maxsize=1)
def get_supabase_auth_client() -> Any:
    """Return a cached anon client for sign-up and password sign-in."""

    if not settings.supabase_url or not settings.supabase_anon_key:
        raise SupabaseServiceError("Supabase Auth credentials are not configured")
    return _create_client(settings.supabase_url, settings.supabase_anon_key)
