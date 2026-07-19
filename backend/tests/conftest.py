"""Shared pytest fixtures for SIGNAL tests.

All tests run with MOCK_MODE enabled so no Gemini API key is required.
The Gemini module is patched at the source to prevent any accidental
network calls during the test suite.
"""
from __future__ import annotations

import os

# ── Force mock mode before any app modules are imported ───────────────────────
os.environ["MOCK_MODE"] = "true"
os.environ["GEMINI_API_KEY"] = ""  # ensure no stray key from shell env

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Synchronous test client for the FastAPI app (session-scoped for speed)."""
    return TestClient(app)


@pytest.fixture
def mock_gemini_chat():
    """Patch generate_response in the chat API to return a canned string."""
    with patch(
        "app.api.chat.generate_response",
        new_callable=AsyncMock,
        return_value="Mock AI response from SIGNAL.",
    ) as mock:
        yield mock


@pytest.fixture
def mock_gemini_advisory():
    """Patch generate_crowd_advisory in the crowd API."""
    with patch(
        "app.api.crowd.generate_crowd_advisory",
        new_callable=AsyncMock,
        return_value="Mock crowd advisory: North Stand at 85% — deploy additional stewards.",
    ) as mock:
        yield mock


@pytest.fixture
def mock_gemini_nav():
    """Patch generate_navigation_directions in the navigation API."""
    with patch(
        "app.api.navigation.generate_navigation_directions",
        new_callable=AsyncMock,
        return_value="1. Head North along the main concourse.\n2. Turn right at Food Court 1.\n3. Your destination is on the left.",
    ) as mock:
        yield mock


@pytest.fixture
def mock_translate():
    """Patch translate in the navigation API."""
    with patch(
        "app.api.navigation.translate",
        new_callable=AsyncMock,
        return_value="Texto traducido de prueba.",
    ) as mock:
        yield mock
