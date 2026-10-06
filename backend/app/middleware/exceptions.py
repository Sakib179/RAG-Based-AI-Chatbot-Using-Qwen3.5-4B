"""Global exception handling for unexpected application failures."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.auth.auth_service import AuthenticationError
from app.database.supabase_client import SupabaseSchemaError, SupabaseServiceError

logger = logging.getLogger(__name__)


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Log an unexpected failure internally and return a safe public response."""

    logger.error(
        "Unhandled exception while processing %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
        },
    )


async def authentication_exception_handler(
    request: Request,
    exc: AuthenticationError,
) -> JSONResponse:
    """Return one safe response for missing, invalid, or expired credentials."""

    # AuthenticationError contains a controlled reason, never tokens or secrets.
    logger.warning("Authentication failed for %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=401,
        content={"success": False, "message": "Authentication failed"},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def supabase_service_exception_handler(
    request: Request,
    exc: SupabaseServiceError,
) -> JSONResponse:
    """Hide provider details when Supabase is unavailable or misconfigured."""

    logger.error("Supabase service failure on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content={"success": False, "message": "Supabase service unavailable"},
    )


async def supabase_schema_exception_handler(
    request: Request,
    exc: SupabaseSchemaError,
) -> JSONResponse:
    """Explain the required one-time migration without exposing provider data."""

    logger.error("Supabase schema is not ready on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "message": "Supabase database schema is not initialized. Run the initial migration.",
        },
    )


def register_exception_handlers(application: FastAPI) -> None:
    """Register global exception handlers on the FastAPI application."""

    application.add_exception_handler(Exception, unhandled_exception_handler)
    application.add_exception_handler(AuthenticationError, authentication_exception_handler)
    application.add_exception_handler(SupabaseSchemaError, supabase_schema_exception_handler)
    application.add_exception_handler(SupabaseServiceError, supabase_service_exception_handler)
