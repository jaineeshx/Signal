"""Crowd density simulation service for SIGNAL.

In a production deployment this module would subscribe to real-time sensor
feeds or access control gate counts.  For the FIFA World Cup 2026 demo it
generates realistic, time-varying crowd data for eight stadium zones so that
the rest of the application (including Gemini advisory generation) works
end-to-end without hardware dependencies.
"""
from __future__ import annotations

import math
import random
import time


from app.models.crowd import CrowdStatusResponse, DensityStatus, ZoneData

# ── Type alias ─────────────────────────────────────────────────────────────────
# (display_name, base_density_pct, zone_capacity)
ZoneSpec = tuple[str, int, int]

# ── Zone definitions ───────────────────────────────────────────────────────────
_ZONES: dict[str, ZoneSpec] = {
    "north_stand":    ("North Stand (Gate A)",  72, 17_500),
    "south_stand":    ("South Stand (Gate B)",  65, 17_500),
    "east_stand":     ("East Stand (Gate C)",   58, 12_000),
    "west_stand":     ("West Stand (Gate D)",   60, 12_000),
    "vip_section":    ("VIP Section",           45,  3_000),
    "food_court_n":   ("Food Court North",      80,  2_500),
    "food_court_s":   ("Food Court South",      74,  2_500),
    "main_concourse": ("Main Concourse",        68,  5_000),
}

_TOTAL_ZONE_CAPACITY: int = sum(cap for _, _, cap in _ZONES.values())

_ALERT_THRESHOLD: int = 80    # % — zones above this trigger an alert flag
_CRITICAL_THRESHOLD: int = 90


def _status(density: int) -> DensityStatus:
    """Map a numeric density to a categorical status."""
    if density >= _CRITICAL_THRESHOLD:
        return DensityStatus.CRITICAL
    if density >= _ALERT_THRESHOLD:
        return DensityStatus.HIGH
    if density >= 60:
        return DensityStatus.MODERATE
    return DensityStatus.OK


def _simulate_density(base: int) -> int:
    """Return a time-varying density based on *base* with sinusoidal fluctuation.

    The sine wave creates natural ebb-and-flow crowd patterns without
    requiring a database or external state.
    """
    now = time.time()
    # 5-minute cycle; each zone's base offset ensures they don't all peak together
    oscillation = math.sin(now / 300 + base) * 8
    noise = random.gauss(0, 3)
    return max(0, min(100, round(base + oscillation + noise)))


def get_crowd_status() -> CrowdStatusResponse:
    """Return a snapshot of current crowd density for all stadium zones."""
    zones: dict[str, ZoneData] = {}
    total_fans = 0

    for zone_id, (display_name, base_density, capacity) in _ZONES.items():
        density = _simulate_density(base_density)
        fan_count = round(capacity * density / 100)
        total_fans += fan_count

        zones[zone_id] = ZoneData(
            zone=display_name,
            density=density,
            fan_count=fan_count,
            status=_status(density),
            alert=density >= _ALERT_THRESHOLD,
        )

    overall_density = round(total_fans / _TOTAL_ZONE_CAPACITY * 100) if _TOTAL_ZONE_CAPACITY else 0
    alert_zones = sum(1 for z in zones.values() if z.alert)

    return CrowdStatusResponse(
        zones=zones,
        overall_density=overall_density,
        total_fans=total_fans,
        alert_zones=alert_zones,
    )


def zone_data_for_advisory() -> dict[str, dict[str, int | str]]:
    """Return a simplified zone dict suitable for the Gemini advisory prompt."""
    status_snapshot = get_crowd_status()
    return {
        data.zone: {"density": data.density, "status": data.status.value}
        for data in status_snapshot.zones.values()
    }
