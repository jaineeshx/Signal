"""Chat endpoint — the primary GenAI interface for SIGNAL.

POST /api/chat
  Accepts a user message plus persona/language context.
  Returns a Gemini-generated response appropriate for the chosen persona.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.gemini import generate_response
from app.models.chat import ChatRequest, ChatResponse
from app.utils.validators import (
    validate_chat_context,
    validate_language,
    validate_message,
    validate_persona,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the SIGNAL AI assistant",
    description=(
        "Submit a message with an optional persona (fan | staff | volunteer | organizer) "
        "and language code. Returns a context-aware Gemini response."
    ),
)
async def chat(request: ChatRequest) -> ChatResponse:
    """Handle an incoming chat message and return an AI response."""
    # ── Validate & sanitise inputs ─────────────────────────────────────────
    try:
        message  = validate_message(request.message)
        persona  = validate_persona(request.persona)
        language = validate_language(request.language)
        context  = validate_chat_context(
            [t.model_dump() for t in request.context] if request.context else None
        )
    except ValueError as exc:
        logger.exception("Pydantic validation error: %s", exc)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    logger.info("Chat request | persona=%s lang=%s chars=%d", persona, language, len(message))

    # ── Generate AI response ───────────────────────────────────────────────
    try:
        reply = await generate_response(
            message=message,
            persona=persona,
            language=language,
            context=context,
        )
    except RuntimeError as exc:
        logger.exception("Chat error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI service is temporarily unavailable. Please try again.",
        ) from exc

    return ChatResponse(
        reply=reply,
        persona=persona,
        language=language,
        mock=not settings.gemini_available,
    )
