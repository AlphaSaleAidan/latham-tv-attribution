"""Google Analytics 4 data models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class GA4DataPoint(BaseModel):
    """Single GA4 metric data point."""
    timestamp: datetime
    metric_name: str = Field(..., description="e.g. sessions, activeUsers, conversions")
    value: float
    city: Optional[str] = None
    region: Optional[str] = None
    source: Optional[str] = None
    medium: Optional[str] = None
    landing_page: Optional[str] = None


class GA4RealtimeSnapshot(BaseModel):
    """Real-time GA4 data snapshot."""
    captured_at: datetime
    active_users: int
    sessions_last_30_min: int
    top_cities: list[dict] = []
    top_sources: list[dict] = []
    top_pages: list[dict] = []


class GA4Config(BaseModel):
    """Configuration for GA4 integration."""
    property_id: str
    credentials_path: str
    metrics: list[str] = ["sessions", "activeUsers", "conversions", "newUsers"]
    dimensions: list[str] = ["city", "sessionSource", "sessionMedium", "dateHour"]
