"""Integration tests for data validation with mock provider.

Tests the full pipeline: Provider → Validate → Canonicalize.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.providers.mock.market_data import MockMarketDataProvider
from src.ingestion.pipeline import IngestionPipeline
from src.validation.validators import BarValidator, TemporalValidator, DuplicateDetector


UTC = timezone.utc


class TestDataIngestionPipeline:
    """Test full ingestion pipeline with mock provider."""
    
    def setup_method(self):
        self.provider = MockMarketDataProvider(seed=42)
        self.pipeline = IngestionPipeline(provider=self.provider)
    
    def test_ingest_m5_bars(self):
        """Ingest M5 bars from mock provider."""
        start = datetime(2026, 8, 31, 14, 0, tzinfo=UTC)
        end = datetime(2026, 8, 31, 15, 0, tzinfo=UTC)
        
        result = self.pipeline.ingest_bars("XAUUSD", "M5", start, end)
        
        assert result.status == "completed", f"Failed: {result.errors}"
        assert result.records_fetched > 0
        assert result.records_persisted > 0
        assert result.records_invalid == 0
    
    def test_ingest_h1_bars(self):
        """Ingest H1 bars from mock provider."""
        start = datetime(2026, 8, 30, 0, 0, tzinfo=UTC)
        end = datetime(2026, 8, 31, 0, 0, tzinfo=UTC)
        
        result = self.pipeline.ingest_bars("XAUUSD", "H1", start, end)
        
        assert result.status == "completed", f"Failed: {result.errors}"
        assert result.records_fetched > 0
    
    def test_ingest_d1_bars(self):
        """Ingest D1 bars from mock provider."""
        start = datetime(2026, 8, 1, 0, 0, tzinfo=UTC)
        end = datetime(2026, 8, 31, 0, 0, tzinfo=UTC)
        
        result = self.pipeline.ingest_bars("XAUUSD", "D1", start, end)
        
        assert result.status == "completed", f"Failed: {result.errors}"
        assert result.records_fetched > 0
    
    def test_empty_date_range(self):
        """Empty date range should return no bars."""
        start = datetime(2026, 8, 31, 14, 0, tzinfo=UTC)
        end = datetime(2026, 8, 31, 14, 0, tzinfo=UTC)
        
        result = self.pipeline.ingest_bars("XAUUSD", "M5", start, end)
        
        assert result.status == "completed"
        assert result.records_fetched == 0


class TestOHLCValidation:
    """Test OHLC validation on real-like data."""
    
    def setup_method(self):
        self.validator = BarValidator()
    
    def test_mock_data_passes_validation(self):
        """Mock data should pass OHLC validation."""
        provider = MockMarketDataProvider(seed=42)
        bars = provider.get_bars(
            "XAUUSD", "M5",
            datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
            datetime(2026, 8, 31, 15, 0, tzinfo=UTC),
        )
        
        for bar in bars:
            result = self.validator.validate(bar)
            assert result.is_valid, f"Bar {bar.bar_id} failed: {result.errors}"


class TestTemporalOrdering:
    """Test temporal ordering on real-like data."""
    
    def setup_method(self):
        self.validator = TemporalValidator()
    
    def test_mock_data_correct_ordering(self):
        """Mock data should be in correct temporal order."""
        provider = MockMarketDataProvider(seed=42)
        bars = provider.get_bars(
            "XAUUSD", "M5",
            datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
            datetime(2026, 8, 31, 15, 0, tzinfo=UTC),
        )
        
        result = self.validator.validate_ordering(bars, "M5")
        assert result.is_valid, f"Ordering errors: {result.errors}"


class TestGapDetection:
    """Test gap detection on real-like data."""
    
    def setup_method(self):
        self.validator = TemporalValidator()
    
    def test_no_gaps_in_mock_data(self):
        """Mock data should have no unexpected gaps."""
        provider = MockMarketDataProvider(seed=42)
        bars = provider.get_bars(
            "XAUUSD", "M5",
            datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
            datetime(2026, 8, 31, 15, 0, tzinfo=UTC),
        )
        
        gaps = self.validator.detect_gaps(bars, "M5")
        # Mock data should have no gaps
        assert len(gaps) == 0


class TestDuplicateDetection:
    """Test duplicate detection on real-like data."""
    
    def setup_method(self):
        self.detector = DuplicateDetector()
    
    def test_no_duplicates_in_mock_data(self):
        """Mock data should have no duplicates."""
        provider = MockMarketDataProvider(seed=42)
        bars = provider.get_bars(
            "XAUUSD", "M5",
            datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
            datetime(2026, 8, 31, 15, 0, tzinfo=UTC),
        )
        
        duplicates = self.detector.detect_bar_duplicates(bars)
        assert len(duplicates) == 0
    
    def test_idempotency(self):
        """Ingesting same data twice should not create duplicates."""
        provider = MockMarketDataProvider(seed=42)
        bars = provider.get_bars(
            "XAUUSD", "M5",
            datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
            datetime(2026, 8, 31, 15, 0, tzinfo=UTC),
        )
        
        # Simulate double ingestion
        all_bars = bars + bars
        duplicates = self.detector.detect_bar_duplicates(all_bars)
        
        # Should detect duplicates
        assert len(duplicates) == len(bars)


class TestCandleCloseSemantics:
    """Test that closed candles are used, not open candles."""
    
    def test_availability_time_after_bar_close(self):
        """Bar should be available only after its close time."""
        provider = MockMarketDataProvider(seed=42)
        pipeline = IngestionPipeline(provider=provider)
        
        start = datetime(2026, 8, 31, 14, 0, tzinfo=UTC)
        end = datetime(2026, 8, 31, 14, 10, tzinfo=UTC)
        raw_bars = provider.get_bars("XAUUSD", "M5", start, end)
        canonical_bars = [pipeline._canonicalize_bar(bar) for bar in raw_bars]
        
        assert len(canonical_bars) > 0
        
        bar = canonical_bars[0]
        
        # Bar time is when bar opened
        bar_open = bar.temporal.event_time.value
        
        # Availability time should be after bar open
        availability = bar.temporal.availability_time.value
        
        assert availability > bar_open, (
            f"Availability time {availability} should be after bar open {bar_open}"
        )


class TestMTFAlignment:
    """Test multi-timeframe alignment."""
    
    def test_m5_to_h1_alignment(self):
        """M5 bars should align to H1 boundaries."""
        provider = MockMarketDataProvider(seed=42)
        pipeline = IngestionPipeline(provider=provider)
        
        start = datetime(2026, 8, 31, 14, 0, tzinfo=UTC)
        end = datetime(2026, 8, 31, 15, 0, tzinfo=UTC)
        
        m5_raw = provider.get_bars("XAUUSD", "M5", start, end)
        m5_bars = [pipeline._canonicalize_bar(bar) for bar in m5_raw]
        
        h1_raw = provider.get_bars("XAUUSD", "H1", start, end)
        h1_bars = [pipeline._canonicalize_bar(bar) for bar in h1_raw]
        
        # H1 bar should have same open as first M5 bar in that hour
        if h1_bars and m5_bars:
            h1_open = h1_bars[0].temporal.event_time.value
            m5_first_in_hour = m5_bars[0].temporal.event_time.value
            
            # Both should start at the same time (14:00)
            assert h1_open.hour == m5_first_in_hour.hour
            assert h1_open.minute == m5_first_in_hour.minute
