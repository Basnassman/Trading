"""Error model for the XAUUSD Trading System.

Defines system errors with clear semantics.
TemporalViolation is a CRITICAL error.
"""

from __future__ import annotations


class TradingSystemError(Exception):
    """Base exception for all trading system errors."""
    
    def __init__(self, message: str, module: str = "", context: dict | None = None):
        super().__init__(message)
        self.module = module
        self.context = context or {}


# ─────────────────────────────────────────────
# DATA ERRORS
# ─────────────────────────────────────────────

class DataError(TradingSystemError):
    """Base for data-related errors."""
    pass


class DataUnavailable(DataError):
    """Required data is not available."""
    pass


class StaleData(DataError):
    """Data is too old for use."""
    
    def __init__(self, message: str, age_seconds: float, max_age: float, **kwargs):
        super().__init__(message, **kwargs)
        self.age_seconds = age_seconds
        self.max_age = max_age


class InvalidData(DataError):
    """Data fails validation checks."""
    
    def __init__(self, message: str, field: str = "", value: any = None, **kwargs):
        super().__init__(message, **kwargs)
        self.field = field
        self.value = value


# ─────────────────────────────────────────────
# TEMPORAL ERRORS
# ─────────────────────────────────────────────

class TemporalViolation(TradingSystemError):
    """CRITICAL: Data used before availability_time.
    
    This is the most serious error in the system.
    It indicates a look-ahead bias or temporal logic bug.
    
    The system must NEVER proceed when this error occurs.
    """
    
    def __init__(
        self,
        message: str,
        feature_name: str = "",
        availability_time: any = None,
        current_time: any = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.feature_name = feature_name
        self.availability_time = availability_time
        self.current_time = current_time


# ─────────────────────────────────────────────
# PROVIDER ERRORS
# ─────────────────────────────────────────────

class ProviderError(TradingSystemError):
    """Base for provider-related errors."""
    pass


class ProviderUnavailable(ProviderError):
    """Data/execution provider is not available."""
    pass


class ProviderTimeout(ProviderError):
    """Provider request timed out."""
    pass


# ─────────────────────────────────────────────
# EXECUTION ERRORS
# ─────────────────────────────────────────────

class ExecutionError(TradingSystemError):
    """Base for execution-related errors."""
    pass


class ExecutionRejected(ExecutionError):
    """Order was rejected by broker."""
    
    def __init__(self, message: str, order_id: str = "", reason: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self.order_id = order_id
        self.reason = reason


class ExecutionTimeout(ExecutionError):
    """Order execution timed out."""
    pass


class PositionMismatch(ExecutionError):
    """Position state doesn't match expected state."""
    pass


# ─────────────────────────────────────────────
# CONFIGURATION ERRORS
# ─────────────────────────────────────────────

class ConfigurationError(TradingSystemError):
    """Configuration is invalid or missing."""
    pass


# ─────────────────────────────────────────────
# CONTRACT ERRORS
# ─────────────────────────────────────────────

class ContractViolation(TradingSystemError):
    """Data contract is violated."""
    
    def __init__(self, message: str, contract: str = "", field: str = "", **kwargs):
        super().__init__(message, **kwargs)
        self.contract = contract
        self.field = field
