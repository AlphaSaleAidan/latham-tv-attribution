"""Google Trends API endpoints."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.core.config import settings
from app.etl.trends import trends_etl

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trends", tags=["Google Trends"])


@router.get("/interest")
async def get_interest_over_time(
    search_terms: Optional[str] = Query(
        default=None,
        description="Comma-separated search terms. Defaults to config terms.",
    ),
    hours_back: int = Query(default=168, le=4320, description="Hours of history (max 180 days)"),
    geo: str = Query(default="US", description="Geographic scope"),
):
    """Fetch hourly Google Trends interest for search terms.

    Returns interest scores (0-100) over time.
    """
    terms = (
        [t.strip() for t in search_terms.split(",")]
        if search_terms
        else settings.trends_search_terms
    )

    df = trends_etl.fetch_hourly_interest(
        search_terms=terms,
        hours_back=hours_back,
        geo=geo,
    )

    if df.empty:
        return {"data": [], "terms": terms, "geo": geo}

    return {
        "data": df.to_dict("records"),
        "terms": terms,
        "geo": geo,
        "data_points": len(df),
    }


@router.get("/by-dma")
async def get_interest_by_dma(
    search_terms: Optional[str] = Query(default=None),
    timeframe: str = Query(default="now 7-d"),
):
    """Fetch search interest broken down by DMA region.

    Shows which geographic markets have highest search interest.
    """
    terms = (
        [t.strip() for t in search_terms.split(",")]
        if search_terms
        else settings.trends_search_terms[:3]  # Limit to 3 for DMA queries
    )

    df = trends_etl.fetch_interest_by_dma(
        search_terms=terms,
        timeframe=timeframe,
    )

    if df.empty:
        return {"data": [], "terms": terms}

    # Sort by interest score descending
    df = df.sort_values("interest_score", ascending=False)

    return {
        "data": df.to_dict("records"),
        "terms": terms,
        "total_dmas": df["dma_name"].nunique(),
    }


@router.get("/related-queries")
async def get_related_queries(
    search_term: str = Query(..., description="Single search term"),
    geo: str = Query(default="US"),
    timeframe: str = Query(default="now 7-d"),
):
    """Get related and rising queries for a search term.

    Shows what people search after/alongside a given term.
    Useful for understanding TV ad impact on search behavior.
    """
    result = trends_etl.fetch_related_queries(
        search_term=search_term,
        geo=geo,
        timeframe=timeframe,
    )

    return {
        "search_term": search_term,
        "geo": geo,
        "top_queries": result["top"],
        "rising_queries": result["rising"],
    }


@router.get("/spikes")
async def detect_trend_spikes(
    search_terms: Optional[str] = Query(default=None),
    hours_back: int = Query(default=168, le=4320),
    geo: str = Query(default="US"),
    sigma_threshold: float = Query(default=2.0, ge=1.0, le=5.0),
):
    """Detect significant spikes in search interest.

    Returns timestamps where search interest exceeded {sigma_threshold}
    standard deviations above the mean baseline.
    """
    terms = (
        [t.strip() for t in search_terms.split(",")]
        if search_terms
        else settings.trends_search_terms
    )

    df = trends_etl.fetch_hourly_interest(
        search_terms=terms,
        hours_back=hours_back,
        geo=geo,
    )

    if df.empty:
        return {"spikes": [], "terms": terms}

    spikes = trends_etl.detect_spikes(df, sigma_threshold=sigma_threshold)

    return {
        "spikes": spikes,
        "terms": terms,
        "geo": geo,
        "total_data_points": len(df),
        "sigma_threshold": sigma_threshold,
    }
