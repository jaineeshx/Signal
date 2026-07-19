"""Input validation and sanitisation utilities for SIGNAL.

All user-supplied strings pass through here before being forwarded to
Gemini or other services, reducing the risk of prompt injection and
ensuring requests stay within sensible bounds.
"""
from __future__ import annotations

import re

from app.core.personas import VALID_LANGUAGES, VALID_PERSONAS

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_MESSAGE_LENGTH: int = 1_000  # characters
MAX_LOCATION_LENGTH: int = 200   # characters
MAX_HISTORY_TURNS: int = 20      # conversation turns retained

# Patterns that look like prompt-injection attempts
_INJECTION_PATTERNS: re.Pattern[str] = re.compile(
    r"(ignore\s+(all\s+)?previous\s+instructions?|"
    r"you\s+are\s+now|system\s+prompt|"
    r"disregard\s+your\s+instructions?|"
    r"new\s+persona|forget\s+everything)",
    re.IGNORECASE,
)


# ── Public helpers ─────────────────────────────────────────────────────────────

def sanitise_text(text: str) -> str:
    """Strip leading/trailing whitespace and collapse internal whitespace."""
    return re.sub(r"\s+", " ", text.strip())


def validate_message(message: str) -> str:
    """Validate and sanitise a user chat message.

    Raises:
        ValueError: if the message is empty, exceeds the length limit,
                    or contains a prompt-injection pattern.
    """
    cleaned = sanitise_text(message)
    if not cleaned:
        raise ValueError("Message must not be empty.")
    if len(cleaned) > MAX_MESSAGE_LENGTH:
        raise ValueError(
            f"Message exceeds the maximum allowed length of {MAX_MESSAGE_LENGTH} characters."
        )
    if _INJECTION_PATTERNS.search(cleaned):
        raise ValueError(
            "Message contains disallowed content. Please rephrase your question."
        )
    return cleaned


def validate_persona(persona: str) -> str:
    """Ensure *persona* is one of the supported values."""
    persona = persona.strip().lower()
    if persona not in VALID_PERSONAS:
        raise ValueError(
            f"Invalid persona '{persona}'. Must be one of: {', '.join(sorted(VALID_PERSONAS))}."
        )
    return persona


def validate_language(language: str) -> str:
    """Ensure *language* is a supported ISO 639-1 code."""
    language = language.strip().lower()
    if language not in VALID_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{language}'. Supported codes: {', '.join(sorted(VALID_LANGUAGES))}."
        )
    return language


def validate_location(location: str) -> str:
    """Validate a stadium location string."""
    cleaned = sanitise_text(location)
    if not cleaned:
        raise ValueError("Location must not be empty.")
    if len(cleaned) > MAX_LOCATION_LENGTH:
        raise ValueError(
            f"Location string exceeds {MAX_LOCATION_LENGTH} characters."
        )
    return cleaned


def validate_chat_context(context: list | None) -> list[dict[str, str]]:
    """Validate and normalise the optional conversation history list.

    Ensures each entry has ``role`` and ``content`` string fields and that
    the list is not excessively long (to avoid inflating token usage).
    Silently discards malformed turns rather than raising, to ensure
    partial history is never a hard failure.
    """
    if context is None:
        return []

    # Keep only the most recent turns to control token usage
    if len(context) > MAX_HISTORY_TURNS:
        context = context[-MAX_HISTORY_TURNS:]

    validated: list[dict[str, str]] = []
    for turn in context:
        if not isinstance(turn, dict):
            continue
        role = str(turn.get("role", "")).strip().lower()
        content = str(turn.get("content", "")).strip()
        if role not in {"user", "model"} or not content:
            continue
        validated.append({"role": role, "content": content[:MAX_MESSAGE_LENGTH]})

    return validated
