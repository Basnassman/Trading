"""MT5 Market Data Provider implementation.

READ-ONLY data access. No order placement.
Returns RawBar/RawTick — the ingestion pipeline handles canonicalization.

Symbol mapping is configurable — not hardcoded.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from src.providers.interfaces import MarketDataProvider
from src.canonical.raw import RawBar, RawTick
from src.canonical.contracts import AccountInfo, TemporalBounds
from src.canonical.enums import Timeframe
from src.canonical.time import EventTime, AvailabilityTime, IngestionTime, utcnow


# MT5 timeframe mapping
TIMEFRAME_MAP = {
    "M1": 1,      # mt5.TIMEFRAME_M1
    "M5": 5,      # mt5.TIMEFRAME_M5
    "M15": 15,    # mt5.TIMEFRAME_M15
    "H1": 60,     # mt5.TIMEFRAME_H1
    "H4": 240,    # mt5.TIMEFRAME_H4
    "D1": 1440,   # mt5.TIMEFRAME_D1
    "W1": 10080,  # mt5.TIMEFRAME_W1
    "MN1": 43200, # mt5.TIMEFRAME_MN1
}


class MT5MarketDataProvider(MarketDataProvider):
    """MT5 Market Data Provider.

    READ-ONLY: Does not place orders.
    Returns RawBar/RawTick — pipeline handles canonicalization.

    Symbol mapping:
        internal_symbol → mt5_symbol
        Configurable via symbol_map parameter.
    """

    def __init__(
        self,
        symbol_map: dict[str, str] | None = None,
        mt5_path: str | None = None,
        mt5_login: int | None = None,
        mt5_password: str | None = None,
        mt5_server: str | None = None,
    ):
        self._symbol_map = symbol_map or {}
        self._mt5 = None
        self._connected = False

        self._mt5_path = mt5_path
        self._mt5_login = mt5_login
        self._mt5_password = mt5_password
        self._mt5_server = mt5_server

    def _ensure_connected(self) -> None:
        """Ensure MT5 connection is active."""
        if self._connected:
            return

        try:
            import MetaTrader5 as mt5

            self._mt5 = mt5

            init_args = {}
            if self._mt5_path:
                init_args["path"] = self._mt5_path

            if not mt5.initialize(**init_args):
                raise ConnectionError(f"MT5 initialization failed: {mt5.last_error()}")

            if self._mt5_login and self._mt5_password and self._mt5_server:
                authorized = mt5.login(
                    login=self._mt5_login,
                    password=self._mt5_password,
                    server=self._mt5_server,
                )
                if not authorized:
                    raise ConnectionError(f"MT5 login failed: {mt5.last_error()}")

            self._connected = True

        except ImportError:
            raise ImportError(
                "MetaTrader5 package not installed. "
                "Install with: pip install MetaTrader5"
            )

    def _map_symbol(self, symbol: str) -> str:
        """Map internal symbol to MT5 symbol."""
        return self._symbol_map.get(symbol, symbol)

    def _get_mt5_timeframe(self, timeframe: str) -> int:
        """Convert timeframe string to MT5 timeframe constant."""
        tf = TIMEFRAME_MAP.get(timeframe)
        if tf is None:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        return tf

    def _convert_bar(self, mt5_bar, symbol: str, timeframe: str) -> RawBar:
        """Convert MT5 bar to RawBar.

        Returns raw data — the pipeline handles canonicalization
        (availability_time computation, validation, etc.).
        """
        bar_time = datetime.fromtimestamp(mt5_bar[0], tz=timezone.utc)

        real_vol = int(mt5_bar[6]) if len(mt5_bar) > 6 and mt5_bar[6] > 0 else None

        return RawBar(
            symbol=symbol,
            timeframe=timeframe,
            bar_time=bar_time,
            open=Decimal(str(mt5_bar[1])),
            high=Decimal(str(mt5_bar[2])),
            low=Decimal(str(mt5_bar[3])),
            close=Decimal(str(mt5_bar[4])),
            tick_volume=int(mt5_bar[5]),
            real_volume=real_vol,
            bid=Decimal(str(mt5_bar[4])),  # Use close as bid proxy
            ask=Decimal(str(mt5_bar[4])),
            provider="mt5",
            provider_symbol=self._map_symbol(symbol),
        )

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: int | None = None,
    ) -> list[RawBar]:
        """Fetch historical bars from MT5.

        Returns RawBar — the ingestion pipeline handles canonicalization.
        """
        self._ensure_connected()

        mt5_symbol = self._map_symbol(symbol)
        mt5_tf = self._get_mt5_timeframe(timeframe)

        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())

        rates = self._mt5.copy_rates_range(mt5_symbol, mt5_tf, start_ts, end_ts)

        if rates is None or len(rates) == 0:
            return []

        bars = [self._convert_bar(rate, symbol, timeframe) for rate in rates]

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
        """Fetch tick data from MT5.

        Returns RawTick — the ingestion pipeline handles canonicalization.
        """
        self._ensure_connected()

        mt5_symbol = self._map_symbol(symbol)

        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())

        ticks = self._mt5.copy_ticks_range(mt5_symbol, start_ts, end_ts)

        if ticks is None or len(ticks) == 0:
            return []

        result = []
        for tick in ticks:
            tick_time = datetime.fromtimestamp(tick[0], tz=timezone.utc)

            result.append(RawTick(
                symbol=symbol,
                bid=Decimal(str(tick[1])),
                ask=Decimal(str(tick[2])),
                timestamp=tick_time,
                volume=int(tick[3]) if tick[3] > 0 else None,
                provider="mt5",
                provider_symbol=self._map_symbol(symbol),
            ))

        if limit and len(result) > limit:
            result = result[-limit:]

        return result

    def get_spread(self, symbol: str, timestamp: datetime) -> float:
        """Get current spread."""
        self._ensure_connected()

        mt5_symbol = self._map_symbol(symbol)
        tick = self._mt5.symbol_info_tick(mt5_symbol)

        if tick is None:
            return 0.0

        return float(tick.ask - tick.bid)

    def get_account_info(self) -> AccountInfo:
        """Get current account state."""
        self._ensure_connected()

        info = self._mt5.account_info()
        if info is None:
            raise ConnectionError("Failed to get account info from MT5")

        now = utcnow()
        return AccountInfo(
            account_id=str(info.login),
            balance=Decimal(str(info.balance)),
            equity=Decimal(str(info.equity)),
            margin=Decimal(str(info.margin)),
            free_margin=Decimal(str(info.margin_free)),
            temporal=TemporalBounds(
                event_time=EventTime(now),
                availability_time=AvailabilityTime(now),
                ingestion_time=IngestionTime(now),
            ),
        )

    def subscribe_bars(self, symbol: str, timeframe: str, callback) -> str:
        """Subscribe to real-time bars."""
        self._ensure_connected()

        mt5_symbol = self._map_symbol(symbol)
        mt5_tf = self._get_mt5_timeframe(timeframe)

        self._mt5.symbol_select(mt5_symbol, True)

        sub_id = f"mt5_{symbol}_{timeframe}"
        return sub_id

    def subscribe_ticks(self, symbol: str, callback) -> str:
        """Subscribe to real-time ticks."""
        self._ensure_connected()

        mt5_symbol = self._map_symbol(symbol)
        self._mt5.symbol_select(mt5_symbol, True)

        sub_id = f"mt5_{symbol}_tick"
        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from data feed."""
        return True

    def disconnect(self) -> None:
        """Disconnect from MT5."""
        if self._mt5 and self._connected:
            self._mt5.shutdown()
            self._connected = False
