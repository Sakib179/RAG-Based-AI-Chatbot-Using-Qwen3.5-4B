"""Supabase Auth operations and access-token verification."""

from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.database.repository import create_profile, get_profile
from app.database.supabase_client import (
    SupabaseServiceError,
    get_supabase_auth_client,
    get_supabase_client,
)


class AuthenticationError(RuntimeError):
    """Raised for missing, invalid, expired, or unverifiable credentials."""


@dataclass(frozen=True)
class AuthenticatedUser:
    """Minimal identity passed from authentication to protected endpoints."""

    id: str
    email: str | None
    role: str = "user"


def _attr(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _user_from_response(user: Any) -> AuthenticatedUser:
    user_id = _attr(user, "id")
    if not user_id:
        raise AuthenticationError("Supabase returned no user identity")
    email = _attr(user, "email")
    role = "user"
    try:
        profile = get_profile(str(user_id))
        if profile and profile.get("role"):
            role = str(profile["role"])
    except SupabaseServiceError:
        # Authentication remains valid even when optional profile lookup fails.
        pass
    return AuthenticatedUser(id=str(user_id), email=email, role=role)


def _session_token(response: Any) -> str | None:
    session = _attr(response, "session")
    return _attr(session, "access_token") if session else None


def register_user(email: str, password: str) -> tuple[AuthenticatedUser, str | None]:
    """Create a Supabase Auth user and its application profile."""

    try:
        response = get_supabase_auth_client().auth.sign_up(
            {"email": email, "password": password}
        )
    except Exception as exc:
        raise AuthenticationError("Supabase registration failed") from exc
    user = _attr(response, "user")
    if not user:
        raise AuthenticationError("Supabase did not return a registered user")
    identity = AuthenticatedUser(id=str(_attr(user, "id")), email=_attr(user, "email"))
    try:
        create_profile(identity.id, identity.email)
    except SupabaseServiceError as exc:
        raise AuthenticationError("Unable to create the user profile") from exc
    return identity, _session_token(response)


def login_user(email: str, password: str) -> tuple[AuthenticatedUser, str]:
    """Sign in with Supabase Auth and return the bearer token."""

    try:
        response = get_supabase_auth_client().auth.sign_in_with_password(
            {"email": email, "password": password}
        )
    except Exception as exc:
        raise AuthenticationError("Supabase login failed") from exc
    token = _session_token(response)
    user = _attr(response, "user")
    if not token or not user:
        raise AuthenticationError("Supabase did not return a login session")
    return _user_from_response(user), token


def _verify_local_jwt(token: str) -> AuthenticatedUser | None:
    """Verify legacy HS256 Supabase tokens when a JWT secret is configured."""

    if not settings.supabase_jwt_secret:
        return None
    try:
        import jwt

        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except Exception as exc:
        raise AuthenticationError("Invalid Supabase JWT") from exc
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid Supabase JWT subject")
    email = payload.get("email")
    metadata = payload.get("user_metadata") or {}
    role = str(metadata.get("role", "user")) if isinstance(metadata, dict) else "user"
    return AuthenticatedUser(id=str(user_id), email=email, role=role)


def verify_access_token(token: str) -> AuthenticatedUser:
    """Verify a bearer token using JWT validation or Supabase Auth."""

    if not token:
        raise AuthenticationError("Missing bearer token")
    local_user = _verify_local_jwt(token)
    if local_user is not None:
        return local_user
    try:
        response = get_supabase_client().auth.get_user(token)
        user = _attr(response, "user")
        if not user:
            raise AuthenticationError("Supabase returned no authenticated user")
        return _user_from_response(user)
    except AuthenticationError:
        raise
    except Exception as exc:
        raise AuthenticationError("Supabase token verification failed") from exc
