"""Health-check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Check backend health",
    description="Returns a healthy status when the backend process is running.",
    response_description="Backend health status",
)
async def health() -> dict[str, str]:
    """Return the current service health status."""

    return {
        "status": "healthy",
        "service": "AI Knowledge Chatbot Backend",
    }
