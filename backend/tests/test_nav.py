"""Comprehensive tests for navigation, translation, health, and location endpoints.

Covers: direction generation, accessibility mode, all language codes,
same-location guard, location catalogue validation, translation schema,
health check schema, and stadium info schema.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestNavigationEndpoint:
    """Tests for POST /api/navigate."""

    def test_valid_request_returns_200(self, client: TestClient, mock_gemini_nav):
        """A valid navigation request must return HTTP 200."""
        response = client.post(
            "/api/navigate",
            json={"from_location": "Gate A", "to_location": "Section 110", "language": "en"},
        )
        assert response.status_code == 200

    def test_response_schema_complete(self, client: TestClient, mock_gemini_nav):
        """Navigation response must include all required fields."""
        data = client.post(
            "/api/navigate",
            json={"from_location": "Gate A", "to_location": "Food Court 1", "language": "en"},
        ).json()
        assert "from_location" in data
        assert "to_location" in data
        assert "directions" in data
        assert "accessibility" in data
        assert "mock" in data

    def test_directions_not_empty(self, client: TestClient, mock_gemini_nav):
        """Directions string must be non-empty."""
        data = client.post(
            "/api/navigate",
            json={"from_location": "Gate B", "to_location": "Medical Centre", "language": "en"},
        ).json()
        assert len(data["directions"]) > 0

    def test_accessibility_flag_echoed_true(self, client: TestClient, mock_gemini_nav):
        """When accessibility=True is requested, the response must echo True."""
        data = client.post(
            "/api/navigate",
            json={"from_location": "Gate D", "to_location": "Section 140", "accessibility": True, "language": "en"},
        ).json()
        assert data["accessibility"] is True

    def test_accessibility_flag_defaults_false(self, client: TestClient, mock_gemini_nav):
        """When accessibility is omitted, it must default to False in the response."""
        data = client.post(
            "/api/navigate",
            json={"from_location": "Gate A", "to_location": "VIP Lounge", "language": "en"},
        ).json()
        assert data["accessibility"] is False

    @pytest.mark.parametrize("language", ["es", "fr", "ar", "pt", "de", "ja", "ko"])
    def test_all_non_english_languages_accepted(self, client: TestClient, mock_gemini_nav, language: str):
        """All 7 non-English language codes must be accepted."""
        response = client.post(
            "/api/navigate",
            json={"from_location": "Gate A", "to_location": "Food Court 2", "language": language},
        )
        assert response.status_code == 200

    def test_same_location_returns_400(self, client: TestClient):
        """Identical start and destination must return HTTP 400."""
        response = client.post(
            "/api/navigate",
            json={"from_location": "Gate A", "to_location": "Gate A", "language": "en"},
        )
        assert response.status_code == 400

    def test_same_location_case_insensitive(self, client: TestClient):
        """Same-location check must be case-insensitive."""
        response = client.post(
            "/api/navigate",
            json={"from_location": "gate a", "to_location": "Gate A", "language": "en"},
        )
        assert response.status_code == 400

    def test_empty_from_location_returns_422(self, client: TestClient):
        """Empty from_location must be rejected."""
        response = client.post(
            "/api/navigate",
            json={"from_location": "", "to_location": "Food Court 2", "language": "en"},
        )
        assert response.status_code == 422

    def test_empty_to_location_returns_422(self, client: TestClient):
        """Empty to_location must be rejected."""
        response = client.post(
            "/api/navigate",
            json={"from_location": "Gate A", "to_location": "", "language": "en"},
        )
        assert response.status_code == 422

    def test_invalid_language_returns_422(self, client: TestClient):
        """Unknown language code must be rejected."""
        response = client.post(
            "/api/navigate",
            json={"from_location": "Gate A", "to_location": "Food Court 1", "language": "xx"},
        )
        assert response.status_code == 422

    def test_location_preserved_in_response(self, client: TestClient, mock_gemini_nav):
        """from_location and to_location must be echoed in the response."""
        data = client.post(
            "/api/navigate",
            json={"from_location": "Gate B", "to_location": "Prayer Room", "language": "en"},
        ).json()
        assert "gate b" in data["from_location"].lower()
        assert "prayer room" in data["to_location"].lower()


class TestLocationListEndpoint:
    """Tests for GET /api/locations."""

    def test_returns_200(self, client: TestClient):
        """Locations endpoint must return HTTP 200."""
        assert client.get("/api/locations").status_code == 200

    def test_returns_non_empty_list(self, client: TestClient):
        """Response must be a non-empty list."""
        data = client.get("/api/locations").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_returns_at_least_30_locations(self, client: TestClient):
        """Stadium catalogue must contain at least 30 named locations."""
        data = client.get("/api/locations").json()
        assert len(data) >= 30

    @pytest.mark.parametrize("gate", ["gate a", "gate b", "gate c", "gate d"])
    def test_all_gates_present(self, client: TestClient, gate: str):
        """All 4 stadium gates must appear in the location catalogue."""
        data = client.get("/api/locations").json()
        assert gate in data

    @pytest.mark.parametrize("facility", [
        "medical centre", "family zone", "fan zone",
        "accessibility services", "lost and found", "prayer room",
    ])
    def test_key_facilities_present(self, client: TestClient, facility: str):
        """All key fan-service facilities must appear in the catalogue."""
        data = client.get("/api/locations").json()
        assert facility in data

    def test_list_is_sorted(self, client: TestClient):
        """Location list must be returned in alphabetical order."""
        data = client.get("/api/locations").json()
        assert data == sorted(data)

    def test_no_duplicate_entries(self, client: TestClient):
        """Location list must not contain duplicate entries."""
        data = client.get("/api/locations").json()
        assert len(data) == len(set(data))


class TestTranslationEndpoint:
    """Tests for POST /api/translate."""

    def test_valid_request_returns_200(self, client: TestClient, mock_translate):
        """Valid translation request must return HTTP 200."""
        response = client.post(
            "/api/translate",
            json={"text": "Welcome to the stadium!", "target_language": "es"},
        )
        assert response.status_code == 200

    def test_response_schema_complete(self, client: TestClient, mock_translate):
        """Translation response must include all required fields."""
        data = client.post(
            "/api/translate",
            json={"text": "Gate A is to your left.", "target_language": "fr"},
        ).json()
        assert "original_text" in data
        assert "translated_text" in data
        assert "target_language" in data
        assert "mock" in data

    def test_original_text_preserved(self, client: TestClient, mock_translate):
        """original_text in the response must match the input."""
        text = "Your seat is in Section 110."
        data = client.post(
            "/api/translate",
            json={"text": text, "target_language": "de"},
        ).json()
        assert data["original_text"] == text

    @pytest.mark.parametrize("language", ["es", "fr", "ar", "pt", "de", "ja", "ko"])
    def test_all_target_languages_accepted(self, client: TestClient, mock_translate, language: str):
        """All 7 non-English target languages must be accepted."""
        response = client.post(
            "/api/translate",
            json={"text": "Gate A is to your left.", "target_language": language},
        )
        assert response.status_code == 200

    def test_invalid_language_returns_422(self, client: TestClient):
        """Unknown language code must be rejected."""
        response = client.post(
            "/api/translate",
            json={"text": "Hello", "target_language": "xx"},
        )
        assert response.status_code == 422

    def test_empty_text_returns_422(self, client: TestClient):
        """Empty text must be rejected."""
        response = client.post(
            "/api/translate",
            json={"text": "", "target_language": "es"},
        )
        assert response.status_code == 422

    def test_whitespace_only_text_returns_422(self, client: TestClient):
        """Whitespace-only text must be rejected."""
        response = client.post(
            "/api/translate",
            json={"text": "    ", "target_language": "es"},
        )
        assert response.status_code == 422


class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_returns_200(self, client: TestClient):
        """Health endpoint must return HTTP 200."""
        assert client.get("/api/health").status_code == 200

    def test_status_field_is_ok(self, client: TestClient):
        """'status' field must be 'ok' when the service is healthy."""
        data = client.get("/api/health").json()
        assert data["status"] == "ok"

    def test_schema_complete(self, client: TestClient):
        """Health response must include all required fields."""
        data = client.get("/api/health").json()
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "mock_mode" in data
        assert "gemini_configured" in data

    def test_mock_mode_is_boolean(self, client: TestClient):
        """'mock_mode' must be a boolean."""
        data = client.get("/api/health").json()
        assert isinstance(data["mock_mode"], bool)

    def test_service_name_is_signal(self, client: TestClient):
        """'service' must be 'SIGNAL'."""
        data = client.get("/api/health").json()
        assert data["service"] == "SIGNAL"


class TestStadiumInfoEndpoint:
    """Tests for GET /api/info."""

    def test_returns_200(self, client: TestClient):
        """Stadium info endpoint must return HTTP 200."""
        assert client.get("/api/info").status_code == 200

    def test_schema_complete(self, client: TestClient):
        """Stadium info response must contain all required fields."""
        data = client.get("/api/info").json()
        assert "name" in data
        assert "total_capacity" in data
        assert "zones" in data
        assert "facilities" in data
        assert "gates" in data

    def test_capacity_is_positive(self, client: TestClient):
        """Stadium capacity must be a positive integer."""
        data = client.get("/api/info").json()
        assert isinstance(data["total_capacity"], int)
        assert data["total_capacity"] > 0

    def test_zones_list_non_empty(self, client: TestClient):
        """Stadium must have at least one zone."""
        data = client.get("/api/info").json()
        assert isinstance(data["zones"], list)
        assert len(data["zones"]) > 0

    def test_gates_list_non_empty(self, client: TestClient):
        """Stadium must have at least one gate."""
        data = client.get("/api/info").json()
        assert isinstance(data["gates"], list)
        assert len(data["gates"]) > 0

    def test_facilities_list_non_empty(self, client: TestClient):
        """Stadium must have at least one named facility."""
        data = client.get("/api/info").json()
        assert isinstance(data["facilities"], list)
        assert len(data["facilities"]) > 0
