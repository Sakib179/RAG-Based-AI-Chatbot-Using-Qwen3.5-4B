"""Global exception handling for unexpected application failures."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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


def register_exception_handlers(application: FastAPI) -> None:
    """Register global exception handlers on the FastAPI application."""

    application.add_exception_handler(Exception, unhandled_exception_handler)
