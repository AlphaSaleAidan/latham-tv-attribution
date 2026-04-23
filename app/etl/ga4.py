"""Google Analytics 4 ETL — fetch website traffic and conversion data.

Requires:
- GA4 Property ID
- Service account JSON with Viewer role on the GA4 property

Not implemented yet — waiting for credentials from Latham team.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)


class GA4ETL:
    """Fetch and process GA4 data for TV attribution."""

    def __init__(self):
        self._client = None
        self._initialized = False

    def _ensure_client(self):
        """Initialize GA4 client if credentials are available."""
        if self._initialized:
            return self._client is not None

        if not settings.ga4_property_id or not settings.ga4_credentials_path:
            logger.info("GA4 not configured — skipping initialization")
            self._initialized = True
            return False

        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(
                settings.ga4_credentials_path,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )
            self._client = BetaAnalyticsDataClient(credentials=credentials)
            self._initialized = True
            logger.info(f"GA4 client initialized for property {settings.ga4_property_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize GA4 client: {e}")
            self._initialized = True
            return False

    @property
    def is_available(self) -> bool:
        """Check if GA4 integration is configured and available."""
        return self._ensure_client()

    def fetch_sessions_over_time(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        dimensions: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Fetch session data over time from GA4.

        Returns DataFrame with columns: timestamp, value, geo, source, medium
        """
        if not self.is_available:
            return pd.DataFrame()

        # TODO: Implement when credentials are available
        # Will use BetaAnalyticsDataClient.run_report()
        logger.info("GA4 fetch_sessions_over_time — not yet implemented")
        return pd.DataFrame()

    def fetch_realtime(self) -> dict:
        """Fetch real-time GA4 data.

        Returns dict with active_users, sessions_last_30_min, top cities/sources.
        """
        if not self.is_available:
            return {"active_users": 0, "error": "GA4 not configured"}

        # TODO: Implement when credentials are available
        # Will use BetaAnalyticsDataClient.run_realtime_report()
        logger.info("GA4 fetch_realtime — not yet implemented")
        return {"active_users": 0, "note": "Not yet implemented"}


# Singleton
ga4_etl = GA4ETL()
