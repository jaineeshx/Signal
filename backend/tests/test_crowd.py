"""Comprehensive tests for crowd management endpoints.

Covers: crowd status schema, density range validation, zone count,
alert logic, AI advisory generation, and edge cases.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestCrowdStatusEndpoint:
    """Tests for GET /api/crowd/status."""

    def test_returns_200(self, client: TestClient):
        """Status endpoint must respond with HTTP 200."""
        assert client.get("/api/crowd/status").status_code == 200

    def test_top_level_schema(self, client: TestClient):
        """Response must contain all required top-level fields."""
        data = client.get("/api/crowd/status").json()
        assert "zones" in data
        assert "overall_density" in data
        assert "total_fans" in data
        assert "alert_zones" in data

    def test_exactly_eight_zones(self, client: TestClient):
        """Stadium must report exactly 8 monitored zones."""
        data = client.get("/api/crowd/status").json()
        assert len(data["zones"]) == 8

    def test_expected_zone_ids_present(self, client: TestClient):
        """All 8 named zone IDs must be present in the response."""
        expected = {
            "north_stand", "south_stand", "east_stand", "west_stand",
            "vip_section", "food_court_n", "food_court_s", "main_concourse",
        }
        data = client.get("/api/crowd/status").json()
        assert set(data["zones"].keys()) == expected

    def test_zone_schema_complete(self, client: TestClient):
        """Each zone must contain all required fields."""
        data = client.get("/api/crowd/status").json()
        for zone_key, zone in data["zones"].items():
            assert "zone" in zone,       f"Zone '{zone_key}' missing 'zone' field"
            assert "density" in zone,    f"Zone '{zone_key}' missing 'density' field"
            assert "fan_count" in zone,  f"Zone '{zone_key}' missing 'fan_count' field"
            assert "status" in zone,     f"Zone '{zone_key}' missing 'status' field"
            assert "alert" in zone,      f"Zone '{zone_key}' missing 'alert' field"

    def test_density_values_in_valid_range(self, client: TestClient):
        """All zone density values must be between 0 and 100 inclusive."""
        data = client.get("/api/crowd/status").json()
        for key, zone in data["zones"].items():
            assert 0 <= zone["density"] <= 100, f"Zone '{key}' density {zone['density']} out of range"

    def test_overall_density_in_valid_range(self, client: TestClient):
        """Stadium-wide density must be 0–100."""
        data = client.get("/api/crowd/status").json()
        assert 0 <= data["overall_density"] <= 100

    def test_total_fans_is_non_negative(self, client: TestClient):
        """Total fan count must be a non-negative integer."""
        data = client.get("/api/crowd/status").json()
        assert data["total_fans"] >= 0
        assert isinstance(data["total_fans"], int)

    def test_alert_zones_count_is_non_negative(self, client: TestClient):
        """Alert zone count must be ≥ 0 and ≤ total zones."""
        data = client.get("/api/crowd/status").json()
        assert 0 <= data["alert_zones"] <= len(data["zones"])

    @pytest.mark.parametrize("status_value", ["OK", "Moderate", "High", "Critical"])
    def test_status_values_are_valid_enum(self, client: TestClient, status_value: str):
        """Status values must belong to the DensityStatus enum."""
        data = client.get("/api/crowd/status").json()
        all_statuses = {z["status"] for z in data["zones"].values()}
        # At least one of the valid statuses must appear across zones
        assert all_statuses.issubset({"OK", "Moderate", "High", "Critical"})

    def test_fan_count_consistent_with_density(self, client: TestClient):
        """Fan count must be positive when density > 0."""
        data = client.get("/api/crowd/status").json()
        for zone in data["zones"].values():
            if zone["density"] > 0:
                assert zone["fan_count"] > 0

    def test_alert_flag_consistent_with_status(self, client: TestClient):
        """Alert flag must be True for zones with High or Critical status."""
        data = client.get("/api/crowd/status").json()
        for key, zone in data["zones"].items():
            if zone["status"] in ("High", "Critical"):
                assert zone["alert"] is True, (
                    f"Zone '{key}' has status '{zone['status']}' but alert is False"
                )

    def test_consecutive_calls_return_same_schema(self, client: TestClient):
        """Two consecutive calls should both return valid, structurally identical responses."""
        r1 = client.get("/api/crowd/status").json()
        r2 = client.get("/api/crowd/status").json()
        assert set(r1["zones"].keys()) == set(r2["zones"].keys())


class TestCrowdAlertEndpoint:
    """Tests for POST /api/crowd/alert."""

    _SAMPLE_ZONE_DATA = {
        "zone_data": {
            "North Stand": {"density": 88, "status": "High"},
            "South Stand": {"density": 62, "status": "Moderate"},
            "East Stand":  {"density": 45, "status": "OK"},
        }
    }

    def test_returns_200_with_zone_data(self, client: TestClient, mock_gemini_advisory):
        """POST with explicit zone data must return HTTP 200."""
        response = client.post("/api/crowd/alert", json=self._SAMPLE_ZONE_DATA)
        assert response.status_code == 200

    def test_returns_200_without_zone_data(self, client: TestClient, mock_gemini_advisory):
        """POST without zone data must auto-use live data and return HTTP 200."""
        response = client.post("/api/crowd/alert", json={})
        assert response.status_code == 200

    def test_advisory_field_is_non_empty_string(self, client: TestClient, mock_gemini_advisory):
        """Response must contain a non-empty 'advisory' string."""
        data = client.post("/api/crowd/alert", json=self._SAMPLE_ZONE_DATA).json()
        assert "advisory" in data
        assert isinstance(data["advisory"], str)
        assert len(data["advisory"].strip()) > 0

    def test_mock_field_is_boolean(self, client: TestClient, mock_gemini_advisory):
        """Response must include a boolean 'mock' field."""
        data = client.post("/api/crowd/alert", json=self._SAMPLE_ZONE_DATA).json()
        assert "mock" in data
        assert isinstance(data["mock"], bool)

    def test_high_density_zone_advisory_content(self, client: TestClient, mock_gemini_advisory):
        """Advisory for a high-density zone must be non-trivially long (> 50 chars)."""
        data = client.post("/api/crowd/alert", json=self._SAMPLE_ZONE_DATA).json()
        assert len(data["advisory"]) > 50


class TestAutoAdvisoryEndpoint:
    """Tests for GET /api/crowd/advisory."""

    def test_returns_200(self, client: TestClient, mock_gemini_advisory):
        """Auto-advisory endpoint must return HTTP 200."""
        assert client.get("/api/crowd/advisory").status_code == 200

    def test_crowd_advisory_internal_server_error(self, client: TestClient, mocker: MockerFixture) -> None:
        """Ensure that exceptions raised in the AI service are caught and return a 502 error."""
        mocker.patch(
            "app.api.crowd.generate_crowd_advisory",
            side_effect=RuntimeError("AI service offline")
        )
        response = client.get("/api/crowd/advisory")
        assert response.status_code == 502
        data = response.json()
        assert "temporarily unavailable" in data["detail"]

    def test_advisory_is_non_empty(self, client: TestClient, mock_gemini_advisory):
        """Advisory string must not be empty."""
        data = client.get("/api/crowd/advisory").json()
        assert "advisory" in data
        assert len(data["advisory"].strip()) > 0

    def test_advisory_has_mock_flag(self, client: TestClient, mock_gemini_advisory):
        """Auto-advisory must include a 'mock' boolean."""
        data = client.get("/api/crowd/advisory").json()
        assert isinstance(data.get("mock"), bool)
