"""Feature store for the XAUUSD Trading System.

Stores computed features with full metadata.
No business logic — just storage and retrieval.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from src.canonical.contracts import FeatureRecord


class FeatureStore:
    """Feature storage and retrieval.
    
    Stores FeatureRecords with full metadata.
    Supports querying by feature name, time range, and source engine.
    """
    
    def __init__(self):
        self._store: dict[str, FeatureRecord] = {}
        self._index_by_name: dict[str, list[str]] = {}
        self._index_by_time: dict[datetime, list[str]] = {}
    
    def store(self, record: FeatureRecord) -> None:
        """Store a feature record."""
        self._store[record.feature_id] = record
        
        # Update indices
        if record.feature_name not in self._index_by_name:
            self._index_by_name[record.feature_name] = []
        self._index_by_name[record.feature_name].append(record.feature_id)
        
        event_time = record.temporal.event_time.value
        if event_time not in self._index_by_time:
            self._index_by_time[event_time] = []
        self._index_by_time[event_time].append(record.feature_id)
    
    def get(
        self,
        feature_id: str,
    ) -> Optional[FeatureRecord]:
        """Get a feature record by ID."""
        return self._store.get(feature_id)
    
    def get_by_name(
        self,
        feature_name: str,
        limit: int = 100,
    ) -> list[FeatureRecord]:
        """Get recent feature records by name."""
        ids = self._index_by_name.get(feature_name, [])
        records = [self._store[rid] for rid in ids if rid in self._store]
        return records[-limit:]
    
    def get_at_time(
        self,
        feature_name: str,
        event_time: datetime,
    ) -> Optional[FeatureRecord]:
        """Get feature record at specific time."""
        ids = self._index_by_name.get(feature_name, [])
        for fid in ids:
            record = self._store.get(fid)
            if record and record.temporal.event_time.value == event_time:
                return record
        return None
    
    def has_features(self, bar_id: str) -> bool:
        """Check if features exist for a bar."""
        return any(
            record.feature_id.startswith(bar_id)
            for record in self._store.values()
        )
    
    def count(self) -> int:
        """Get total number of stored features."""
        return len(self._store)
    
    def clear(self) -> None:
        """Clear all stored features."""
        self._store.clear()
        self._index_by_name.clear()
        self._index_by_time.clear()
