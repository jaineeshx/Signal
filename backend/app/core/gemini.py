"""Google Gemini AI client for SIGNAL.

All interactions with the Gemini API are centralised here so that:
  • Mocking in tests is trivial (patch one module).
  • The API key is configured once and never scattered throughout the codebase.
  • Retry / error handling lives in a single place.
  • Model instances are cached at module level — one per configuration —
    so we never pay the construction overhead on every API call.
"""
from __future__ import annotations

import logging

import google.generativeai as genai

from app.core.config import settings
from app.core.personas import _LANGUAGE_INSTRUCTIONS, get_system_prompt

logger = logging.getLogger(__name__)

# ── Configure Gemini SDK once on import ───────────────────────────────────────
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)

# ── Shared generation configs (immutable dicts) ───────────────────────────────
_GEN_CONFIG_CHAT = genai.types.GenerationConfig(
    temperature=0.7,
    top_p=0.95,
    top_k=40,
    max_output_tokens=1_024,
)

_GEN_CONFIG_ADVISORY = genai.types.GenerationConfig(
    temperature=0.3,
    top_p=0.95,
    top_k=40,
    max_output_tokens=1_024,
)

_GEN_CONFIG_NAV = genai.types.GenerationConfig(
    temperature=0.2,
    top_p=0.95,
    top_k=40,
    max_output_tokens=1_024,
)

_GEN_CONFIG_TRANSLATE = genai.types.GenerationConfig(
    temperature=0.1,
    top_p=0.95,
    top_k=40,
    max_output_tokens=1_024,
)

_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH",        "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",  "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT",  "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# ── Cached model instances ─────────────────────────────────────────────────────
# Advisory and translation use a fixed system prompt, so we can cache them once.
# The chat model varies by persona/language, so we cache per (persona, language) pair.
_advisory_model: genai.GenerativeModel | None = None
_nav_base_model: genai.GenerativeModel | None = None
_translate_model: genai.GenerativeModel | None = None
_chat_model_cache: dict[str, genai.GenerativeModel] = {}


def _get_advisory_model() -> genai.GenerativeModel:
    """Return (and cache) the shared crowd-advisory model instance."""
    global _advisory_model  # noqa: PLW0603
    if _advisory_model is None:
        _advisory_model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=_GEN_CONFIG_ADVISORY,
            safety_settings=_SAFETY_SETTINGS,
        )
    return _advisory_model


def _get_translate_model() -> genai.GenerativeModel:
    """Return (and cache) the shared translation model instance."""
    global _translate_model  # noqa: PLW0603
    if _translate_model is None:
        _translate_model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=_GEN_CONFIG_TRANSLATE,
            safety_settings=_SAFETY_SETTINGS,
        )
    return _translate_model


def _get_chat_model(persona: str, language: str) -> genai.GenerativeModel:
    """Return a cached chat model for the given persona + language combination."""
    cache_key = f"{persona}:{language}"
    if cache_key not in _chat_model_cache:
        system_prompt = get_system_prompt(persona, language)
        _chat_model_cache[cache_key] = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=_GEN_CONFIG_CHAT,
            safety_settings=_SAFETY_SETTINGS,
            system_instruction=system_prompt,
        )
    return _chat_model_cache[cache_key]


def _get_nav_model(system_instruction: str) -> genai.GenerativeModel:
    """Return a navigation model; each route may vary in system prompt, so no global cache."""
    return genai.GenerativeModel(
        model_name=settings.gemini_model,
        generation_config=_GEN_CONFIG_NAV,
        safety_settings=_SAFETY_SETTINGS,
        system_instruction=system_instruction,
    )


# ── Mock responses (used when MOCK_MODE=true or no API key) ───────────────────
_MOCK_RESPONSES: dict[str, str] = {
    "fan": (
        "Welcome to FIFA World Cup 2026! ⚽🏆 I'm SIGNAL, your personal stadium assistant. "
        "I can help you find your seat, locate the nearest food court, get transport info, "
        "or answer any stadium question. What do you need?"
    ),
    "staff": (
        "SIGNAL Operational Mode active. Ready to support incident triage, crowd monitoring, "
        "emergency protocols, and zone management. How can I assist your team right now?"
    ),
    "volunteer": (
        "Hi there, volunteer! SIGNAL is here to help you do your best work. "
        "I can help you direct fans, explain procedures, or find the right contact. ✅ What do you need?"
    ),
    "organizer": (
        "SIGNAL Analytics Mode active. Currently monitoring 8 stadium zones. "
        "Aggregate capacity: 78%. All critical systems nominal. How can I support operations?"
    ),
}

_MOCK_ADVISORY = (
    "⚠️ ADVISORY: North Stand (Zone 1) approaching high density at 87%. "
    "Recommend activating overflow corridor B-3 and deploying 4 additional stewards "
    "to Gate A. Fan throughput should normalise within 15 minutes."
)

_MOCK_DIRECTIONS = (
    "🗺️ Step-by-step directions:\n"
    "1. Exit through your current concourse door heading North.\n"
    "2. Follow the main concourse past Food Court 2 on your right.\n"
    "3. Take the escalator (or Lift 3 for wheelchair access) up to Level 2.\n"
    "4. Follow the yellow wayfinding signs to your destination.\n"
    "Estimated walk time: 3–4 minutes."
)

_MOCK_TRANSLATION = (
    "Translation unavailable in mock mode — "
    "connect a Gemini API key to enable multilingual translation."
)


