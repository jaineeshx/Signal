"""Google Gemini AI client for SIGNAL.

All interactions with the Gemini API are centralised here so that:
  • Mocking in tests is trivial (patch one module).
  • The API key is configured once and never scattered throughout the codebase.
  • Retry / error handling lives in a single place.
  • Migrated to the new `google.genai` SDK for Code Quality standards.
"""
from __future__ import annotations

import logging

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.personas import _LANGUAGE_INSTRUCTIONS, get_system_prompt

logger = logging.getLogger(__name__)

# ── Configure Gemini SDK once on import ───────────────────────────────────────
client = None
if settings.gemini_api_key:
    client = genai.Client(api_key=settings.gemini_api_key)

# ── Shared safety settings ───────────────────────────────────────────────────
_SAFETY_SETTINGS = [
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_MEDIUM_AND_ABOVE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_MEDIUM_AND_ABOVE"),
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_MEDIUM_AND_ABOVE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_MEDIUM_AND_ABOVE"),
]

# ── Shared generation configs ─────────────────────────────────────────────────
_GEN_CONFIG_ADVISORY = types.GenerateContentConfig(
    temperature=0.3,
    top_p=0.95,
    top_k=40,
    max_output_tokens=1_024,
    safety_settings=_SAFETY_SETTINGS,
)

_GEN_CONFIG_TRANSLATE = types.GenerateContentConfig(
    temperature=0.1,
    top_p=0.95,
    top_k=40,
    max_output_tokens=1_024,
    safety_settings=_SAFETY_SETTINGS,
)

def _get_chat_config(persona: str, language: str) -> types.GenerateContentConfig:
    system_prompt = get_system_prompt(persona, language)
    return types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        top_k=40,
        max_output_tokens=1_024,
        safety_settings=_SAFETY_SETTINGS,
        system_instruction=system_prompt,
    )

def _get_nav_config(system_instruction: str) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        top_k=40,
        max_output_tokens=1_024,
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
    """Generate a persona-aware Gemini response."""
    if not settings.gemini_available or client is None:
        logger.warning("Gemini unavailable — returning mock response (persona=%s)", persona)
        return _MOCK_RESPONSES.get(persona, _MOCK_RESPONSES["fan"])

    try:
        config = _get_chat_config(persona, language)
        history = []
        for turn in (context or []):
            history.append(types.Content(
                role=turn["role"],
                parts=[types.Part.from_text(text=turn["content"])]
            ))
        
        chat = client.aio.chats.create(
            model=settings.gemini_model,
            config=config,
            history=history
        )
        response = await chat.send_message(message)
        return response.text

    except Exception as exc:
        logger.exception("Gemini chat error: %s", exc)
        raise RuntimeError(f"AI service error: {exc}") from exc


async def generate_crowd_advisory(zone_data: dict[str, dict]) -> str:
    """Generate a natural-language crowd advisory for venue staff."""
    if not settings.gemini_available or client is None:
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
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=_GEN_CONFIG_ADVISORY,
        )
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
    """Generate step-by-step stadium navigation directions via Gemini."""
    if not settings.gemini_available or client is None:
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
        config = _get_nav_config(system)
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=config,
        )
        return response.text

    except Exception as exc:
        logger.exception("Gemini navigation error: %s", exc)
        raise RuntimeError(f"Navigation AI error: {exc}") from exc


async def translate_text(text: str, target_language: str) -> str:
    """Translate *text* to *target_language* using Gemini."""
    if not settings.gemini_available or client is None:
        return _MOCK_TRANSLATION

    prompt = (
        f"Translate the following text accurately into the language with ISO code '{target_language}'. "
        "Return ONLY the translated text, nothing else.\n\n"
        f"Text to translate:\n{text}"
    )

    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=_GEN_CONFIG_TRANSLATE,
        )
        return response.text

    except Exception as exc:
        logger.exception("Gemini translation error: %s", exc)
        raise RuntimeError(f"Translation error: {exc}") from exc
