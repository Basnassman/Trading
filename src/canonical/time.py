"""Time semantics for the XAUUSD Trading System.

Every observation has three timestamps:
- event_time: When the event occurred in the market
- availability_time: When the system can legitimately consume the data
- ingestion_time: When our infrastructure received the data

All timestamps are timezone-aware (UTC). Naive datetime is NOT allowed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional


UTC = timezone.utc


def utcnow() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(UTC)


def ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is UTC timezone-aware.
    
    Raises:
        TypeError: If dt is naive (no timezone info).
    """
    if dt.tzinfo is None:
        raise TypeError(
            f"Naive datetime not allowed: {dt}. "
            "All timestamps must be timezone-aware (UTC)."
        )
    return dt.astimezone(UTC)


def to_utc(dt: datetime) -> datetime:
    """Convert any timezone-aware datetime to UTC."""
    return ensure_utc(dt)


@dataclass(frozen=True)
class EventTime:
    """When the event occurred in the market.
    
    Examples:
        - Bar open time for OHLCV
        - Release time for news
        - Publication time for macro data
    """
    value: datetime = field(metadata={"description": "Market event time (UTC)"})
    
    def __post_init__(self):
        object.__setattr__(self, 'value', ensure_utc(self.value))


@dataclass(frozen=True)
class AvailabilityTime:
    """When the data became available for system consumption.
    
    Examples:
        - Bar close time + confirmation delay for OHLCV
        - Release time for news actual
        - Revision time for news revisions
        - Training window end for calibration parameters
    """
    value: datetime = field(metadata={"description": "Data availability time (UTC)"})
    
    def __post_init__(self):
        object.__setattr__(self, 'value', ensure_utc(self.value))
    
    def is_available_at(self, current_time: datetime) -> bool:
        """Check if data is available at given time."""
        return self.value <= ensure_utc(current_time)


@dataclass(frozen=True)
class IngestionTime:
    """When our infrastructure received the data.
    
    Used for freshness monitoring and latency measurement.
    """
    value: datetime = field(metadata={"description": "Data ingestion time (UTC)"})
    
    def __post_init__(self):
        object.__setattr__(self, 'value', ensure_utc(self.value))
    
    def freshness_seconds(self, reference_time: datetime | None = None) -> float:
        """Compute data age in seconds."""
        ref = ensure_utc(reference_time) if reference_time else utcnow()
        delta = ref - self.value
        return max(0.0, delta.total_seconds())


@dataclass(frozen=True)
class TemporalBounds:
    """Complete temporal information for an observation."""
    event_time: EventTime
    availability_time: AvailabilityTime
    ingestion_time: IngestionTime
    
    def is_available_at(self, current_time: datetime) -> bool:
        """Check if observation is available at given time."""
        return self.availability_time.is_available_at(current_time)
    
    def latency_seconds(self) -> float:
        """Compute ingestion latency (availability to ingestion)."""
        delta = self.ingestion_time.value - self.availability_time.value
        return max(0.0, delta.total_seconds())


def create_temporal_bounds(
    event_time: datetime,
    availability_time: datetime,
    ingestion_time: datetime | None = None,
) -> TemporalBounds:
    """Factory function to create TemporalBounds."""
    return TemporalBounds(
        event_time=EventTime(event_time),
        availability_time=AvailabilityTime(availability_time),
        ingestion_time=IngestionTime(ingestion_time or utcnow()),
    )


def compute_availability_delay(
    event_time: datetime,
    bar_duration: timedelta,
    confirmation_bars: int = 1,
) -> datetime:
    """Compute availability time for a bar-based observation.
    
    Args:
        event_time: When the bar started
        bar_duration: Duration of one bar (e.g., 5 minutes for M5)
        confirmation_bars: How many bars to wait for confirmation
    
    Returns:
        Availability time = event_time + confirmation_bars × bar_duration
    """
    return ensure_utc(event_time) + (bar_duration * confirmation_bars)
