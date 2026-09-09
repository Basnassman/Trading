"""Temporal enforcement for the XAUUSD Trading System.

Ensures data is only used after its availability_time.
This is the core mechanism for preventing look-ahead bias.

CRITICAL: TemporalViolation is raised when data is used too early.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.canonical.time import TemporalBounds, ensure_utc
from src.errors.exceptions import TemporalViolation


class TemporalEnforcer:
    """Enforces temporal correctness for all data access.
    
    Usage:
        enforcer = TemporalEnforcer()
        
        # Before using any observation:
        enforcer.check_availability(observation.temporal, current_time)
        
        # Or filter a list:
        available = enforcer.filter_available(observations, current_time)
    """
    
    def check_availability(
        self,
        temporal: TemporalBounds,
        current_time: datetime,
        feature_name: str = "",
    ) -> None:
        """Check if observation is available at current_time.
        
        Raises TemporalViolation if not available.
        
        Args:
            temporal: Temporal bounds of the observation
            current_time: Current system time
            feature_name: Name of the feature being accessed (for error message)
        
        Raises:
            TemporalViolation: If availability_time > current_time
        """
        current_time = ensure_utc(current_time)
        
        if not temporal.is_available_at(current_time):
            raise TemporalViolation(
                f"Temporal violation: '{feature_name}' is not yet available. "
                f"availability_time={temporal.availability_time.value}, "
                f"current_time={current_time}",
                feature_name=feature_name,
                availability_time=temporal.availability_time.value,
                current_time=current_time,
                module="temporal_enforcer",
            )
    
    def filter_available(
        self,
        observations: list[Any],
        current_time: datetime,
    ) -> list[Any]:
        """Filter observations to only those available at current_time.
        
        Args:
            observations: List of observations with .temporal attribute
            current_time: Current system time
        
        Returns:
            List of available observations
        """
        current_time = ensure_utc(current_time)
        return [
            obs for obs in observations
            if hasattr(obs, 'temporal') and obs.temporal.is_available_at(current_time)
        ]
    
    def get_latest_available(
        self,
        observations: list[Any],
        current_time: datetime,
    ) -> Any | None:
        """Get the most recent observation available at current_time.
        
        Args:
            observations: List of observations with .temporal attribute
            current_time: Current system time
        
        Returns:
            Most recent available observation, or None
        """
        available = self.filter_available(observations, current_time)
        if not available:
            return None
        return max(available, key=lambda o: o.temporal.event_time.value)
    
    def compute_availability_time(
        self,
        event_time: datetime,
        confirmation_bars: int,
        bar_duration_seconds: int,
    ) -> datetime:
        """Compute availability time for a bar-based observation.
        
        Args:
            event_time: When the event occurred
            confirmation_bars: How many bars to wait
            bar_duration_seconds: Duration of one bar in seconds
        
        Returns:
            Availability time
        """
        from datetime import timedelta
        return ensure_utc(event_time) + timedelta(
            seconds=bar_duration_seconds * confirmation_bars
        )
