"""Data validation layer for the XAUUSD Trading System.

Validates raw data from providers before canonicalization.
Does NOT modify or delete records — only validates and classifies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from src.canonical.raw import RawBar, RawTick
from src.errors.exceptions import InvalidData


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating a single record."""
    is_valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    quality_status: str = "valid"  # "valid", "warning", "invalid"


@dataclass(frozen=True)
class ValidationReport:
    """Aggregate validation report for a batch of records."""
    total_records: int
    valid_records: int
    warning_records: int
    invalid_records: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class BarValidator:
    """Validates OHLCV bars."""
    
    def validate(self, bar: RawBar) -> ValidationResult:
        """Validate a single bar."""
        errors = []
        warnings = []
        
        # Price > 0
        if bar.open <= 0:
            errors.append(f"Open price <= 0: {bar.open}")
        if bar.high <= 0:
            errors.append(f"High price <= 0: {bar.high}")
        if bar.low <= 0:
            errors.append(f"Low price <= 0: {bar.low}")
        if bar.close <= 0:
            errors.append(f"Close price <= 0: {bar.close}")
        
        # High >= max(Open, Close)
        if bar.high < max(bar.open, bar.close):
            errors.append(f"High {bar.high} < max(Open={bar.open}, Close={bar.close})")
        
        # Low <= min(Open, Close)
        if bar.low > min(bar.open, bar.close):
            errors.append(f"Low {bar.low} > min(Open={bar.open}, Close={bar.close})")
        
        # High >= Low
        if bar.high < bar.low:
            errors.append(f"High {bar.high} < Low {bar.low}")
        
        # Volume >= 0
        if bar.tick_volume < 0:
            errors.append(f"Tick volume < 0: {bar.tick_volume}")
        
        # Spread validity (use bid_at_close/ask_at_close if available)
        bid = getattr(bar, 'bid_at_close', None) or getattr(bar, 'bid', None)
        ask = getattr(bar, 'ask_at_close', None) or getattr(bar, 'ask', None)
        if bid is not None and ask is not None:
            if bid > ask:
                errors.append(f"Bid {bid} > Ask {ask}")
        
        # Timestamp
        bar_time = getattr(bar, 'bar_time', None)
        if bar_time is not None and bar_time.tzinfo is None:
            errors.append("Bar time is naive (no timezone)")
        
        # Extreme price jump (> 10% in one bar)
        if bar.open > 0:
            jump_pct = abs(float(bar.close - bar.open)) / float(bar.open)
            if jump_pct > 0.10:
                warnings.append(f"Extreme price jump: {jump_pct:.1%}")
        
        # Zero range (doji)
        if bar.high == bar.low:
            warnings.append("Zero range bar (doji)")
        
        is_valid = len(errors) == 0
        quality_status = "valid" if not errors else ("warning" if not errors else "invalid")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=tuple(errors),
            warnings=tuple(warnings),
            quality_status=quality_status,
        )
    
    def validate_batch(self, bars: list[RawBar]) -> ValidationReport:
        """Validate a batch of bars."""
        results = [self.validate(bar) for bar in bars]
        
        valid = sum(1 for r in results if r.is_valid and not r.warnings)
        warning = sum(1 for r in results if r.is_valid and r.warnings)
        invalid = sum(1 for r in results if not r.is_valid)
        
        all_errors = []
        all_warnings = []
        for r in results:
            all_errors.extend(r.errors)
            all_warnings.extend(r.warnings)
        
        return ValidationReport(
            total_records=len(bars),
            valid_records=valid,
            warning_records=warning,
            invalid_records=invalid,
            errors=all_errors,
            warnings=all_warnings,
        )


class TickValidator:
    """Validates tick data."""
    
    def validate(self, tick: RawTick) -> ValidationResult:
        """Validate a single tick."""
        errors = []
        warnings = []
        
        # Bid > 0, Ask > 0
        if tick.bid <= 0:
            errors.append(f"Bid <= 0: {tick.bid}")
        if tick.ask <= 0:
            errors.append(f"Ask <= 0: {tick.ask}")
        
        # Bid <= Ask
        if tick.bid > tick.ask:
            errors.append(f"Bid {tick.bid} > Ask {tick.ask}")
        
        # Volume >= 0
        if tick.volume is not None and tick.volume < 0:
            errors.append(f"Volume < 0: {tick.volume}")
        
        # Timestamp
        if tick.timestamp.tzinfo is None:
            errors.append("Timestamp is naive (no timezone)")
        
        # Extreme spread
        if tick.bid > 0 and tick.ask > 0:
            spread_pips = float(tick.ask - tick.bid) * 10  # Assuming 2 decimal places
            if spread_pips > 100:
                warnings.append(f"Extreme spread: {spread_pips} pips")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=tuple(errors),
            warnings=tuple(warnings),
            quality_status="valid" if is_valid else "invalid",
        )


