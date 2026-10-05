"""Small, explicit repository for application data stored in Supabase."""

from typing import Any
from uuid import UUID

from app.database.supabase_client import SupabaseServiceError, get_supabase_client


class RepositoryError(SupabaseServiceError):
    """Raised when a database operation fails."""


def _rows(response: Any) -> list[dict[str, Any]]:
    data = getattr(response, "data", None)
    if data is None and isinstance(response, dict):
        data = response.get("data")
    return list(data or [])


def _single(response: Any) -> dict[str, Any] | None:
    rows = _rows(response)
    return rows[0] if rows else None


def _execute(operation: str, callback: Any) -> Any:
    try:
        return callback()
    except SupabaseServiceError:
        raise
    except Exception as exc:
        raise RepositoryError(f"Supabase operation failed: {operation}") from exc


def create_profile(user_id: UUID | str, email: str | None, role: str = "user") -> dict[str, Any]:
    response = _execute(
        "create profile",
        lambda: get_supabase_client().table("profiles").upsert(
            {"id": str(user_id), "email": email, "role": role}, on_conflict="id"
        ).execute(),
    )
    result = _single(response)
    if result is None:
        raise RepositoryError("Supabase did not return the created profile")
    return result


def get_profile(user_id: UUID | str) -> dict[str, Any] | None:
    response = _execute(
        "get profile",
        lambda: get_supabase_client().table("profiles").select("*").eq("id", str(user_id)).limit(1).execute(),
    )
    return _single(response)


def create_conversation(user_id: UUID | str, title: str | None = None) -> dict[str, Any]:
    response = _execute(
        "create conversation",
        lambda: get_supabase_client().table("conversations").insert(
            {"user_id": str(user_id), "title": title}
        ).execute(),
    )
    result = _single(response)
    if result is None:
        raise RepositoryError("Supabase did not return the created conversation")
    return result


def _conversation_owned(conversation_id: UUID | str, user_id: UUID | str) -> bool:
    response = _execute(
        "check conversation ownership",
        lambda: get_supabase_client().table("conversations").select("id").eq(
            "id", str(conversation_id)
        ).eq("user_id", str(user_id)).limit(1).execute(),
    )
    return _single(response) is not None


def save_message(
    conversation_id: UUID | str,
    role: str,
    content: str,
    sources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if role not in {"user", "assistant", "system"}:
        raise ValueError("Message role must be user, assistant, or system")
    response = _execute(
        "save message",
        lambda: get_supabase_client().table("messages").insert(
            {
                "conversation_id": str(conversation_id),
                "role": role,
                "content": content,
                "sources": sources or [],
            }
        ).execute(),
    )
    result = _single(response)
    if result is None:
        raise RepositoryError("Supabase did not return the saved message")
    return result


def get_conversation_history(
    conversation_id: UUID | str,
    user_id: UUID | str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    if limit < 1:
        return []
    if not _conversation_owned(conversation_id, user_id):
        raise RepositoryError("Conversation was not found for this user")
    response = _execute(
        "get conversation history",
        lambda: get_supabase_client().table("messages").select(
            "id,conversation_id,role,content,sources,created_at"
        ).eq("conversation_id", str(conversation_id)).order(
            "created_at", desc=True
        ).limit(min(limit, 100)).execute(),
    )
    return list(reversed(_rows(response)))


def create_document(
    filename: str,
    file_type: str,
    uploaded_by: UUID | str,
) -> dict[str, Any]:
    response = _execute(
        "save document metadata",
        lambda: get_supabase_client().table("documents").insert(
            {"filename": filename, "file_type": file_type, "uploaded_by": str(uploaded_by)}
        ).execute(),
    )
    result = _single(response)
    if result is None:
        raise RepositoryError("Supabase did not return document metadata")
    return result


def save_log(
    user_id: UUID | str | None,
    endpoint: str,
    request_data: dict[str, Any],
    response_time: float,
    success: bool,
) -> dict[str, Any]:
    response = _execute(
        "save request log",
        lambda: get_supabase_client().table("logs").insert(
            {
                "user_id": str(user_id) if user_id else None,
                "endpoint": endpoint,
                "request_data": request_data,
                "response_time": response_time,
                "success": success,
            }
        ).execute(),
    )
    result = _single(response)
    if result is None:
        raise RepositoryError("Supabase did not return the saved log")
    return result
