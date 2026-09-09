"""Data ingestion pipeline for the XAUUSD Trading System.

Flow: Provider → Fetch → Validate → Canonicalize → Persist

The pipeline is:
- Idempotent (same data ingested twice → no duplicates)
- Resumable (can restart after failure)
- Auditable (every run is logged)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

from src.canonical.raw import RawBar
from src.canonical.contracts import CanonicalBar
from src.canonical.enums import DataQuality, Timeframe
from src.canonical.time import TemporalBounds, EventTime, AvailabilityTime, IngestionTime, utcnow
from src.providers.interfaces import MarketDataProvider
from src.validation.validators import BarValidator, TemporalValidator, DuplicateDetector
from src.errors.exceptions import DataError, InvalidData


@dataclass
class IngestionResult:
    """Result of an ingestion run."""
    run_id: str
    source: str
    instrument: str
    timeframe: str
    
    start_time: datetime
    end_time: Optional[datetime] = None
    
    records_fetched: int = 0
    records_valid: int = 0
    records_warning: int = 0
    records_invalid: int = 0
    records_persisted: int = 0
    
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    status: str = "running"  # running, completed, failed


class IngestionPipeline:
    """Data ingestion pipeline.
    
    Handles fetching, validation, canonicalization, and persistence.
    """
    
    def __init__(
        self,
        provider: MarketDataProvider,
        bar_validator: BarValidator | None = None,
        temporal_validator: TemporalValidator | None = None,
        duplicate_detector: DuplicateDetector | None = None,
    ):
        self.provider = provider
        self.bar_validator = bar_validator or BarValidator()
        self.temporal_validator = temporal_validator or TemporalValidator()
        self.duplicate_detector = duplicate_detector or DuplicateDetector()
    
    def ingest_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> IngestionResult:
        """Ingest historical bars.
        
        Args:
            symbol: Instrument symbol
            timeframe: Bar timeframe
            start: Start time (UTC)
            end: End time (UTC)
        
        Returns:
            IngestionResult with statistics
        """
        run_id = f"ingest_{uuid.uuid4().hex[:12]}"
        now = utcnow()
        
        result = IngestionResult(
            run_id=run_id,
            source="mt5",
            instrument=symbol,
            timeframe=timeframe,
            start_time=now,
        )
        
        try:
            # 1. Fetch from provider
            raw_bars = self.provider.get_bars(symbol, timeframe, start, end)
            result.records_fetched = len(raw_bars)
            
            if not raw_bars:
                result.status = "completed"
                result.end_time = utcnow()
                return result
            
            # 2. Validate
            validation_report = self.bar_validator.validate_batch(raw_bars)
            result.records_valid = validation_report.valid_records
            result.records_warning = validation_report.warning_records
            result.records_invalid = validation_report.invalid_records
            result.errors.extend(validation_report.errors)
            result.warnings.extend(validation_report.warnings)
            
            # 3. Filter valid bars
            valid_bars = [
                bar for bar in raw_bars
                if self.bar_validator.validate(bar).is_valid
            ]
            
            # 4. Check temporal ordering
            ordering_result = self.temporal_validator.validate_ordering(valid_bars, timeframe)
            if not ordering_result.is_valid:
                result.errors.extend(ordering_result.errors)
            
            # 5. Detect duplicates
            duplicates = self.duplicate_detector.detect_bar_duplicates(valid_bars)
            if duplicates:
                result.warnings.append(f"Found {len(duplicates)} duplicate bars")
            
            # 6. Detect gaps
            gaps = self.temporal_validator.detect_gaps(valid_bars, timeframe)
            if gaps:
                for gap in gaps:
                    result.warnings.append(
                        f"Gap: {gap['start']} to {gap['end']} ({gap['type']})"
                    )
            
            # 7. Canonicalize (convert RawBar to CanonicalBar)
            canonical_bars = [
                self._canonicalize_bar(bar) for bar in valid_bars
            ]
            
            result.records_persisted = len(canonical_bars)
            result.status = "completed"
            result.end_time = utcnow()
            
        except Exception as e:
            result.status = "failed"
            result.errors.append(str(e))
            result.end_time = utcnow()
        
        return result
    
    def _canonicalize_bar(self, raw: RawBar) -> CanonicalBar:
        """Convert RawBar to CanonicalBar."""
        from datetime import timedelta
        
        # Compute availability time based on timeframe
        tf_minutes = {
            "M1": 1, "M5": 5, "M15": 15,
            "H1": 60, "H4": 240, "D1": 1440,
        }.get(raw.timeframe, 5)
        
        availability_time = raw.bar_time + timedelta(minutes=tf_minutes)
        
        return CanonicalBar(
            bar_id=f"canonical_{raw.symbol}_{raw.timeframe}_{raw.bar_time.isoformat()}",
            symbol=raw.symbol,
            timeframe=Timeframe(raw.timeframe),
            open=raw.open,
            high=raw.high,
            low=raw.low,
            close=raw.close,
            tick_volume=raw.tick_volume,
            real_volume=raw.real_volume,
            bid_at_close=raw.bid,
            ask_at_close=raw.ask,
            temporal=TemporalBounds(
                event_time=EventTime(raw.bar_time),
                availability_time=AvailabilityTime(availability_time),
                ingestion_time=IngestionTime(utcnow()),
            ),
        )
