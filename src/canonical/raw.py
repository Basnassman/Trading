"""Raw data models for provider output.

These are the raw records returned by data providers BEFORE validation
and canonicalization. They carry the original provider's data format.

Flow: Provider → RawRecord → Validation → CanonicalRecord
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class RawBar:
    """Raw OHLCV bar from provider."""
    symbol: str
    timeframe: str
    bar_time: datetime  # Bar open time (from provider)
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    tick_volume: int
    real_volume: Optional[int] = None
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    provider: str = ""
    provider_symbol: str = ""
    retrieval_time: datetime = field(default_factory=lambda: datetime.utcnow())


@dataclass(frozen=True)
class RawTick:
    """Raw tick from provider."""
    symbol: str
    bid: Decimal
    ask: Decimal
    timestamp: datetime
    volume: Optional[int] = None
    provider: str = ""
    provider_symbol: str = ""
    retrieval_time: datetime = field(default_factory=lambda: datetime.utcnow())


@dataclass(frozen=True)
class RawNewsEvent:
    """Raw news event from provider."""
    name: str
    currency: str
    category: str
    importance: int
    release_time: datetime
    actual: Optional[Decimal] = None
    forecast: Optional[Decimal] = None
    previous: Optional[Decimal] = None
    unit: str = ""
    provider: str = ""
    retrieval_time: datetime = field(default_factory=lambda: datetime.utcnow())


@dataclass(frozen=True)
class RawMacroObservation:
    """Raw macro data from provider."""
    indicator: str
    value: Decimal
    observation_date: datetime
    provider: str = ""
    retrieval_time: datetime = field(default_factory=lambda: datetime.utcnow())
