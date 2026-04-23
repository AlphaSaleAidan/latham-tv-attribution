"""Correlation engine models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TimeWindow(BaseModel):
    """Time window configuration for correlation analysis."""
    label: str
    minutes: int
    weight: float = Field(default=1.0, description="Importance weight for scoring")


# Default time windows for analysis
DEFAULT_TIME_WINDOWS = [
    TimeWindow(label="immediate", minutes=30, weight=1.0),
    TimeWindow(label="short", minutes=120, weight=0.8),
    TimeWindow(label="medium", minutes=1440, weight=0.5),   # 24 hours
    TimeWindow(label="extended", minutes=4320, weight=0.3),  # 72 hours
]


class CorrelationResult(BaseModel):
    """Result of correlating a single airing with digital signals."""
    airing_id: str
    airing_timestamp: datetime
    network: str
    dma_code: Optional[str]
    creative_id: Optional[str]

    # Signals by time window
    trends_lift: dict[str, float] = Field(default_factory=dict, description="Trends lift by window label")
    ga4_session_lift: dict[str, float] = Field(default_factory=dict)
    ga4_conversion_lift: dict[str, float] = Field(default_factory=dict)
    search_console_lift: dict[str, float] = Field(default_factory=dict)
    call_volume_lift: dict[str, float] = Field(default_factory=dict)
    qr_scan_lift: dict[str, float] = Field(default_factory=dict)

    # Composite scores
    composite_score: float = Field(..., description="Weighted composite attribution score (0-100)")
    confidence: float = Field(..., ge=0.0, le=1.0)
    signals_available: int = Field(..., description="How many data sources had data")
    is_significant: bool = False


class CampaignSummary(BaseModel):
    """Aggregated attribution results for a campaign or time period."""
    period_start: datetime
    period_end: datetime
    total_airings: int
    total_spend: float
    total_estimated_impressions: int

    # Aggregate lift metrics
    avg_trends_lift: float
    avg_session_lift: float
    avg_conversion_lift: float
    avg_call_lift: float

    # Top performers
    best_network: Optional[str] = None
    best_daypart: Optional[str] = None
    best_creative: Optional[str] = None
    best_dma: Optional[str] = None

    # Significance
    significant_airings: int
    significance_rate: float = Field(..., description="% of airings with significant lift")
    avg_composite_score: float


class BaselineConfig(BaseModel):
    """Configuration for baseline calculation."""
    lookback_days: int = Field(default=7, description="Days to look back for baseline")
    same_day_of_week: bool = Field(default=True, description="Match same day of week")
    same_hour: bool = Field(default=True, description="Match same hour of day")
    exclude_airing_windows: bool = Field(default=True, description="Exclude known airing windows from baseline")
    sigma_threshold: float = Field(default=2.0, description="Standard deviations for significance")