class TemporalValidator:
    """Validates temporal ordering and gaps."""
    
    def validate_ordering(
        self,
        bars: list[RawBar],
        timeframe: str,
    ) -> ValidationResult:
        """Validate that bars are in chronological order."""
        errors = []
        warnings = []
        
        if len(bars) < 2:
            return ValidationResult(is_valid=True)
        
        for i in range(1, len(bars)):
            t_i = getattr(bars[i], 'bar_time', None) or bars[i].temporal.event_time.value
            t_prev = getattr(bars[i-1], 'bar_time', None) or bars[i-1].temporal.event_time.value
            if t_i <= t_prev:
                errors.append(
                    f"Out of order: bar {i} time {t_i} "
                    f"<= bar {i-1} time {t_prev}"
                )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )
    
    def detect_gaps(
        self,
        bars: list[RawBar],
        timeframe: str,
    ) -> list[dict]:
        """Detect gaps in bar sequence."""
        gaps = []
        
        if len(bars) < 2:
            return gaps
        
        # Expected interval based on timeframe
        intervals = {
            "M1": timedelta(minutes=1),
            "M5": timedelta(minutes=5),
            "M15": timedelta(minutes=15),
            "H1": timedelta(hours=1),
            "H4": timedelta(hours=4),
            "D1": timedelta(days=1),
        }
        
        expected_interval = intervals.get(timeframe)
        if expected_interval is None:
            return gaps
        
        for i in range(1, len(bars)):
            t_i = getattr(bars[i], 'bar_time', None) or bars[i].temporal.event_time.value
            t_prev = getattr(bars[i-1], 'bar_time', None) or bars[i-1].temporal.event_time.value
            actual_gap = t_i - t_prev
            
            # Allow some tolerance (e.g., 2x expected interval)
            if actual_gap > expected_interval * 2:
                gap_type = self._classify_gap(bars[i-1].bar_time, bars[i].bar_time)
                gaps.append({
                    "start": t_prev,
                    "end": t_i,
                    "expected_interval": expected_interval,
                    "actual_gap": actual_gap,
                    "type": gap_type,
                })
        
        return gaps
    
    def _classify_gap(self, start: datetime, end: datetime) -> str:  # noqa: E501
        """Classify gap type."""
        # Weekend gap (Saturday-Sunday)
        if start.weekday() == 4 and end.weekday() == 0:  # Fri -> Mon
            return "expected_weekend"
        
        # Holiday gap (Monday after Friday close)
        if start.weekday() == 4 and end.weekday() == 0:
            return "expected_weekend"
        
        # Session gap (off-hours)
        if start.hour >= 22 or end.hour < 2:
            return "expected_session"
        
        return "unexpected"


class DuplicateDetector:
    """Detects duplicate records."""
    
    def detect_bar_duplicates(
        self,
        bars: list[RawBar],
    ) -> list[RawBar]:
        """Return duplicate bars (same symbol, timeframe, bar_time)."""
        seen = {}
        duplicates = []
        
        for bar in bars:
            bar_time = getattr(bar, 'bar_time', None) or bar.temporal.event_time.value
            key = (bar.symbol, bar.timeframe, bar_time)
            if key in seen:
                duplicates.append(bar)
            else:
                seen[key] = bar
        
        return duplicates
    
    def detect_tick_duplicates(
        self,
        ticks: list[RawTick],
    ) -> list[RawTick]:
        """Return duplicate ticks (same symbol, timestamp)."""
        seen = {}
        duplicates = []
        
        for tick in ticks:
            key = (tick.symbol, tick.timestamp)
            if key in seen:
                duplicates.append(tick)
            else:
                seen[key] = tick
        
        return duplicates
