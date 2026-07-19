"""SIGNAL — FastAPI application entry point.

Initialises the app, registers API routers, configures CORS, mounts the
static frontend, and sets up startup/shutdown logging.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import chat, crowd, health, navigation
from app.core.config import settings
from app.utils.logger import get_logger

# ── Logging ────────────────────────────────────────────────────────────────────
log_level = logging.DEBUG if settings.debug else logging.INFO
logger = get_logger(__name__, level=log_level)

# ── Lifecycle events ───────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    gemini_status = "LIVE" if settings.gemini_available else "MOCK"
    logger.info(
        "SIGNAL %s v%s started | Gemini: %s | Model: %s",
        settings.app_name,
        settings.app_version,
        gemini_status,
        settings.gemini_model,
    )
    yield
    logger.info("SIGNAL shutting down.")

# ── Application ────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "SIGNAL — Smart Intelligent Guide for Navigation and Live-operations. "
        "A GenAI-powered assistant for FIFA World Cup 2026 stadium operations."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── API routers ────────────────────────────────────────────────────────────────
API_PREFIX = "/api"

app.include_router(health.router,     prefix=API_PREFIX)
app.include_router(chat.router,       prefix=API_PREFIX)
app.include_router(crowd.router,      prefix=API_PREFIX)
app.include_router(navigation.router, prefix=API_PREFIX)

# ── Static frontend ────────────────────────────────────────────────────────────
_FRONTEND_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
)

if os.path.isdir(_FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
    logger.info("Frontend mounted from: %s", _FRONTEND_DIR)
else:
    logger.warning(
        "Frontend directory not found at '%s' — UI will not be served.", _FRONTEND_DIR
    )



