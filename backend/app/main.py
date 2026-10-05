"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="AI-Knowledge-Chatbot API",
    version="0.1.0",
    description="Project foundation with a basic health endpoint.",
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Report that the application is running."""
    return {"status": "healthy"}
