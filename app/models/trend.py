"""Google Trends data models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TrendDataPoint(BaseModel):
    """Single Google Trends data point."""
    timestamp: datetime
    search_term: str
    interest_score: int = Field(..., ge=0, le=100, description="Google Trends interest (0-100)")
    geo: Optional[str] = Field(None, description="Geographic filter (DMA or country)")
    is_partial: bool = False


class TrendQuery(BaseModel):
    """Request to fetch Google Trends data."""
    search_terms: list[str] = Field(default_factory=list, description="Terms to query")
    geo: str = Field(default="US", description="Geographic scope (US or DMA code)")
    timeframe: str = Field(default="now 7-d", description="Trends timeframe")


class TrendSpike(BaseModel):
    """Detected spike in search interest."""
    search_term: str
    spike_timestamp: datetime
    peak_interest: int
    baseline_interest: float
    lift_percentage: float = Field(..., description="% increase above baseline")
    geo: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class TrendCorrelation(BaseModel):
    """Correlation between a TV airing and a Trends spike."""
    airing_id: str
    airing_timestamp: datetime
    network: str
    dma_code: Optional[str]
    search_term: str
    time_window_minutes: int
    baseline_interest: float
    post_airing_interest: float
    lift_percentage: float
    lift_absolute: float
    confidence_score: float
    is_significant: bool = Field(..., description="Whether lift exceeds 2σ threshold")
