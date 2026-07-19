"""Tests for navigation and translation endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestNavigationEndpoint:
    """Tests for POST /api/navigate."""

    def test_navigate_returns_200(self, client: TestClient, mock_gemini_nav):
        """Valid navigation request should return HTTP 200."""
        response = client.post(
            "/api/navigate",
            json={
                "from_location": "Gate A",
                "to_location": "Section 110",
                "language": "en",
            },
        )
        assert response.status_code == 200

    def test_navigate_response_schema(self, client: TestClient, mock_gemini_nav):
        """Navigation response must include required fields."""
        data = client.post(
            "/api/navigate",
            json={"from_location": "Gate A", "to_location": "Food Court 1", "language": "en"},
        ).json()
        assert "from_location" in data
        assert "to_location" in data
        assert "directions" in data
        assert "accessibility" in data
        assert "mock" in data

    def test_navigate_directions_not_empty(self, client: TestClient, mock_gemini_nav):
        """Directions string must not be empty."""
        data = client.post(
            "/api/navigate",
            json={"from_location": "Gate B", "to_location": "Medical Centre", "language": "en"},
        ).json()
        assert len(data["directions"]) > 0

    def test_navigate_accessibility_mode(self, client: TestClient, mock_gemini_nav):
        """Accessibility flag should be echoed in the response."""
        data = client.post(
            "/api/navigate",
            json={
                "from_location": "Gate D",
                "to_location": "Section 140",
                "accessibility": True,
                "language": "en",
            },
        ).json()
        assert data["accessibility"] is True

    def test_navigate_multilingual(self, client: TestClient, mock_gemini_nav):
        """Non-English language codes should be accepted."""
        for lang in ("es", "fr", "ar", "pt"):
            response = client.post(
                "/api/navigate",
                json={"from_location": "Gate A", "to_location": "VIP Lounge", "language": lang},
            )
            assert response.status_code == 200

    def test_navigate_same_location_returns_400(self, client: TestClient):
        """Start and destination must be different."""
        response = client.post(
            "/api/navigate",
            json={"from_location": "Gate A", "to_location": "Gate A", "language": "en"},
        )
        assert response.status_code == 400

    def test_navigate_empty_from_returns_422(self, client: TestClient):
        """Empty from_location should be rejected."""
        response = client.post(
            "/api/navigate",
            json={"from_location": "", "to_location": "Food Court 2", "language": "en"},
        )
        assert response.status_code == 422

    def test_navigate_invalid_language_returns_422(self, client: TestClient):
        """Unknown language code should be rejected with 422."""
        response = client.post(
            "/api/navigate",
            json={"from_location": "Gate A", "to_location": "Food Court 1", "language": "xx"},
        )
        assert response.status_code == 422


class TestLocationListEndpoint:
    """Tests for GET /api/locations."""

    def test_locations_returns_200(self, client: TestClient):
        response = client.get("/api/locations")
        assert response.status_code == 200

    def test_locations_returns_list(self, client: TestClient):
        data = client.get("/api/locations").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_locations_includes_gates(self, client: TestClient):
        """Known gates should be present in the location list."""
        data = client.get("/api/locations").json()
        for gate in ("gate a", "gate b", "gate c", "gate d"):
            assert gate in data

    def test_locations_includes_facilities(self, client: TestClient):
        """Core facilities should be present."""
        data = client.get("/api/locations").json()
        for facility in ("medical centre", "family zone", "fan zone"):
            assert facility in data


class TestTranslationEndpoint:
    """Tests for POST /api/translate."""

    def test_translate_returns_200(self, client: TestClient, mock_translate):
        response = client.post(
            "/api/translate",
            json={"text": "Welcome to the stadium!", "target_language": "es"},
        )
        assert response.status_code == 200

    def test_translate_response_schema(self, client: TestClient, mock_translate):
        data = client.post(
            "/api/translate",
            json={"text": "Gate A is to your left.", "target_language": "fr"},
        ).json()
        assert "original_text" in data
        assert "translated_text" in data
        assert "target_language" in data

    def test_translate_invalid_language(self, client: TestClient):
        response = client.post(
            "/api/translate",
            json={"text": "Hello", "target_language": "xx"},
        )
        assert response.status_code == 422

    def test_translate_empty_text_rejected(self, client: TestClient):
        response = client.post(
            "/api/translate",
            json={"text": "", "target_language": "es"},
        )
        assert response.status_code == 422


class TestHealthEndpoint:
    """Tests for GET /api/health and GET /api/info."""

    def test_health_returns_200(self, client: TestClient):
        assert client.get("/api/health").status_code == 200

    def test_health_schema(self, client: TestClient):
        data = client.get("/api/health").json()
        assert data["status"] == "ok"
        assert "service" in data
        assert "version" in data
        assert "mock_mode" in data

    def test_info_returns_200(self, client: TestClient):
        assert client.get("/api/info").status_code == 200

    def test_info_schema(self, client: TestClient):
        data = client.get("/api/info").json()
        assert "name" in data
        assert "total_capacity" in data
        assert "zones" in data
        assert "facilities" in data
        assert "gates" in data
