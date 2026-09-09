"""Temporal leakage tests for the data layer.

CRITICAL: These tests ensure no look-ahead bias in data handling.
If any test fails, the system has a temporal violation bug.

These tests work on CanonicalBar (output of pipeline) which has temporal bounds.
RawBar has bar_time only; the pipeline adds availability_time.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.providers.mock.market_data import MockMarketDataProvider
from src.ingestion.pipeline import IngestionPipeline
from src.temporal.enforcer import TemporalEnforcer
from src.errors.exceptions import TemporalViolation


UTC = timezone.utc


def _canonicalize_mock_bars(
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
    seed: int = 42,
):
    """Helper: get raw bars from mock provider, run through pipeline, return canonical bars."""
    provider = MockMarketDataProvider(seed=seed)
    pipeline = IngestionPipeline(provider=provider)
    result = pipeline.ingest_bars(symbol, timeframe, start, end)

    # Re-run to get actual canonical bars (pipeline stores them internally)
    # We need to access the pipeline's canonicalization directly
    raw_bars = provider.get_bars(symbol, timeframe, start, end)
    canonical_bars = [pipeline._canonicalize_bar(bar) for bar in raw_bars]
    return canonical_bars


class TestDataLeakage:
    """Test that data is not used before availability_time."""

    def setup_method(self):
        self.enforcer = TemporalEnforcer()

    def test_bar_not_available_before_confirmation(self):
        """Bar should not be available before its confirmation time."""
        bars = _canonicalize_mock_bars(
            "XAUUSD", "M5",
            datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
            datetime(2026, 8, 31, 14, 10, tzinfo=UTC),
        )

        assert len(bars) > 0
        bar = bars[0]

        # Try to use bar before its availability_time
        before_availability = bar.temporal.availability_time.value - timedelta(minutes=1)

        with pytest.raises(TemporalViolation):
            self.enforcer.check_availability(
                bar.temporal,
                before_availability,
                "test_feature"
            )

    def test_bar_available_after_confirmation(self):
        """Bar should be available after its confirmation time."""
        bars = _canonicalize_mock_bars(
            "XAUUSD", "M5",
            datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
            datetime(2026, 8, 31, 14, 10, tzinfo=UTC),
        )

        assert len(bars) > 0
        bar = bars[0]

        # Try to use bar after its availability_time
        after_availability = bar.temporal.availability_time.value + timedelta(minutes=1)

        # Should NOT raise
        self.enforcer.check_availability(
            bar.temporal,
            after_availability,
            "test_feature"
        )

    def test_future_bar_not_accessible(self):
        """Future bars should not be accessible."""
        bars = _canonicalize_mock_bars(
            "XAUUSD", "M5",
            datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
            datetime(2026, 8, 31, 15, 0, tzinfo=UTC),
        )

        assert len(bars) > 1

        # Current time is when first bar is available
        current_time = bars[0].temporal.availability_time.value

        # Second bar should NOT be available yet
        second_bar = bars[1]

        with pytest.raises(TemporalViolation):
            self.enforcer.check_availability(
                second_bar.temporal,
                current_time,
                "future_bar"
            )

    def test_filter_only_available_bars(self):
        """Filter should return only bars available at current time."""
        bars = _canonicalize_mock_bars(
            "XAUUSD", "M5",
            datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
            datetime(2026, 8, 31, 14, 30, tzinfo=UTC),
        )

        assert len(bars) > 5

        # Current time is when bar 5 is available
        current_time = bars[4].temporal.availability_time.value

        available = self.enforcer.filter_available(bars, current_time)

        # Only bars 0-4 should be available
        assert len(available) <= 5

        # All available bars should have availability_time <= current_time
        for bar in available:
            assert bar.temporal.availability_time.value <= current_time


class TestNoFutureDataAccess:
    """Test that no component accesses future data."""

    def test_gsi_components_checked(self):
        """GSI computation should check component availability."""
        from src.canonical.contracts import CanonicalGSI
        from src.canonical.enums import Direction

        enforcer = TemporalEnforcer()

        # GSI computed at 14:10
        gsi_time = datetime(2026, 8, 31, 14, 10, tzinfo=UTC)

        # Structure score available at 14:05
        structure_available = datetime(2026, 8, 31, 14, 5, tzinfo=UTC)

        # Trend score available at 14:15 (NOT YET AVAILABLE)
        trend_available = datetime(2026, 8, 31, 14, 15, tzinfo=UTC)

        from src.canonical.time import TemporalBounds, EventTime, AvailabilityTime, IngestionTime

        structure_temporal = TemporalBounds(
            event_time=EventTime(datetime(2026, 8, 31, 14, 0, tzinfo=UTC)),
            availability_time=AvailabilityTime(structure_available),
            ingestion_time=IngestionTime(gsi_time),
        )

        trend_temporal = TemporalBounds(
            event_time=EventTime(datetime(2026, 8, 31, 14, 10, tzinfo=UTC)),
            availability_time=AvailabilityTime(trend_available),
            ingestion_time=IngestionTime(gsi_time),
        )

        # Structure is available
        enforcer.check_availability(structure_temporal, gsi_time, "structure_score")

        # Trend is NOT available
        with pytest.raises(TemporalViolation):
            enforcer.check_availability(trend_temporal, gsi_time, "trend_score")


class TestDataIntegrity:
    """Test data integrity rules on canonical bars."""

    def test_all_timestamps_utc(self):
        """All timestamps should be UTC timezone-aware."""
        bars = _canonicalize_mock_bars(
            "XAUUSD", "M5",
            datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
            datetime(2026, 8, 31, 15, 0, tzinfo=UTC),
        )

        for bar in bars:
            assert bar.temporal.event_time.value.tzinfo is not None
            assert bar.temporal.availability_time.value.tzinfo is not None
            assert bar.temporal.ingestion_time.value.tzinfo is not None

    def test_availability_after_event(self):
        """availability_time should be after event_time."""
        bars = _canonicalize_mock_bars(
            "XAUUSD", "M5",
            datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
            datetime(2026, 8, 31, 15, 0, tzinfo=UTC),
        )

        for bar in bars:
            assert bar.temporal.availability_time.value >= bar.temporal.event_time.value

    def test_ingestion_after_availability(self):
        """ingestion_time should be after availability_time."""
        bars = _canonicalize_mock_bars(
            "XAUUSD", "M5",
            datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
            datetime(2026, 8, 31, 15, 0, tzinfo=UTC),
        )

        for bar in bars:
            assert bar.temporal.ingestion_time.value >= bar.temporal.availability_time.value
