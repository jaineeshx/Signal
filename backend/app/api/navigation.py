"""Navigation and translation endpoints for SIGNAL.

POST /api/navigate   — AI-powered step-by-step stadium directions.
POST /api/translate  — Translate any text to a supported language.
GET  /api/locations  — List all known stadium location names.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.gemini import generate_navigation_directions
from app.models.venue import (
    NavigationRequest,
    NavigationResponse,
    TranslationRequest,
    TranslationResponse,
)
from app.services.nav_service import list_all_locations
from app.services.translate_service import translate
from app.utils.validators import validate_language, validate_location

logger = logging.getLogger(__name__)
router = APIRouter(tags=["navigation"])


@router.post(
    "/navigate",
    response_model=NavigationResponse,
    summary="Get AI-generated stadium navigation directions",
)
async def navigate(request: NavigationRequest) -> NavigationResponse:
    """Return step-by-step walking directions from one stadium location to another."""
    try:
        from_loc  = validate_location(request.from_location)
        to_loc    = validate_location(request.to_location)
        language  = validate_language(request.language)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    if from_loc.lower() == to_loc.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start and destination locations must be different.",
        )

    logger.info(
        "Navigation request | from='%s' to='%s' accessible=%s lang=%s",
        from_loc, to_loc, request.accessibility, language,
    )

    try:
        directions = await generate_navigation_directions(
            from_location=from_loc,
            to_location=to_loc,
            accessibility=request.accessibility,
            language=language,
        )
    except RuntimeError as exc:
        logger.error("Navigation AI error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Navigation AI service temporarily unavailable.",
        ) from exc

    return NavigationResponse(
        from_location=from_loc,
        to_location=to_loc,
        directions=directions,
        accessibility=request.accessibility,
        mock=not settings.gemini_available,
    )


@router.post(
    "/translate",
    response_model=TranslationResponse,
    summary="Translate text using Gemini AI",
)
async def translate_endpoint(request: TranslationRequest) -> TranslationResponse:
    """Translate the provided text to a target language via Gemini."""
    try:
        language = validate_language(request.target_language)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    try:
        translated = await translate(request.text, language)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Translation service unavailable",
        ) from exc

    return TranslationResponse(
        original_text=request.text,
        translated_text=translated,
        target_language=language,
        mock=not settings.gemini_available,
    )


@router.get(
    "/locations",
    summary="List all known stadium locations",
    response_model=list[str],
)
async def list_locations() -> list[str]:
    """Return every named location in the stadium that SIGNAL can navigate to."""
    return list_all_locations()
