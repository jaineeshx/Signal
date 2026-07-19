"""Pydantic request/response models for the /api/chat endpoint."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ConversationTurn(BaseModel):
    """A single turn in a conversation history."""

    role: str = Field(..., description="'user' or 'model'")
    content: str = Field(..., description="The message text for this turn")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in {"user", "model"}:
            raise ValueError("role must be 'user' or 'model'")
        return v


class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=1_000,
        description="The user's message (max 1 000 characters)",
    )
    persona: str = Field(
        default="fan",
        description="User role: fan | staff | volunteer | organizer",
    )
    language: str = Field(
        default="en",
        description="ISO 639-1 language code for the AI response",
    )
    context: Optional[List[ConversationTurn]] = Field(
        default=None,
        description="Recent conversation history for multi-turn chat",
    )


class ChatResponse(BaseModel):
    """Response returned by the /api/chat endpoint."""

    reply: str = Field(..., description="The AI-generated response text")
    persona: str = Field(..., description="Persona that was used for this response")
    language: str = Field(..., description="Language code of the response")
    mock: bool = Field(
        default=False,
        description="True when the response came from the mock fallback, not live Gemini",
    )
