"""Pydantic models for stadium venue data."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Facility(BaseModel):
    """A named facility inside or adjacent to the stadium."""

    name: str = Field(..., description="Display name of the facility")
    level: int = Field(..., description="Floor level (0 = exterior, 1 = ground, 2 = upper)")
    side: str = Field(..., description="Stadium side: North | South | East | West | All | Exterior")
    description: str = Field(..., description="Short human-readable description")
    accessible: bool = Field(default=True, description="Whether this facility is wheelchair-accessible")


class NavigationRequest(BaseModel):
    """Request body for POST /api/navigate."""

    from_location: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="User's current location (gate, section, facility, etc.)",
    )
    to_location: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Intended destination",
    )
    accessibility: bool = Field(
        default=False,
        description="When True, return only wheelchair-accessible routes",
    )
    language: str = Field(
        default="en",
        description="ISO 639-1 language code for the response",
    )


class NavigationResponse(BaseModel):
    """AI-generated navigation directions."""

    from_location: str = Field(..., description="Starting location as submitted")
    to_location: str = Field(..., description="Destination as submitted")
    directions: str = Field(..., description="Step-by-step navigation directions from Gemini")
    accessibility: bool = Field(..., description="Whether accessibility routing was applied")
    mock: bool = Field(default=False, description="True when directions are a mock fallback")


class TranslationRequest(BaseModel):
    """Request body for POST /api/translate."""

    text: str = Field(..., min_length=1, max_length=2_000, description="Text to translate")
    target_language: str = Field(..., description="ISO 639-1 target language code")


class TranslationResponse(BaseModel):
    """Translated text response."""

    original_text: str = Field(..., description="The original input text")
    translated_text: str = Field(..., description="Gemini-translated output")
    target_language: str = Field(..., description="ISO 639-1 target language code")
    mock: bool = Field(default=False)


class StadiumInfo(BaseModel):
    """High-level stadium configuration returned by the health/info endpoint."""

    name: str
    total_capacity: int
    zones: List[str]
    facilities: List[str]
    gates: List[str]
