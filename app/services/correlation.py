"""Correlation engine — match TV airings to digital signal lifts.

Core methodology:
1. For each TV airing, look at digital signals in 4 time windows post-airing
2. Compare post-airing signals to a 7-day rolling baseline (same day/hour)
3. Apply adstock decay model for extended-window analysis
4. Score correlations by lift magnitude, statistical significance, and geo match
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np
import pandas as pd

from app.models.correlation import (
    BaselineConfig,
    CorrelationResult,
    DEFAULT_TIME_WINDOWS,
    TimeWindow,
)

logger = logging.getLogger(__name__)


class CorrelationEngine:
    """Correlate TV airings with digital signal changes."""

    def __init__(self, baseline_config: Optional[BaselineConfig] = None):
        self.config = baseline_config or BaselineConfig()

    def compute_baseline(
        self,
        signal_data: pd.DataFrame,
        target_timestamp: datetime,
        geo: Optional[str] = None,
    ) -> tuple[float, float]:
        """Compute baseline mean and std for a signal at a given timestamp.

        Uses 7-day lookback, matching same day-of-week and hour for accuracy.

        Args:
            signal_data: DataFrame with 'timestamp' and 'value' columns
            target_timestamp: The airing timestamp to compute baseline for
            geo: Optional geographic filter

        Returns:
            Tuple of (baseline_mean, baseline_std)
        """
        if signal_data.empty:
            return 0.0, 0.0

        lookback_start = target_timestamp - timedelta(days=self.config.lookback_days)

        # Filter to lookback period
        mask = (
            (signal_data["timestamp"] >= lookback_start)
            & (signal_data["timestamp"] < target_timestamp)
        )

        if geo and "geo" in signal_data.columns:
            mask &= signal_data["geo"] == geo

        baseline_data = signal_data[mask].copy()

        if baseline_data.empty:
            return 0.0, 0.0

        if self.config.same_hour:
            target_hour = target_timestamp.hour
            baseline_data = baseline_data[
                baseline_data["timestamp"].dt.hour == target_hour
            ]

        if self.config.same_day_of_week:
            target_dow = target_timestamp.weekday()
            baseline_data = baseline_data[
                baseline_data["timestamp"].dt.weekday == target_dow
            ]

        if baseline_data.empty:
            # Fall back to all hours/days if too restrictive
            mask = (
                (signal_data["timestamp"] >= lookback_start)
                & (signal_data["timestamp"] < target_timestamp)
            )
            baseline_data = signal_data[mask]

        values = baseline_data["value"].values
        return float(np.mean(values)), float(np.std(values)) if len(values) > 1 else (float(np.mean(values)), 0.0)

    def compute_post_airing_signal(
        self,
        signal_data: pd.DataFrame,
        airing_timestamp: datetime,
        window_minutes: int,
        geo: Optional[str] = None,
    ) -> float:
        """Get average signal value in the window after an airing.

        Args:
            signal_data: DataFrame with 'timestamp' and 'value' columns
            airing_timestamp: When the ad aired
            window_minutes: How many minutes after airing to look
            geo: Optional geographic filter

        Returns:
            Average signal value in the post-airing window
        """
        window_end = airing_timestamp + timedelta(minutes=window_minutes)

        mask = (
            (signal_data["timestamp"] >= airing_timestamp)
            & (signal_data["timestamp"] <= window_end)
        )

        if geo and "geo" in signal_data.columns:
            mask &= signal_data["geo"] == geo

        window_data = signal_data[mask]

        if window_data.empty:
            return 0.0

        return float(window_data["value"].mean())

    def apply_adstock(
        self,
        values: np.ndarray,
        decay_rate: float = 0.7,
    ) -> np.ndarray:
        """Apply adstock transformation (exponential decay) to a signal.

        Models how TV ad effects carry over and decay over time.
        Borrowed from Google LightweightMMM methodology.

        Args:
            values: Array of signal values over time
            decay_rate: How quickly the effect decays (0-1, higher = longer carry)

        Returns:
            Adstocked values
        """
        adstocked = np.zeros_like(values, dtype=float)
        adstocked[0] = values[0]

        for i in range(1, len(values)):
            adstocked[i] = values[i] + decay_rate * adstocked[i - 1]

        return adstocked

    def correlate_airing(
        self,
        airing: dict,
        trends_data: Optional[pd.DataFrame] = None,
        ga4_data: Optional[pd.DataFrame] = None,
        call_data: Optional[pd.DataFrame] = None,
        qr_data: Optional[pd.DataFrame] = None,
        search_console_data: Optional[pd.DataFrame] = None,
        time_windows: Optional[list[TimeWindow]] = None,
    ) -> CorrelationResult:
        """Correlate a single TV airing with all available digital signals.

        Args:
            airing: Dict with airing info (id, airing_timestamp, network, dma_code, etc.)
            trends_data: Google Trends interest over time
            ga4_data: GA4 sessions/conversions over time
            call_data: Call volume over time
            qr_data: QR scan count over time
            search_console_data: Search Console clicks/impressions over time
            time_windows: Custom time windows (defaults to 30min, 2hr, 24hr, 72hr)

        Returns:
            CorrelationResult with lift metrics per window and composite score
        """
        windows = time_windows or DEFAULT_TIME_WINDOWS
        airing_ts = airing["airing_timestamp"]
        if isinstance(airing_ts, str):
            airing_ts = datetime.fromisoformat(airing_ts)
        dma = airing.get("dma_code")

        trends_lift = {}
        ga4_session_lift = {}
        ga4_conversion_lift = {}
        search_console_lift = {}
        call_volume_lift = {}
        qr_scan_lift = {}
        signals_available = 0
        all_lifts = []

        for window in windows:
            label = window.label

            # Google Trends
            if trends_data is not None and not trends_data.empty:
                t_data = trends_data.rename(columns={"interest_score": "value"})
                baseline_mean, baseline_std = self.compute_baseline(t_data, airing_ts, geo=dma)
                post_value = self.compute_post_airing_signal(t_data, airing_ts, window.minutes, geo=dma)

                if baseline_mean > 0:
                    lift = ((post_value - baseline_mean) / baseline_mean) * 100
                else:
                    lift = 0.0

                trends_lift[label] = round(lift, 1)
                all_lifts.append(lift * window.weight)

                if label == "immediate":
                    signals_available += 1

            # GA4 Sessions
            if ga4_data is not None and not ga4_data.empty:
                baseline_mean, baseline_std = self.compute_baseline(ga4_data, airing_ts, geo=dma)
                post_value = self.compute_post_airing_signal(ga4_data, airing_ts, window.minutes, geo=dma)

                if baseline_mean > 0:
                    lift = ((post_value - baseline_mean) / baseline_mean) * 100
                else:
                    lift = 0.0

                ga4_session_lift[label] = round(lift, 1)
                all_lifts.append(lift * window.weight)

                if label == "immediate":
                    signals_available += 1

            # Call volume
            if call_data is not None and not call_data.empty:
                baseline_mean, baseline_std = self.compute_baseline(call_data, airing_ts, geo=dma)
                post_value = self.compute_post_airing_signal(call_data, airing_ts, window.minutes, geo=dma)

                if baseline_mean > 0:
                    lift = ((post_value - baseline_mean) / baseline_mean) * 100
                else:
                    lift = 0.0

                call_volume_lift[label] = round(lift, 1)
                all_lifts.append(lift * window.weight)

                if label == "immediate":
                    signals_available += 1

            # QR scans
            if qr_data is not None and not qr_data.empty:
                baseline_mean, baseline_std = self.compute_baseline(qr_data, airing_ts, geo=dma)
                post_value = self.compute_post_airing_signal(qr_data, airing_ts, window.minutes, geo=dma)

                if baseline_mean > 0:
                    lift = ((post_value - baseline_mean) / baseline_mean) * 100
                else:
                    lift = 0.0

                qr_scan_lift[label] = round(lift, 1)
                all_lifts.append(lift * window.weight)

                if label == "immediate":
                    signals_available += 1

        # Composite score: weighted average of all lifts, normalized to 0-100
        if all_lifts:
            raw_score = np.mean(all_lifts)
            composite_score = max(0.0, min(100.0, raw_score))
        else:
            composite_score = 0.0

        # Confidence based on signals available and lift consistency
        confidence = min(1.0, signals_available / 4.0)  # More signals = higher confidence

        # Significance check
        is_significant = composite_score > 10.0 and signals_available >= 1

        return CorrelationResult(
            airing_id=airing.get("id", ""),
            airing_timestamp=airing_ts,
            network=airing.get("network", ""),
            dma_code=dma,
            creative_id=airing.get("creative_id"),
            trends_lift=trends_lift,
            ga4_session_lift=ga4_session_lift,
            ga4_conversion_lift=ga4_conversion_lift,
            search_console_lift=search_console_lift,
            call_volume_lift=call_volume_lift,
            qr_scan_lift=qr_scan_lift,
            composite_score=round(composite_score, 1),
            confidence=round(confidence, 2),
            signals_available=signals_available,
            is_significant=is_significant,
        )


# Singleton
correlation_engine = CorrelationEngine()
