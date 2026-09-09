"""Temporal correctness tests for the XAUUSD Trading System.

CRITICAL: These tests ensure no look-ahead bias.
If any test fails, the system has a temporal violation bug.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.canonical.contracts import CanonicalBar, CanonicalSwing, CanonicalGSI
from src.canonical.enums import Timeframe, SwingType, DataQuality, Direction
from src.canonical.time import TemporalBounds, EventTime, AvailabilityTime, IngestionTime
from src.temporal.enforcer import TemporalEnforcer
from src.errors.exceptions import TemporalViolation


UTC = timezone.utc


def make_temporal(
    event_time: datetime,
    availability_time: datetime,
    ingestion_time: datetime | None = None,
) -> TemporalBounds:
    """Helper to create TemporalBounds."""
    return TemporalBounds(
        event_time=EventTime(event_time),
        availability_time=AvailabilityTime(availability_time),
        ingestion_time=IngestionTime(ingestion_time or datetime.now(UTC)),
    )


def make_bar(
    bar_time: datetime,
    confirmation_bars: int = 1,
    bar_duration_minutes: int = 5,
) -> CanonicalBar:
    """Helper to create a CanonicalBar with proper temporal bounds."""
    availability = bar_time + timedelta(minutes=bar_duration_minutes * confirmation_bars)
    return CanonicalBar(
        bar_id=f"test_{bar_time.isoformat()}",
        symbol="XAUUSD",
        timeframe=Timeframe.M5,
        open=1850.00,
        high=1855.00,
        low=1848.00,
        close=1853.00,
        tick_volume=100,
        temporal=make_temporal(bar_time, availability),
    )


class TestTemporalEnforcer:
    """Test the TemporalEnforcer."""
    
    def setup_method(self):
        self.enforcer = TemporalEnforcer()
    
    def test_available_at_correct_time(self):
        """Data should be available after availability_time."""
        t_event = datetime(2026, 8, 31, 14, 0, tzinfo=UTC)
        t_available = datetime(2026, 8, 31, 14, 5, tzinfo=UTC)
        t_current = datetime(2026, 8, 31, 14, 10, tzinfo=UTC)
        
        temporal = make_temporal(t_event, t_available)
        
        # Should NOT raise
        self.enforcer.check_availability(temporal, t_current, "test_feature")
    
    def test_not_available_before_availability_time(self):
        """Data should NOT be available before availability_time."""
        t_event = datetime(2026, 8, 31, 14, 0, tzinfo=UTC)
        t_available = datetime(2026, 8, 31, 14, 5, tzinfo=UTC)
        t_current = datetime(2026, 8, 31, 14, 3, tzinfo=UTC)  # Before availability
        
        temporal = make_temporal(t_event, t_available)
        
        with pytest.raises(TemporalViolation) as exc_info:
            self.enforcer.check_availability(temporal, t_current, "test_feature")
        
        assert "test_feature" in str(exc_info.value)
    
    def test_not_available_at_exact_availability_time(self):
        """Data should be available at exactly availability_time."""
        t_event = datetime(2026, 8, 31, 14, 0, tzinfo=UTC)
        t_available = datetime(2026, 8, 31, 14, 5, tzinfo=UTC)
        t_current = datetime(2026, 8, 31, 14, 5, tzinfo=UTC)  # Exactly at availability
        
        temporal = make_temporal(t_event, t_available)
        
        # Should NOT raise (availability_time <= current_time)
        self.enforcer.check_availability(temporal, t_current, "test_feature")
    
    def test_filter_available(self):
        """Filter should return only available observations."""
        t_current = datetime(2026, 8, 31, 14, 10, tzinfo=UTC)
        
        # Bar 1: available at 14:05
        bar1 = make_bar(datetime(2026, 8, 31, 14, 0, tzinfo=UTC))
        # Bar 2: available at 14:10
        bar2 = make_bar(datetime(2026, 8, 31, 14, 5, tzinfo=UTC))
        # Bar 3: available at 14:15 (not yet available)
        bar3 = make_bar(datetime(2026, 8, 31, 14, 10, tzinfo=UTC))
        
        available = self.enforcer.filter_available([bar1, bar2, bar3], t_current)
        
        assert len(available) == 2
        assert bar1 in available
        assert bar2 in available
        assert bar3 not in available


class TestBarTemporalRules:
    """Test bar-specific temporal rules."""
    
    def test_m5_bar_confirmation(self):
        """M5 bar should be available after close (5 minutes)."""
        enforcer = TemporalEnforcer()
        
        bar_time = datetime(2026, 8, 31, 14, 0, tzinfo=UTC)
        bar = make_bar(bar_time, confirmation_bars=1, bar_duration_minutes=5)
        
        # Before confirmation (14:03)
        with pytest.raises(TemporalViolation):
            enforcer.check_availability(
                bar.temporal,
                datetime(2026, 8, 31, 14, 3, tzinfo=UTC),
                "M5_bar"
            )
        
        # After confirmation (14:06)
        enforcer.check_availability(
            bar.temporal,
            datetime(2026, 8, 31, 14, 6, tzinfo=UTC),
            "M5_bar"
        )
    
    def test_swing_confirmation(self):
        """Swing should be available after k-bar confirmation."""
        enforcer = TemporalEnforcer()
        
        swing_time = datetime(2026, 8, 31, 14, 0, tzinfo=UTC)
        confirmation_time = swing_time + timedelta(minutes=15)  # k=3, M5
        
        swing = CanonicalSwing(
            swing_id="test_swing",
            symbol="XAUUSD",
            timeframe=Timeframe.M5,
            swing_type=SwingType.HIGH,
            price=1855.00,
            bar_time=swing_time,
            confirmation_time=confirmation_time,
            is_confirmed=False,
            strength=0.8,
            temporal=make_temporal(swing_time, confirmation_time),
        )
        
        # Before confirmation (14:10)
        with pytest.raises(TemporalViolation):
            enforcer.check_availability(
                swing.temporal,
                datetime(2026, 8, 31, 14, 10, tzinfo=UTC),
                "swing_point"
            )
        
        # After confirmation (14:16)
        enforcer.check_availability(
            swing.temporal,
            datetime(2026, 8, 31, 14, 16, tzinfo=UTC),
            "swing_point"
        )
    
    def test_news_actual_not_available_before_release(self):
        """News actual should not be available before release_time."""
        from src.canonical.contracts import CanonicalNewsEvent
        from src.canonical.enums import NewsCategory, NewsImpact
        
        enforcer = TemporalEnforcer()
        
        release_time = datetime(2026, 8, 31, 13, 30, tzinfo=UTC)
        
        event = CanonicalNewsEvent(
            event_id="test_cpi",
            name="CPI m/m",
            currency="USD",
            category=NewsCategory.CPI,
            importance=NewsImpact.HIGH,
            release_time=release_time,
            actual=0.4,
            forecast=0.3,
            temporal=make_temporal(release_time, release_time),
        )
        
        # Before release (13:29)
        with pytest.raises(TemporalViolation):
            enforcer.check_availability(
                event.temporal,
                datetime(2026, 8, 31, 13, 29, tzinfo=UTC),
                "news_actual"
            )
        
        # At release (13:30)
        enforcer.check_availability(
            event.temporal,
            datetime(2026, 8, 31, 13, 30, tzinfo=UTC),
            "news_actual"
        )


class TestGSITemporalRules:
    """Test GSI temporal rules."""
    
    def test_gsi_uses_only_available_components(self):
        """GSI should only use components available at computation time."""
        enforcer = TemporalEnforcer()
        
        # GSI computed at 14:10
        gsi_time = datetime(2026, 8, 31, 14, 10, tzinfo=UTC)
        
        # Structure score available at 14:05
        structure_available = datetime(2026, 8, 31, 14, 5, tzinfo=UTC)
        
        # Flow score available at 14:10
        flow_available = datetime(2026, 8, 31, 14, 10, tzinfo=UTC)
        
        # Trend score available at 14:15 (NOT YET AVAILABLE at 14:10)
        trend_available = datetime(2026, 8, 31, 14, 15, tzinfo=UTC)
        
        # Structure is available
        structure_temporal = make_temporal(
            datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
            structure_available,
        )
        enforcer.check_availability(structure_temporal, gsi_time, "structure_score")
        
        # Flow is available
        flow_temporal = make_temporal(
            datetime(2026, 8, 31, 14, 5, tzinfo=UTC),
            flow_available,
        )
        enforcer.check_availability(flow_temporal, gsi_time, "flow_score")
        
        # Trend is NOT available
        trend_temporal = make_temporal(
            datetime(2026, 8, 31, 14, 10, tzinfo=UTC),
            trend_available,
        )
        with pytest.raises(TemporalViolation):
            enforcer.check_availability(trend_temporal, gsi_time, "trend_score")


class TestNoNaiveDatetime:
    """Test that naive datetime is rejected."""
    
    def test_naive_datetime_rejected(self):
        """Naive datetime should raise TypeError."""
        from src.canonical.time import ensure_utc
        
        naive = datetime(2026, 8, 31, 14, 0)  # No timezone
        
        with pytest.raises(TypeError) as exc_info:
            ensure_utc(naive)
        
        assert "Naive datetime not allowed" in str(exc_info.value)
    
    def test_utc_datetime_accepted(self):
        """UTC datetime should be accepted."""
        from src.canonical.time import ensure_utc
        
        utc_aware = datetime(2026, 8, 31, 14, 0, tzinfo=UTC)
        
        result = ensure_utc(utc_aware)
        assert result.tzinfo is not None
