"""CallRail ETL — fetch phone call tracking data.

Requires:
- CallRail API key
- CallRail Account ID

Not implemented yet — waiting for credentials.
"""

import logging
from datetime import datetime
from typing import Optional

import httpx
import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)

CALLRAIL_BASE_URL = "https://api.callrail.com/v3"


class CallRailETL:
    """Fetch and process CallRail call data for TV attribution."""

    def __init__(self):
        self._headers = {}
        if settings.callrail_api_key:
            self._headers = {
                "Authorization": f"Token token={settings.callrail_api_key}",
                "Content-Type": "application/json",
            }

    @property
    def is_available(self) -> bool:
        """Check if CallRail integration is configured."""
        return bool(settings.callrail_api_key and settings.callrail_account_id)

    async def fetch_calls(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Fetch call records from CallRail.

        Returns DataFrame with: call_timestamp, caller_city, caller_state,
                                duration_seconds, is_first_call, tracking_number
        """
        if not self.is_available:
            return pd.DataFrame()

        # TODO: Implement when credentials are available
        # Endpoint: GET /a/{account_id}/calls.json
        logger.info("CallRail fetch — not yet implemented")
        return pd.DataFrame()


# Singleton
callrail_etl = CallRailETL()