# ── Core AI functions ──────────────────────────────────────────────────────────

async def generate_response(
    message: str,
    persona: str = "fan",
    language: str = "en",
    context: list[dict[str, str]] | None = None,
) -> str:
    """Generate a persona-aware Gemini response.

    Args:
        message:  The user's sanitised message.
        persona:  One of ``fan``, ``staff``, ``volunteer``, ``organizer``.
        language: ISO 639-1 language code for the response.
        context:  Optional list of prior conversation turns
                  (each a dict with ``role`` and ``content`` keys).

    Returns:
        The AI-generated text response.

    Raises:
        RuntimeError: If the Gemini API call fails.
    """
    if not settings.gemini_available:
        logger.warning("Gemini unavailable — returning mock response (persona=%s)", persona)
        return _MOCK_RESPONSES.get(persona, _MOCK_RESPONSES["fan"])

    try:
        model = _get_chat_model(persona, language)
        history = [
            {"role": turn["role"], "parts": [turn["content"]]}
            for turn in (context or [])
        ]
        chat = model.start_chat(history=history)
        response = await chat.send_message_async(message)
        return response.text

    except Exception as exc:
        logger.exception("Gemini chat error: %s", exc)
        raise RuntimeError(f"AI service error: {exc}") from exc


async def generate_crowd_advisory(zone_data: dict[str, dict]) -> str:
    """Generate a natural-language crowd advisory for venue staff.

    Args:
        zone_data: Mapping of zone name → ``{"density": int, "status": str}``.

    Returns:
        A 2–3 sentence operational advisory string.
    """
    if not settings.gemini_available:
        return _MOCK_ADVISORY

    zones_text = "\n".join(
        f"  • {zone}: {data['density']}% capacity — {data['status']}"
        for zone, data in zone_data.items()
    )

    prompt = (
        "You are an operational AI for FIFA World Cup 2026 crowd management.\n\n"
        f"Current stadium zone data:\n{zones_text}\n\n"
        "Write a 2–3 sentence professional crowd advisory for venue staff. Include:\n"
        "1. The most critical zone(s) needing attention.\n"
        "2. A specific recommended action.\n"
        "3. The expected outcome.\n"
        "Be concise, direct, and use operational language. No emojis."
    )

    try:
        model = _get_advisory_model()
        response = await model.generate_content_async(prompt)
        return response.text

    except Exception as exc:
        logger.exception("Gemini crowd advisory error: %s", exc)
        raise RuntimeError(f"AI advisory error: {exc}") from exc


async def generate_navigation_directions(
    from_location: str,
    to_location: str,
    accessibility: bool = False,
    language: str = "en",
) -> str:
    """Generate step-by-step stadium navigation directions via Gemini.

    Args:
        from_location: Starting location inside/outside the stadium.
        to_location:   Destination (seat, facility, gate, etc.).
        accessibility: When True, restrict to wheelchair-accessible routes.
        language:      ISO 639-1 response language code.

    Returns:
        Numbered walking directions as a formatted string.
    """
    if not settings.gemini_available:
        return _MOCK_DIRECTIONS

    access_note = (
        "IMPORTANT: This person requires a fully wheelchair-accessible route. "
        "Avoid all stairs and escalators. Use lifts and ramps only. "
        "Mention Accessibility Services (Gate D, Level 1) if relevant."
        if accessibility
        else ""
    )

    lang_note = _LANGUAGE_INSTRUCTIONS.get(language, _LANGUAGE_INSTRUCTIONS["en"])

    system = (
        "You are a stadium navigation assistant for FIFA World Cup 2026. "
        "The stadium layout:\n"
        "  • Entry gates: A (North), B (South), C (East, VIP/Media), D (West, Accessibility)\n"
        "  • Seating: Sections 101–140 (Lower) and 201–240 (Upper)\n"
        "  • Facilities: Food Courts 1–4, Medical Centre (Gate C, Level 1), "
        "Prayer Room (Level 2 North), Family Zone (Gate D, Level 1), "
        "Accessibility Services (Gate D, Level 1), Lost & Found (Gate B, Level 1), "
        "VIP Lounge (Gate C, Level 2), Merchandise (all concourses), "
        "Parking: P1–P5 (exterior)\n"
        f"{access_note}\n"
        f"{lang_note}"
    )

    prompt = (
        f"Navigate from: {from_location}\n"
        f"Destination: {to_location}\n\n"
        "Provide clear, numbered step-by-step walking directions. "
        "Include landmark cues and an estimated walking time."
    )

    try:
        model = _get_nav_model(system)
        response = await model.generate_content_async(prompt)
        return response.text

    except Exception as exc:
        logger.exception("Gemini navigation error: %s", exc)
        raise RuntimeError(f"Navigation AI error: {exc}") from exc


async def translate_text(text: str, target_language: str) -> str:
    """Translate *text* to *target_language* using Gemini.

    Useful for staff-to-fan real-time communication.
    """
    if not settings.gemini_available:
        return _MOCK_TRANSLATION

    prompt = (
        f"Translate the following text accurately into the language with ISO code '{target_language}'. "
        "Return ONLY the translated text, nothing else.\n\n"
        f"Text to translate:\n{text}"
    )

    try:
        model = _get_translate_model()
        response = await model.generate_content_async(prompt)
        return response.text

    except Exception as exc:
        logger.exception("Gemini translation error: %s", exc)
        raise RuntimeError(f"Translation error: {exc}") from exc
