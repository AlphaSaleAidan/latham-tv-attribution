"""Google Trends ETL — fetch and store search interest data.

Uses pytrends (unofficial Google Trends API) to pull:
- Hourly interest over time for brand terms
- Interest by DMA region
- Related queries

Rate limiting is critical — Google blocks aggressive scrapers.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd
from pytrends.request import TrendReq

from app.core.config import settings

logger = logging.getLogger(__name__)

# DMA codes for major US markets (Nielsen)
MAJOR_DMAS = {
    "501": "New York",
    "803": "Los Angeles",
    "602": "Chicago",
    "504": "Philadelphia",
    "506": "Boston",
    "511": "Washington DC",
    "524": "Atlanta",
    "753": "Phoenix",
    "623": "Dallas-Ft Worth",
    "618": "Houston",
    "539": "Tampa-St Pete",
    "528": "Miami-Ft Lauderdale",
    "527": "Indianapolis",
    "505": "Detroit",
    "534": "Orlando",
    "510": "Cleveland",
    "517": "Charlotte",
    "659": "Nashville",
    "548": "West Palm Beach",
    "West Palm Beach": "548",
}


class GoogleTrendsETL:
    """Fetch and process Google Trends data for TV attribution."""

    def __init__(self):
        self.pytrends = TrendReq(
            hl="en-US",
            tz=300,  # EST
            timeout=(10, 30),
            retries=3,
            backoff_factor=1.0,
        )
        self._last_request_time = 0.0

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < settings.trends_rate_limit_delay:
            sleep_time = settings.trends_rate_limit_delay - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def fetch_hourly_interest(
        self,
        search_terms: list[str],
        hours_back: int = 168,  # 7 days
        geo: str = "US",
    ) -> pd.DataFrame:
        """Fetch hourly search interest for given terms.

        Args:
            search_terms: List of search terms (max 5 per request)
            hours_back: How many hours of history to fetch
            geo: Geographic scope (US, or DMA like 'US-NY-501')

        Returns:
            DataFrame with columns: timestamp, search_term, interest_score, geo
        """
        all_data = []

        # pytrends only allows 5 terms per request
        for i in range(0, len(search_terms), 5):
            batch = search_terms[i : i + 5]
            self._rate_limit()

            try:
                # For hourly data, use "now {hours}-H" format (max 7 days)
                if hours_back <= 4:
                    timeframe = f"now {hours_back}-H"
                elif hours_back <= 168:
                    days = hours_back // 24
                    timeframe = f"now {days}-d"
                else:
                    timeframe = "today 3-m"

                self.pytrends.build_payload(
                    kw_list=batch,
                    timeframe=timeframe,
                    geo=geo,
                )

                df = self.pytrends.interest_over_time()

                if df.empty:
                    logger.warning(f"No Trends data for {batch} in {geo}")
                    continue

                # Reshape from wide to long format
                for term in batch:
                    if term in df.columns:
                        term_data = df[[term, "isPartial"]].copy()
                        term_data = term_data.reset_index()
                        term_data.columns = ["timestamp", "interest_score", "is_partial"]
                        term_data["search_term"] = term
                        term_data["geo"] = geo
                        all_data.append(term_data)

            except Exception as e:
                logger.error(f"Error fetching trends for {batch}: {e}")
                # Back off more on errors
                time.sleep(settings.trends_rate_limit_delay * 3)

        if not all_data:
            return pd.DataFrame(columns=["timestamp", "search_term", "interest_score", "geo", "is_partial"])

        result = pd.concat(all_data, ignore_index=True)
        result["timestamp"] = pd.to_datetime(result["timestamp"], utc=True)
        return result

    def fetch_interest_by_dma(
        self,
        search_terms: list[str],
        timeframe: str = "now 7-d",
    ) -> pd.DataFrame:
        """Fetch search interest broken down by DMA region.

        Returns:
            DataFrame with columns: dma_code, dma_name, search_term, interest_score
        """
        all_data = []

        for i in range(0, len(search_terms), 5):
            batch = search_terms[i : i + 5]
            self._rate_limit()

            try:
                self.pytrends.build_payload(
                    kw_list=batch,
                    timeframe=timeframe,
                    geo="US",
                )

                df = self.pytrends.interest_by_region(
                    resolution="DMA",
                    inc_low_vol=True,
                    inc_geo_code=True,
                )

                if df.empty:
                    continue

                df = df.reset_index()
                for term in batch:
                    if term in df.columns:
                        term_data = df[["geoName", "geoCode", term]].copy()
                        term_data.columns = ["dma_name", "dma_code", "interest_score"]
                        term_data["search_term"] = term
                        all_data.append(term_data)

            except Exception as e:
                logger.error(f"Error fetching DMA interest for {batch}: {e}")
                time.sleep(settings.trends_rate_limit_delay * 3)

        if not all_data:
            return pd.DataFrame(columns=["dma_name", "dma_code", "search_term", "interest_score"])

        return pd.concat(all_data, ignore_index=True)

    def fetch_related_queries(
        self,
        search_term: str,
        geo: str = "US",
        timeframe: str = "now 7-d",
    ) -> dict:
        """Fetch related and rising queries for a term.

        Useful for understanding what people search after seeing a TV ad.
        """
        self._rate_limit()

        try:
            self.pytrends.build_payload(
                kw_list=[search_term],
                timeframe=timeframe,
                geo=geo,
            )
            related = self.pytrends.related_queries()
            result = {"top": None, "rising": None}

            if search_term in related:
                if related[search_term]["top"] is not None:
                    result["top"] = related[search_term]["top"].to_dict("records")
                if related[search_term]["rising"] is not None:
                    result["rising"] = related[search_term]["rising"].to_dict("records")

            return result

        except Exception as e:
            logger.error(f"Error fetching related queries for '{search_term}': {e}")
            return {"top": None, "rising": None}

    def detect_spikes(
        self,
        df: pd.DataFrame,
        sigma_threshold: float = 2.0,
        min_absolute_lift: int = 10,
    ) -> list[dict]:
        """Detect significant spikes in Trends data above baseline.

        Args:
            df: DataFrame from fetch_hourly_interest
            sigma_threshold: Number of standard deviations for significance
            min_absolute_lift: Minimum absolute interest point increase

        Returns:
            List of spike dictionaries with timestamp, lift, confidence
        """
        spikes = []

        for term in df["search_term"].unique():
            term_data = df[df["search_term"] == term].sort_values("timestamp")

            if len(term_data) < 10:
                continue

            scores = term_data["interest_score"].values
            mean = scores.mean()
            std = scores.std()

            if std == 0:
                continue

            for _, row in term_data.iterrows():
                z_score = (row["interest_score"] - mean) / std
                lift_abs = row["interest_score"] - mean
                lift_pct = (lift_abs / mean * 100) if mean > 0 else 0

                if z_score >= sigma_threshold and lift_abs >= min_absolute_lift:
                    spikes.append({
                        "search_term": term,
                        "spike_timestamp": row["timestamp"],
                        "peak_interest": int(row["interest_score"]),
                        "baseline_interest": round(mean, 1),
                        "lift_percentage": round(lift_pct, 1),
                        "lift_absolute": round(lift_abs, 1),
                        "z_score": round(z_score, 2),
                        "geo": row.get("geo", "US"),
                        "confidence": min(1.0, round(z_score / 4.0, 2)),  # Normalize to 0-1
                    })

        return sorted(spikes, key=lambda x: x["lift_percentage"], reverse=True)


# Singleton
trends_etl = GoogleTrendsETL()
