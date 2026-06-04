"""FastAPI application entry point."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.database import create_tables
from core.redis_client import close_redis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI Wealth System API — env: %s", settings.app_env)
    try:
        await create_tables()
        logger.info("Database tables ready")
    except Exception as exc:
        logger.warning("Database setup failed (non-fatal in dev): %s", exc)
    yield
    # Shutdown
    await close_redis()
    logger.info("API shutdown complete")


app = FastAPI(
    title="AI Wealth System",
    description="Autonomous AI agent ecosystem for wealth generation research and execution.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────

from api.routers import agents, opportunities, revenue, memory, system
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(opportunities.router, prefix="/api/opportunities", tags=["Opportunities"])
app.include_router(revenue.router, prefix="/api/revenue", tags=["Revenue"])
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
app.include_router(system.router, prefix="/api/system", tags=["System"])

# ─── WebSocket ────────────────────────────────────────────────────────────────

from api.websockets.dashboard_ws import router as ws_router
app.include_router(ws_router)

# ─── Static / Dashboard ───────────────────────────────────────────────────────

import os
dashboard_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard")
if os.path.isdir(dashboard_path):
    app.mount("/assets", StaticFiles(directory=dashboard_path), name="dashboard_assets")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_dashboard():
    html_path = os.path.join(dashboard_path, "index.html")
    if os.path.isfile(html_path):
        with open(html_path) as f:
            return f.read()
    return HTMLResponse("<h1>AI Wealth System</h1><p>Dashboard not found.</p>")


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env, "version": "1.0.0"}
