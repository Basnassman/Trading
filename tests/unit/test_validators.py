"""Unit tests for data validation layer."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.canonical.raw import RawBar
from src.validation.validators import BarValidator, TemporalValidator, DuplicateDetector


UTC = timezone.utc


def make_raw_bar(
    bar_time: datetime | None = None,
    open_price: float = 1850.0,
    high_price: float = 1855.0,
    low_price: float = 1848.0,
    close_price: float = 1853.0,
    tick_volume: int = 100,
) -> RawBar:
    """Helper to create a RawBar."""
    return RawBar(
        symbol="XAUUSD",
        timeframe="M5",
        open=Decimal(str(open_price)),
        high=Decimal(str(high_price)),
        low=Decimal(str(low_price)),
        close=Decimal(str(close_price)),
        tick_volume=tick_volume,
        bar_time=bar_time or datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
    )


class TestBarValidator:
    """Test bar validation."""
    
    def setup_method(self):
        self.validator = BarValidator()
    
    def test_valid_bar(self):
        """Valid bar should pass validation."""
        bar = make_raw_bar()
        result = self.validator.validate(bar)
        assert result.is_valid
    
    def test_high_below_open(self):
        """High below open should fail."""
        bar = make_raw_bar(high_price=1849.0)  # Below open=1850
        result = self.validator.validate(bar)
        assert not result.is_valid
        assert any("High" in e for e in result.errors)
    
    def test_low_above_close(self):
        """Low above close should fail."""
        bar = make_raw_bar(low_price=1854.0)  # Above close=1853
        result = self.validator.validate(bar)
        assert not result.is_valid
        assert any("Low" in e for e in result.errors)
    
    def test_high_below_low(self):
        """High below low should fail."""
        bar = RawBar(
            symbol="XAUUSD",
            timeframe="M5",
            open=Decimal("1850"),
            high=Decimal("1845"),
            low=Decimal("1848"),
            close=Decimal("1853"),
            tick_volume=100,
            bar_time=datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
        )
        result = self.validator.validate(bar)
        assert not result.is_valid
    
    def test_negative_volume(self):
        """Negative volume should fail."""
        bar = make_raw_bar(tick_volume=-10)
        result = self.validator.validate(bar)
        assert not result.is_valid
    
    def test_zero_price(self):
        """Zero price should fail."""
        bar = make_raw_bar(open_price=0.0)
        result = self.validator.validate(bar)
        assert not result.is_valid
    
    def test_bid_greater_than_ask(self):
        """Bid > Ask should fail."""
        bar = RawBar(
            symbol="XAUUSD",
            timeframe="M5",
            open=Decimal("1850"),
            high=Decimal("1855"),
            low=Decimal("1848"),
            close=Decimal("1853"),
            tick_volume=100,
            bar_time=datetime(2026, 8, 31, 14, 0, tzinfo=UTC),
            bid=Decimal("1853.50"),
            ask=Decimal("1853.00"),  # Ask < Bid
        )
        result = self.validator.validate(bar)
        assert not result.is_valid
    
    def test_naive_timestamp(self):
        """Naive timestamp should fail."""
        bar = RawBar(
            symbol="XAUUSD",
            timeframe="M5",
            open=Decimal("1850"),
            high=Decimal("1855"),
            low=Decimal("1848"),
            close=Decimal("1853"),
            tick_volume=100,
            bar_time=datetime(2026, 8, 31, 14, 0),  # No timezone
        )
        result = self.validator.validate(bar)
        assert not result.is_valid
    
    def test_extreme_price_jump_warning(self):
        """Extreme price jump should warn but still be valid OHLC."""
        bar = make_raw_bar(open_price=1850.0, high_price=2060.0, low_price=1845.0, close_price=2050.0)
        result = self.validator.validate(bar)
        assert result.is_valid  # Valid OHLC, but with warning
        assert any("Extreme price jump" in w for w in result.warnings)


class TestTemporalValidator:
    """Test temporal validation."""
    
    def setup_method(self):
        self.validator = TemporalValidator()
    
    def test_correct_ordering(self):
        """Correctly ordered bars should pass."""
        bars = [
            make_raw_bar(bar_time=datetime(2026, 8, 31, 14, 0, tzinfo=UTC)),
            make_raw_bar(bar_time=datetime(2026, 8, 31, 14, 5, tzinfo=UTC)),
            make_raw_bar(bar_time=datetime(2026, 8, 31, 14, 10, tzinfo=UTC)),
        ]
        result = self.validator.validate_ordering(bars, "M5")
        assert result.is_valid
    
    def test_out_of_order(self):
        """Out of order bars should fail."""
        bars = [
            make_raw_bar(bar_time=datetime(2026, 8, 31, 14, 5, tzinfo=UTC)),
            make_raw_bar(bar_time=datetime(2026, 8, 31, 14, 0, tzinfo=UTC)),  # Earlier
        ]
        result = self.validator.validate_ordering(bars, "M5")
        assert not result.is_valid


class TestDuplicateDetector:
    """Test duplicate detection."""
    
    def setup_method(self):
        self.detector = DuplicateDetector()
    
    def test_no_duplicates(self):
        """Unique bars should have no duplicates."""
        bars = [
            make_raw_bar(bar_time=datetime(2026, 8, 31, 14, 0, tzinfo=UTC)),
            make_raw_bar(bar_time=datetime(2026, 8, 31, 14, 5, tzinfo=UTC)),
        ]
        duplicates = self.detector.detect_bar_duplicates(bars)
        assert len(duplicates) == 0
    
    def test_duplicates(self):
        """Duplicate bars should be detected."""
        t = datetime(2026, 8, 31, 14, 0, tzinfo=UTC)
        bars = [
            make_raw_bar(bar_time=t),
            make_raw_bar(bar_time=t),  # Duplicate
        ]
        duplicates = self.detector.detect_bar_duplicates(bars)
        assert len(duplicates) == 1
