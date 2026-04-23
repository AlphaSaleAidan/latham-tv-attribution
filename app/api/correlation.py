"""Correlation analysis endpoints — the core of the attribution platform."""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from app.core.config import settings
from app.core.dependencies import get_db
from app.etl.trends import trends_etl
from app.services.correlation import correlation_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/correlation", tags=["Correlation Engine"])


@router.post("/analyze/{airing_id}")
async def analyze_single_airing(
    airing_id: str,
    db: Client = Depends(get_db),
):
    """Analyze correlation between a single TV airing and digital signals.

    Fetches Google Trends data for the airing's time window and computes
    lift metrics across all configured time windows.
    """
    # Get the airing
    result = db.table("tv_airings").select("*").eq("id", airing_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Airing not found")

    airing = result.data[0]

    # Fetch Trends data around the airing time
    trends_df = trends_etl.fetch_hourly_interest(
        search_terms=settings.trends_search_terms,
        hours_back=168,  # 7 days for baseline
        geo="US",
    )

    # Run correlation
    correlation = correlation_engine.correlate_airing(
        airing=airing,
        trends_data=trends_df if not trends_df.empty else None,
    )

    # Store result
    try:
        db.table("correlation_results").insert({
            "airing_id": airing_id,
            "airing_timestamp": airing["airing_timestamp"],
            "network": airing.get("network", ""),
            "dma_code": airing.get("dma_code"),
            "trends_lift": correlation.trends_lift,
            "ga4_session_lift": correlation.ga4_session_lift,
            "call_volume_lift": correlation.call_volume_lift,
            "composite_score": correlation.composite_score,
            "confidence": correlation.confidence,
            "signals_available": correlation.signals_available,
            "is_significant": correlation.is_significant,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        logger.warning(f"Could not store correlation result: {e}")

    return correlation.model_dump()


@router.post("/analyze-batch")
async def analyze_batch(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=200),
    db: Client = Depends(get_db),
):
    """Analyze correlation for multiple airings in a date range.

    Fetches Trends data once and correlates all airings against it.
    """
    query = db.table("tv_airings").select("*").order("airing_timestamp", desc=True)

    if start_date:
        query = query.gte("airing_timestamp", start_date.isoformat())
    if end_date:
        query = query.lte("airing_timestamp", end_date.isoformat())

    result = query.limit(limit).execute()

    if not result.data:
        return {"results": [], "total_analyzed": 0}

    # Fetch Trends data once for the full period
    trends_df = trends_etl.fetch_hourly_interest(
        search_terms=settings.trends_search_terms,
        hours_back=168,
        geo="US",
    )

    results = []
    for airing in result.data:
        try:
            correlation = correlation_engine.correlate_airing(
                airing=airing,
                trends_data=trends_df if not trends_df.empty else None,
            )
            results.append(correlation.model_dump())
        except Exception as e:
            logger.error(f"Error analyzing airing {airing.get('id')}: {e}")

    # Summary stats
    significant_count = sum(1 for r in results if r["is_significant"])
    avg_score = (
        sum(r["composite_score"] for r in results) / len(results)
        if results
        else 0
    )

    return {
        "results": results,
        "total_analyzed": len(results),
        "significant_count": significant_count,
        "significance_rate": round(significant_count / len(results) * 100, 1) if results else 0,
        "avg_composite_score": round(avg_score, 1),
    }


@router.get("/summary")
async def get_correlation_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    group_by: str = Query(default="network", enum=["network", "dma_code", "creative_id", "daypart"]),
    db: Client = Depends(get_db),
):
    """Get aggregated correlation summary grouped by a dimension.

    Useful for answering questions like:
    - Which network drives the most brand lift?
    - Which DMA is most responsive to TV ads?
    - Which creative performs best?
    """
    query = db.table("correlation_results").select("*")

    if start_date:
        query = query.gte("airing_timestamp", start_date.isoformat())
    if end_date:
        query = query.lte("airing_timestamp", end_date.isoformat())

    result = query.execute()

    if not result.data:
        return {"groups": [], "group_by": group_by}

    # Group and aggregate
    from collections import defaultdict
    groups = defaultdict(list)
    for row in result.data:
        key = row.get(group_by, "Unknown") or "Unknown"
        groups[key].append(row)

    summary = []
    for key, rows in groups.items():
        scores = [r["composite_score"] for r in rows if r.get("composite_score") is not None]
        significant = sum(1 for r in rows if r.get("is_significant"))

        summary.append({
            "group": key,
            "total_airings": len(rows),
            "avg_composite_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "max_composite_score": round(max(scores), 1) if scores else 0,
            "significant_airings": significant,
            "significance_rate": round(significant / len(rows) * 100, 1) if rows else 0,
        })

    summary.sort(key=lambda x: x["avg_composite_score"], reverse=True)

    return {"groups": summary, "group_by": group_by, "total_records": len(result.data)}
