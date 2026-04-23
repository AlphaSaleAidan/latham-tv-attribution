"""Google Search Console ETL — fetch organic search performance data.

Requires:
- Verified site in Search Console
- Service account with access

Not implemented yet — waiting for credentials from Latham team.
"""

import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)


class SearchConsoleETL:
    """Fetch and process Search Console data for TV attribution."""

    def __init__(self):
        self._client = None
        self._initialized = False

    @property
    def is_available(self) -> bool:
        """Check if Search Console integration is configured."""
        return bool(settings.gsc_site_url)

    def fetch_brand_keyword_performance(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        brand_keywords: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Fetch search performance for brand-related keywords.

        Returns DataFrame with: date, query, clicks, impressions, ctr, position
        """
        if not self.is_available:
            return pd.DataFrame()

        # TODO: Implement when credentials are available
        logger.info("Search Console fetch — not yet implemented")
        return pd.DataFrame()


# Singleton
search_console_etl = SearchConsoleETL()
