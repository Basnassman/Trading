"""Mock Market Data Provider for testing.

Generates synthetic XAUUSD data for validation testing.
DO NOT use for real trading decisions.

Returns RawBar/RawTick — the ingestion pipeline handles canonicalization.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random

from src.providers.interfaces import MarketDataProvider
from src.canonical.raw import RawBar, RawTick
from src.canonical.contracts import AccountInfo, TemporalBounds
from src.canonical.time import EventTime, AvailabilityTime, IngestionTime, utcnow


UTC = timezone.utc


class MockMarketDataProvider(MarketDataProvider):
    """Mock market data provider for testing.

    Generates synthetic XAUUSD-like data.
    Returns RawBar/RawTick for pipeline canonicalization.
    DO NOT use for real trading.
    """

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)
        self._base_price = 1850.0

    def _generate_raw_bar(
        self,
        bar_time: datetime,
        timeframe: str,
        prev_close: float | None = None,
    ) -> RawBar:
        """Generate a synthetic raw bar."""
        base = prev_close or self._base_price

        # Random walk
        change = self._rng.gauss(0, 2.0)
        open_price = base
        close_price = base + change
        high_price = max(open_price, close_price) + abs(self._rng.gauss(0, 1.0))
        low_price = min(open_price, close_price) - abs(self._rng.gauss(0, 1.0))

        # Ensure OHLC consistency
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)

        tick_volume = max(1, int(self._rng.gauss(100, 30)))

        return RawBar(
            symbol="XAUUSD",
            timeframe=timeframe,
            bar_time=bar_time,
            open=Decimal(str(round(open_price, 2))),
            high=Decimal(str(round(high_price, 2))),
            low=Decimal(str(round(low_price, 2))),
            close=Decimal(str(round(close_price, 2))),
            tick_volume=tick_volume,
            bid=Decimal(str(round(close_price, 2))),
            ask=Decimal(str(round(close_price + 0.3, 2))),
            provider="mock",
            provider_symbol="XAUUSD",
        )

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: int | None = None,
    ) -> list[RawBar]:
        """Generate synthetic raw bars."""
        tf_minutes = {
            "M1": 1, "M5": 5, "M15": 15,
            "H1": 60, "H4": 240, "D1": 1440,
        }.get(timeframe, 5)

        bars = []
        current = start
        prev_close = None

        while current < end:
            bar = self._generate_raw_bar(current, timeframe, prev_close)
            bars.append(bar)
            prev_close = float(bar.close)
            current += timedelta(minutes=tf_minutes)

        if limit and len(bars) > limit:
            bars = bars[-limit:]

        return bars

    def get_ticks(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        limit: int | None = None,
    ) -> list[RawTick]:
        """Generate synthetic raw ticks."""
        ticks = []
        current = start

        while current < end:
            price = self._base_price + self._rng.gauss(0, 5.0)
            spread = abs(self._rng.gauss(0.3, 0.1))

            tick = RawTick(
                symbol=symbol,
                bid=Decimal(str(round(price, 2))),
                ask=Decimal(str(round(price + spread, 2))),
                timestamp=current,
                provider="mock",
                provider_symbol=symbol,
            )
            ticks.append(tick)
            current += timedelta(seconds=1)

        if limit and len(ticks) > limit:
            ticks = ticks[-limit:]

        return ticks

    def get_spread(self, symbol: str, timestamp: datetime) -> float:
        """Generate synthetic spread."""
        return abs(self._rng.gauss(0.3, 0.1))

    def get_account_info(self) -> AccountInfo:
        """Generate synthetic account info."""
        now = utcnow()
        return AccountInfo(
            account_id="mock_account",
            balance=Decimal("10000.00"),
            equity=Decimal("10000.00"),
            margin=Decimal("0.00"),
            free_margin=Decimal("10000.00"),
            temporal=TemporalBounds(
                event_time=EventTime(now),
                availability_time=AvailabilityTime(now),
                ingestion_time=IngestionTime(now),
            ),
        )

    def subscribe_bars(self, symbol: str, timeframe: str, callback) -> str:
        """Mock subscription."""
        return f"mock_sub_{symbol}_{timeframe}"

    def subscribe_ticks(self, symbol: str, callback) -> str:
        """Mock subscription."""
        return f"mock_sub_{symbol}_tick"

    def unsubscribe(self, subscription_id: str) -> bool:
        """Mock unsubscribe."""
        return True
