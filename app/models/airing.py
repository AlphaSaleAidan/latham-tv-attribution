"""TV airing data models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AiringBase(BaseModel):
    """Base TV airing fields."""
    airing_timestamp: datetime = Field(..., description="When the ad aired (UTC)")
    network: str = Field(..., description="TV network (e.g., ESPN, HGTV)")
    dma_code: Optional[str] = Field(None, description="Nielsen DMA code")
    dma_name: Optional[str] = Field(None, description="DMA name (e.g., 'New York')")
    creative_id: Optional[str] = Field(None, description="ISCI code or creative identifier")
    creative_name: Optional[str] = Field(None, description="Human-readable creative name")
    duration_seconds: Optional[int] = Field(None, description="Ad duration in seconds")
    estimated_impressions: Optional[int] = Field(None, description="Estimated viewer impressions")
    spend: Optional[float] = Field(None, description="Cost for this airing in USD")
    daypart: Optional[str] = Field(None, description="Daypart (e.g., 'Primetime', 'Daytime')")
    program_name: Optional[str] = Field(None, description="Program during which ad aired")


class AiringCreate(AiringBase):
    """Schema for creating a new airing record."""
    pass


class Airing(AiringBase):
    """Full airing record with DB fields."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AiringCSVUpload(BaseModel):
    """Response from CSV upload endpoint."""
    rows_imported: int
    rows_skipped: int
    errors: list[str] = []
    sample_records: list[dict] = []


class AiringFilter(BaseModel):
    """Query filters for airings."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    network: Optional[str] = None
    dma_code: Optional[str] = None
    creative_id: Optional[str] = None
    min_impressions: Optional[int] = None
