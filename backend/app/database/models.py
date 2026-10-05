"""Typed records exchanged between the Supabase repository and API layers."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str | None = None
    role: str = "user"
    created_at: datetime | None = None


class ConversationRecord(BaseModel):
    id: UUID
    user_id: UUID
    title: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MessageRecord(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime | None = None


class DocumentRecord(BaseModel):
    id: UUID
    filename: str
    file_type: str
    uploaded_by: UUID
    created_at: datetime | None = None


class LogRecord(BaseModel):
    id: UUID
    user_id: UUID | None = None
    endpoint: str
    request_data: dict[str, Any] = Field(default_factory=dict)
    response_time: float | None = None
    success: bool = True
    created_at: datetime | None = None
