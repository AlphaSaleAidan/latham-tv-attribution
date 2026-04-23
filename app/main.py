"""Latham Pools TV Attribution Platform — FastAPI Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import airings, trends, correlation

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Latham TV Attribution Platform starting up")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Trends search terms: {settings.trends_search_terms}")
    yield
    logger.info("👋 Shutting down")


app = FastAPI(
    title="Latham Pools TV Attribution Platform",
    description=(
        "Correlate TV commercial airings with digital lead generation signals "
        "to measure TV's impact on the Latham Pools business."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(airings.router, prefix="/api/v1")
app.include_router(trends.router, prefix="/api/v1")
app.include_router(correlation.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check and API info."""
    return {
        "name": "Latham Pools TV Attribution Platform",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "airings": "/api/v1/airings",
            "trends": "/api/v1/trends",
            "correlation": "/api/v1/correlation",
        },
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    from app.core.database import health_check

    db_healthy = False
    try:
        db_healthy = health_check()
    except Exception:
        pass

    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected",
        "environment": settings.app_env,
        "integrations": {
            "google_trends": "available",  # Always available (no auth)
            "ga4": "configured" if settings.ga4_property_id else "not_configured",
            "search_console": "configured" if settings.gsc_site_url else "not_configured",
            "callrail": "configured" if settings.callrail_api_key else "not_configured",
        },
    }
