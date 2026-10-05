"""FastAPI dependency for protected routes."""

from fastapi import Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth.auth_service import AuthenticatedUser, AuthenticationError, verify_access_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    """Resolve the current Supabase user from an HTTP Bearer token."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Missing bearer token")
    return await run_in_threadpool(verify_access_token, credentials.credentials)
