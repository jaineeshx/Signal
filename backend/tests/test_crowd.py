"""Tests for crowd management endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestCrowdStatusEndpoint:
    """Tests for GET /api/crowd/status."""

    def test_crowd_status_returns_200(self, client: TestClient):
        """Status endpoint should respond with HTTP 200."""
        response = client.get("/api/crowd/status")
        assert response.status_code == 200

    def test_crowd_status_schema(self, client: TestClient):
        """Status response must contain required top-level fields."""
        data = client.get("/api/crowd/status").json()
        assert "zones" in data
        assert "overall_density" in data
        assert "total_fans" in data
        assert "alert_zones" in data

    def test_crowd_status_has_eight_zones(self, client: TestClient):
        """Stadium has exactly 8 monitored zones."""
        data = client.get("/api/crowd/status").json()
        assert len(data["zones"]) == 8

    def test_crowd_zone_schema(self, client: TestClient):
        """Each zone must have zone, density, fan_count, status, alert fields."""
        data = client.get("/api/crowd/status").json()
        for zone_key, zone in data["zones"].items():
            assert "zone" in zone
            assert "density" in zone
            assert "fan_count" in zone
            assert "status" in zone
            assert "alert" in zone

    def test_crowd_density_in_valid_range(self, client: TestClient):
        """All density values must be between 0 and 100 inclusive."""
        data = client.get("/api/crowd/status").json()
        for zone in data["zones"].values():
            assert 0 <= zone["density"] <= 100

    def test_crowd_overall_density_in_valid_range(self, client: TestClient):
        """Overall stadium density must be 0–100."""
        data = client.get("/api/crowd/status").json()
        assert 0 <= data["overall_density"] <= 100

    def test_crowd_total_fans_positive(self, client: TestClient):
        """Total fan count should be a non-negative integer."""
        data = client.get("/api/crowd/status").json()
        assert data["total_fans"] >= 0

    def test_crowd_status_values_valid(self, client: TestClient):
        """Status values must be one of: OK, Moderate, High, Critical."""
        valid = {"OK", "Moderate", "High", "Critical"}
        data = client.get("/api/crowd/status").json()
        for zone in data["zones"].values():
            assert zone["status"] in valid


class TestCrowdAlertEndpoint:
    """Tests for POST /api/crowd/alert."""

    _SAMPLE_ZONE_DATA = {
        "zone_data": {
            "North Stand": {"density": 88, "status": "High"},
            "South Stand": {"density": 62, "status": "Moderate"},
        }
    }

    def test_crowd_alert_returns_200(self, client: TestClient, mock_gemini_advisory):
        """Alert endpoint with valid zone data should return 200."""
        response = client.post("/api/crowd/alert", json=self._SAMPLE_ZONE_DATA)
        assert response.status_code == 200

    def test_crowd_alert_has_advisory_field(self, client: TestClient, mock_gemini_advisory):
        """Response must contain 'advisory' string."""
        data = client.post("/api/crowd/alert", json=self._SAMPLE_ZONE_DATA).json()
        assert "advisory" in data
        assert isinstance(data["advisory"], str)
        assert len(data["advisory"]) > 0

    def test_crowd_alert_mock_flag(self, client: TestClient, mock_gemini_advisory):
        """Response must include 'mock' boolean."""
        data = client.post("/api/crowd/alert", json=self._SAMPLE_ZONE_DATA).json()
        assert "mock" in data
        assert isinstance(data["mock"], bool)


class TestAutoAdvisoryEndpoint:
    """Tests for GET /api/crowd/advisory."""

    def test_auto_advisory_returns_200(self, client: TestClient, mock_gemini_advisory):
        """Auto-advisory endpoint should return HTTP 200."""
        response = client.get("/api/crowd/advisory")
        assert response.status_code == 200

    def test_auto_advisory_has_advisory(self, client: TestClient, mock_gemini_advisory):
        """Auto-advisory response must contain a non-empty advisory string."""
        data = client.get("/api/crowd/advisory").json()
        assert "advisory" in data
        assert len(data["advisory"]) > 0
