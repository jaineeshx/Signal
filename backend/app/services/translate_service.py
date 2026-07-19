"""Translation service — thin wrapper around the Gemini translation function.

Kept as a separate service layer so that the translation provider can be
swapped (e.g. for Google Cloud Translation API) without touching the API routes.
"""
from __future__ import annotations

from app.core.gemini import translate_text
from app.core.personas import VALID_LANGUAGES


async def translate(text: str, target_language: str) -> str:
    """Translate *text* into *target_language* via Gemini.

    Args:
        text:            Source text (any language, max 2 000 chars).
        target_language: ISO 639-1 language code (must be in VALID_LANGUAGES).

    Returns:
        Translated string.

    Raises:
        ValueError:     If *target_language* is not supported.
        RuntimeError:   If the Gemini API call fails.
    """
    if target_language not in VALID_LANGUAGES:
        raise ValueError(
            f"Unsupported target language '{target_language}'. "
            f"Supported: {', '.join(sorted(VALID_LANGUAGES))}."
        )
    return await translate_text(text, target_language)
