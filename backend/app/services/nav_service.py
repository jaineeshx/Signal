"""Stadium navigation data and helpers for SIGNAL.

This module provides a structured map of stadium locations and a lookup
helper that feeds rich context into the Gemini navigation prompts.
"""
from __future__ import annotations

# ── Type alias ─────────────────────────────────────────────────────────────────
LocationInfo = dict[str, str | int | bool]

# ── Stadium location catalogue ─────────────────────────────────────────────────
# Each entry: level (0=exterior, 1=ground, 2=upper), side, description, accessible
_LOCATIONS: dict[str, LocationInfo] = {
    # Gates
    "gate a":               {"level": 1, "side": "North",    "description": "Main public entrance — North side. Nearest parking: P1, P2.", "accessible": True},
    "gate b":               {"level": 1, "side": "South",    "description": "Main public entrance — South side. Nearest parking: P3, P4.", "accessible": True},
    "gate c":               {"level": 1, "side": "East",     "description": "VIP, media, and accreditation entrance — East side.", "accessible": True},
    "gate d":               {"level": 1, "side": "West",     "description": "Accessibility-first entrance — West side. Lifts to all levels.", "accessible": True},
    # Seating — lower
    "section 101":          {"level": 1, "side": "North",    "description": "North Lower Stand, Row A–Z. Nearest gate: A.", "accessible": False},
    "section 102":          {"level": 1, "side": "North",    "description": "North Lower Stand, Row A–Z. Nearest gate: A.", "accessible": False},
    "section 110":          {"level": 1, "side": "North",    "description": "North Lower Stand corner block.", "accessible": True},
    "section 111":          {"level": 1, "side": "South",    "description": "South Lower Stand, Row A–Z. Nearest gate: B.", "accessible": False},
    "section 120":          {"level": 1, "side": "South",    "description": "South Lower Stand corner block.", "accessible": True},
    "section 121":          {"level": 1, "side": "East",     "description": "East Lower Stand. Nearest gate: C.", "accessible": False},
    "section 130":          {"level": 1, "side": "East",     "description": "East Lower Stand corner block.", "accessible": True},
    "section 131":          {"level": 1, "side": "West",     "description": "West Lower Stand. Nearest gate: D.", "accessible": False},
    "section 140":          {"level": 1, "side": "West",     "description": "West Lower Stand, wheelchair bays included.", "accessible": True},
    # Seating — upper
    "section 201":          {"level": 2, "side": "North",    "description": "North Upper Stand. Lift access via Gate A.", "accessible": True},
    "section 211":          {"level": 2, "side": "South",    "description": "South Upper Stand. Lift access via Gate B.", "accessible": True},
    "section 221":          {"level": 2, "side": "East",     "description": "East Upper Stand. Lift access via Gate C.", "accessible": True},
    "section 231":          {"level": 2, "side": "West",     "description": "West Upper Stand. Lift access via Gate D.", "accessible": True},
    # Facilities
    "food court 1":         {"level": 1, "side": "North",    "description": "Fast food, hot dogs, soft drinks, snacks.", "accessible": True},
    "food court 2":         {"level": 1, "side": "South",    "description": "International cuisine — pizza, wraps, noodles.", "accessible": True},
    "food court 3":         {"level": 2, "side": "East",     "description": "Halal-certified meals and vegetarian options.", "accessible": True},
    "food court 4":         {"level": 2, "side": "West",     "description": "Premium dining — table service available.", "accessible": True},
    "medical centre":       {"level": 1, "side": "East",     "description": "First aid, paramedics, and AED stations. Open all match hours.", "accessible": True},
    "prayer room":          {"level": 2, "side": "North",    "description": "Multi-faith quiet prayer space. Wudu facilities available.", "accessible": True},
    "family zone":          {"level": 1, "side": "West",     "description": "Children's play area, baby-changing, quiet space.", "accessible": True},
    "accessibility services": {"level": 1, "side": "West",  "description": "Wheelchair loan, hearing loops, visual aids, companion tickets.", "accessible": True},
    "lost and found":       {"level": 1, "side": "South",    "description": "Lost property, reunification point for separated fans.", "accessible": True},
    "fan zone":             {"level": 0, "side": "Exterior", "description": "Outdoor entertainment area with screens, food trucks, and live music.", "accessible": True},
    "vip lounge":           {"level": 2, "side": "East",     "description": "VIP hospitality — accreditation required.", "accessible": True},
    "merchandise":          {"level": 1, "side": "All",      "description": "Official FIFA 2026 merchandise — 8 outlets across all concourses.", "accessible": True},
    # Parking
    "parking p1":           {"level": 0, "side": "North",    "description": "North parking — 1 200 spaces. 5 min walk to Gate A.", "accessible": True},
    "parking p2":           {"level": 0, "side": "North",    "description": "North overflow parking — 800 spaces. Shuttle to Gate A.", "accessible": True},
    "parking p3":           {"level": 0, "side": "South",    "description": "South parking — 1 400 spaces. 6 min walk to Gate B.", "accessible": True},
    "parking p4":           {"level": 0, "side": "South",    "description": "South overflow — 600 spaces. Shuttle to Gate B.", "accessible": True},
    "parking p5":           {"level": 0, "side": "West",     "description": "Accessible parking — 150 dedicated bays. Direct ramp to Gate D.", "accessible": True},
}

# Pre-sorted list cached at module level — never recomputed on each request
_SORTED_LOCATION_NAMES: list[str] = sorted(_LOCATIONS.keys())


def lookup_location(name: str) -> LocationInfo | None:
    """Return location data for *name* (case-insensitive)."""
    return _LOCATIONS.get(name.strip().lower())


def list_all_locations() -> list[str]:
    """Return a pre-sorted list of all known location names."""
    return _SORTED_LOCATION_NAMES


def get_location_context(from_name: str, to_name: str) -> str:
    """Build a brief context string for the Gemini navigation prompt."""
    from_data = lookup_location(from_name) or {}
    to_data   = lookup_location(to_name) or {}

    from_desc = str(from_data.get("description", "unknown location"))
    to_desc   = str(to_data.get("description", "unknown location"))

    return (
        f"Origin '{from_name}': {from_desc}\n"
        f"Destination '{to_name}': {to_desc}"
    )
