"""Pydantic request/response models for crowd management endpoints."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class DensityStatus(str, Enum):
    """Categorical crowd density status for a stadium zone."""

    OK = "OK"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"


class ZoneData(BaseModel):
    """Crowd data snapshot for a single stadium zone."""

    zone: str = Field(..., description="Human-readable zone name")
    density: int = Field(..., ge=0, le=100, description="Capacity utilisation percentage (0–100)")
    fan_count: int = Field(..., ge=0, description="Estimated number of fans in the zone")
    status: DensityStatus = Field(..., description="Categorical density status")
    alert: bool = Field(..., description="True when density exceeds the alert threshold")


class CrowdStatusResponse(BaseModel):
    """Aggregated crowd status for the entire stadium."""

    zones: dict[str, ZoneData] = Field(..., description="Per-zone crowd data keyed by zone ID")
    overall_density: int = Field(..., ge=0, le=100, description="Stadium-wide capacity utilisation (%)")
    total_fans: int = Field(..., ge=0, description="Total estimated fans across all zones")
    alert_zones: int = Field(..., ge=0, description="Number of zones currently in alert state")


class CrowdAlertRequest(BaseModel):
    """Optional zone data override for the advisory endpoint."""

    zone_data: dict[str, dict] | None = Field(
        default=None,
        description="Zone data to analyse. If omitted, live data is used automatically.",
    )


class CrowdAlertResponse(BaseModel):
    """AI-generated operational advisory for venue staff."""

    advisory: str = Field(..., description="2–3 sentence Gemini-generated crowd advisory")
    mock: bool = Field(default=False, description="True when the advisory came from the mock engine")
