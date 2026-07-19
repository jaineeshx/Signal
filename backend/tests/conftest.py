"""Shared pytest fixtures and test configuration for SIGNAL.

All tests run with MOCK_MODE enabled so no Gemini API key is required.
The Gemini functions are patched at the call site to prevent any accidental
network calls during the test suite. This ensures tests are:
  - Fast (no I/O)
  - Deterministic (no flaky external service)
  - Safe (no API quota consumption)
"""
from __future__ import annotations

import os

# ── Force mock mode BEFORE any app modules are imported ──────────────────────
# This must happen before `from app.main import app` to ensure pydantic-settings
# picks up the overrides rather than values from any .env file on disk.
os.environ["MOCK_MODE"] = "true"
os.environ["GEMINI_API_KEY"] = "test-key-not-used"

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app


# ── Client fixture ────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client() -> TestClient:
    """Synchronous test client for the FastAPI app.

    Session-scoped so a single app instance is shared across all tests
    in a test run, which significantly reduces startup overhead.
    """
    return TestClient(app)


# ── Gemini mock fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def mock_gemini_chat():
    """Patch ``generate_response`` in the chat router to return a deterministic string.

    Prevents all real Gemini SDK calls during chat endpoint tests.
    """
    with patch(
        "app.api.chat.generate_response",
        new_callable=AsyncMock,
        return_value="Mock AI response: SIGNAL is here to help you at FIFA World Cup 2026.",
    ) as mock:
        yield mock


@pytest.fixture
def mock_gemini_advisory():
    """Patch ``generate_crowd_advisory`` in the crowd router."""
    with patch(
        "app.api.crowd.generate_crowd_advisory",
        new_callable=AsyncMock,
        return_value=(
            "North Stand (Zone 1) is at 88% capacity — deploy 4 additional stewards to Gate A. "
            "Open overflow corridor B-3 to improve flow. "
            "Fan throughput should normalise within 15 minutes."
        ),
    ) as mock:
        yield mock


@pytest.fixture
def mock_gemini_nav():
    """Patch ``generate_navigation_directions`` in the navigation router."""
    with patch(
        "app.api.navigation.generate_navigation_directions",
        new_callable=AsyncMock,
        return_value=(
            "1. Head North along the main concourse.\n"
            "2. Turn right at Food Court 1.\n"
            "3. Take the escalator to Level 2.\n"
            "4. Your destination is on the left. Estimated time: 3 minutes."
        ),
    ) as mock:
        yield mock


@pytest.fixture
def mock_translate():
    """Patch ``translate`` in the navigation router."""
    with patch(
        "app.api.navigation.translate",
        new_callable=AsyncMock,
        return_value="Bienvenido al estadio. Su asiento está en la Sección 110.",
    ) as mock:
        yield mock
