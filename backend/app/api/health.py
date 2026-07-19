"""Health check and stadium info endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.models.venue import StadiumInfo
from app.services.nav_service import list_all_locations

router = APIRouter(tags=["health"])

_ZONES = [
    "North Stand", "South Stand", "East Stand", "West Stand",
    "VIP Section", "Food Court North", "Food Court South", "Main Concourse",
]
_GATES = ["Gate A (North)", "Gate B (South)", "Gate C (East/VIP)", "Gate D (West/Accessibility)"]


@router.get("/health", summary="Health check")
async def health_check() -> dict:
    """Return service status and basic configuration info."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "gemini_configured": bool(settings.gemini_api_key),
        "mock_mode": settings.mock_mode,
    }


@router.get("/info", summary="Stadium info", response_model=StadiumInfo)
async def stadium_info() -> StadiumInfo:
    """Return high-level stadium configuration (name, capacity, zones, facilities)."""
    all_locations = list_all_locations()
    facilities = [loc for loc in all_locations if not loc.startswith(("gate", "section", "parking"))]
    return StadiumInfo(
        name=settings.stadium_name,
        total_capacity=settings.total_capacity,
        zones=_ZONES,
        facilities=facilities,
        gates=_GATES,
    )
