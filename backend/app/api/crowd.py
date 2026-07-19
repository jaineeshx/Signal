"""Crowd management endpoints for SIGNAL.

GET  /api/crowd/status  — Returns live crowd density for all zones.
POST /api/crowd/alert   — Generates a Gemini AI advisory from zone data.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.gemini import generate_crowd_advisory
from app.models.crowd import CrowdAlertRequest, CrowdAlertResponse, CrowdStatusResponse
from app.services.crowd_service import get_crowd_status, zone_data_for_advisory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/crowd", tags=["crowd"])


@router.get(
    "/status",
    response_model=CrowdStatusResponse,
    summary="Get live crowd density for all stadium zones",
)
async def crowd_status() -> CrowdStatusResponse:
    """Return simulated real-time crowd density data for all 8 stadium zones."""
    return get_crowd_status()


@router.post(
    "/alert",
    response_model=CrowdAlertResponse,
    summary="Generate an AI crowd advisory from current zone data",
    description=(
        "Passes current zone density data to Gemini and returns a 2–3 sentence "
        "operational advisory for venue staff."
    ),
)
async def crowd_alert(request: CrowdAlertRequest) -> CrowdAlertResponse:
    """Generate a Gemini-powered crowd advisory."""
    zone_data = request.zone_data or zone_data_for_advisory()

    logger.info("Crowd advisory requested for %d zones", len(zone_data))

    try:
        advisory = await generate_crowd_advisory(zone_data)
    except RuntimeError as exc:
        logger.exception("Failed to generate crowd advisory: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI advisory service temporarily unavailable.",
        ) from exc

    return CrowdAlertResponse(
        advisory=advisory,
        mock=not settings.gemini_available,
    )


@router.get(
    "/advisory",
    response_model=CrowdAlertResponse,
    summary="Auto-generate an AI advisory from current live data",
)
async def auto_advisory() -> CrowdAlertResponse:
    """Convenience endpoint: fetches live zone data and generates an advisory in one call."""
    zone_data = zone_data_for_advisory()

    try:
        advisory = await generate_crowd_advisory(zone_data)
    except RuntimeError as exc:
        logger.exception("Auto-advisory error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI advisory service temporarily unavailable.",
        ) from exc

    return CrowdAlertResponse(advisory=advisory, mock=not settings.gemini_available)
