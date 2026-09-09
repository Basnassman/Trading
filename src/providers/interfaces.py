"""Abstract provider interfaces for the XAUUSD Trading System.

Trading logic depends ONLY on these interfaces.
Concrete implementations (MT5, Paper, Backtest) are injected at runtime.

This ensures:
- Source Abstraction (P8)
- Dependency Inversion (P7)
- Backtest/Paper/Live Parity
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.canonical.raw import RawBar, RawTick
from src.canonical.contracts import (
    CanonicalNewsEvent, CanonicalMacroObservation,
    AccountInfo, OrderRequest, OrderResult, CanonicalPosition,
)
from src.canonical.enums import Timeframe


# ─────────────────────────────────────────────
# MARKET DATA PROVIDER
# ─────────────────────────────────────────────

class MarketDataProvider(ABC):
    """Abstract interface for market data."""
    
    @abstractmethod
    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: int | None = None,
    ) -> list[RawBar]:
        """Fetch historical bars.
        
        Returns RAW data — the ingestion pipeline handles validation
        and canonicalization.
        
        Args:
            symbol: Instrument symbol (e.g., "XAUUSD")
            timeframe: Bar timeframe string
            start: Start time (UTC)
            end: End time (UTC)
            limit: Maximum number of bars
        
        Returns:
            List of RawBar in chronological order
        """
        ...
    
    @abstractmethod
    def get_ticks(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        limit: int | None = None,
    ) -> list[RawTick]:
        """Fetch tick data.
        
        Args:
            symbol: Instrument symbol
            start: Start time (UTC)
            end: End time (UTC)
            limit: Maximum number of ticks
        
        Returns:
            List of ticks in chronological order
        """
        ...
    
    @abstractmethod
    def get_spread(self, symbol: str, timestamp: datetime) -> float:
        """Get current spread in pips.
        
        Args:
            symbol: Instrument symbol
            timestamp: Time to get spread for
        
        Returns:
            Spread in pips
        """
        ...
    
    @abstractmethod
    def get_account_info(self) -> AccountInfo:
        """Get current account state.
        
        Returns:
            Account balance, equity, margin, etc.
        """
        ...
    
    @abstractmethod
    def subscribe_bars(
        self,
        symbol: str,
        timeframe: Timeframe,
        callback,
    ) -> str:
        """Subscribe to real-time bar updates.
        
        Args:
            symbol: Instrument symbol
            timeframe: Bar timeframe
            callback: Function to call with new bars
        
        Returns:
            Subscription ID for unsubscribing
        """
        ...
    
    @abstractmethod
    def subscribe_ticks(self, symbol: str, callback) -> str:
        """Subscribe to real-time tick updates.
        
        Args:
            symbol: Instrument symbol
            callback: Function to call with new ticks
        
        Returns:
            Subscription ID for unsubscribing
        """
        ...
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from updates.
        
        Args:
            subscription_id: ID from subscribe_bars/subscribe_ticks
        
        Returns:
            True if successfully unsubscribed
        """
        ...


# ─────────────────────────────────────────────
# NEWS PROVIDER
# ─────────────────────────────────────────────

class NewsProvider(ABC):
    """Abstract interface for news data."""
    
    @abstractmethod
    def get_events(
        self,
        start: datetime,
        end: datetime,
        currencies: list[str] | None = None,
        min_importance: int = 1,
    ) -> list[CanonicalNewsEvent]:
        """Fetch economic events.
        
        Args:
            start: Start time (UTC)
            end: End time (UTC)
            currencies: Filter by currency (None = all)
            min_importance: Minimum importance level (1-4)
        
        Returns:
            List of news events
        """
        ...
    
    @abstractmethod
    def get_upcoming_events(
        self,
        hours_ahead: int = 24,
        min_importance: int = 3,
    ) -> list[CanonicalNewsEvent]:
        """Fetch upcoming high-impact events.
        
        Args:
            hours_ahead: How far ahead to look
            min_importance: Minimum importance level
        
        Returns:
            List of upcoming events
        """
        ...
    
    @abstractmethod
    def subscribe_events(self, callback) -> str:
        """Subscribe to real-time event updates.
        
        Args:
            callback: Function to call with new/updated events
        
        Returns:
            Subscription ID
        """
        ...


# ─────────────────────────────────────────────
# MACRO PROVIDER
# ─────────────────────────────────────────────

class MacroProvider(ABC):
    """Abstract interface for macro data."""
    
    @abstractmethod
    def get_indicator(
        self,
        indicator: str,
        start: datetime,
        end: datetime,
    ) -> list[CanonicalMacroObservation]:
        """Fetch macro indicator values.
        
        Args:
            indicator: Indicator name (e.g., "DXY", "US_10Y_YIELD")
            start: Start time (UTC)
            end: End time (UTC)
        
        Returns:
            List of observations in chronological order
        """
        ...
    
    @abstractmethod
    def get_latest(self, indicator: str) -> Optional[CanonicalMacroObservation]:
        """Get latest value for indicator.
        
        Args:
            indicator: Indicator name
        
        Returns:
            Latest observation or None if unavailable
        """
        ...


# ─────────────────────────────────────────────
# EXECUTION PROVIDER
# ─────────────────────────────────────────────

class ExecutionProvider(ABC):
    """Abstract interface for order execution.
    
    This is the ONLY interface through which trading logic
    interacts with the broker/exchange.
    """
    
    @abstractmethod
    def submit_order(self, order: OrderRequest) -> OrderResult:
        """Submit an order.
        
        Args:
            order: Order to submit
        
        Returns:
            Execution result
        """
        ...
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order.
        
        Args:
            order_id: ID of order to cancel
        
        Returns:
            True if successfully cancelled
        """
        ...
    
    @abstractmethod
    def modify_position(
        self,
        position_id: str,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
    ) -> bool:
        """Modify SL/TP of existing position.
        
        Args:
            position_id: ID of position to modify
            sl: New stop loss (None = no change)
            tp: New take profit (None = no change)
        
        Returns:
            True if successfully modified
        """
        ...
    
    @abstractmethod
    def close_position(self, position_id: str) -> OrderResult:
        """Close a position.
        
        Args:
            position_id: ID of position to close
        
        Returns:
            Execution result
        """
        ...
    
    @abstractmethod
    def get_positions(self) -> list[CanonicalPosition]:
        """Get all open positions.
        
        Returns:
            List of open positions
        """
        ...
    
    @abstractmethod
    def get_account(self) -> AccountInfo:
        """Get account info.
        
        Returns:
            Account balance, equity, margin, etc.
        """
        ...
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection to broker is active.
        
        Returns:
            True if connected
        """
        ...
    
    @abstractmethod
    def get_last_error(self) -> Optional[str]:
        """Get last execution error message.
        
        Returns:
            Error message or None if no error
        """
        ...
