"""Pydantic models for crowd management data."""
from __future__ import annotations

from enum import Enum
from typing import Dict

from pydantic import BaseModel, Field


class DensityStatus(str, Enum):
    """Categorical crowd density status for a single zone."""

    OK = "OK"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"


class ZoneData(BaseModel):
    """Real-time crowd data for a single stadium zone."""

    zone: str = Field(..., description="Zone display name")
    density: int = Field(..., ge=0, le=100, description="Percentage of zone capacity filled")
    fan_count: int = Field(..., ge=0, description="Estimated number of fans in zone")
    status: DensityStatus = Field(..., description="Traffic-light status")
    alert: bool = Field(default=False, description="True when zone requires immediate attention")


class CrowdStatusResponse(BaseModel):
    """Response returned by GET /api/crowd/status."""

    zones: Dict[str, ZoneData] = Field(..., description="Mapping of zone id → zone data")
    overall_density: int = Field(..., ge=0, le=100, description="Stadium-wide average density %")
    total_fans: int = Field(..., ge=0, description="Total estimated fan count across all zones")
    alert_zones: int = Field(..., ge=0, description="Number of zones currently in alert state")


class CrowdAlertRequest(BaseModel):
    """Request body for POST /api/crowd/alert — generates an AI advisory."""

    zone_data: Dict[str, dict] = Field(
        ...,
        description="Zone data snapshot to generate advisory from",
    )


class CrowdAlertResponse(BaseModel):
    """AI-generated crowd advisory."""

    advisory: str = Field(..., description="Gemini-generated operational advisory text")
    mock: bool = Field(default=False, description="True when the advisory is a mock response")
