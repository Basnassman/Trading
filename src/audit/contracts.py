"""Audit trail contracts for the XAUUSD Trading System.

Every decision must be fully reconstructable from the audit trail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from src.canonical.enums import DecisionType, NoTradeSeverity, MarketRegime
from src.canonical.time import TemporalBounds


@dataclass(frozen=True)
class AuditEvent:
    """Single audit event."""
    event_id: str
    event_type: str  # "decision", "execution", "error", "config_change"
    
    timestamp: datetime
    
    module: str
    message: str
    
    # Context
    decision_id: Optional[str] = None
    trade_id: Optional[str] = None
    
    # Data snapshot
    data_snapshot: dict[str, Any] = field(default_factory=dict)
    
    # Error info
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    
    version: str = "1.0"


@dataclass(frozen=True)
class DecisionAudit:
    """Complete audit trail for a trading decision.
    
    This record contains ALL information needed to reconstruct
    why a specific decision was made.
    """
    decision_id: str
    timestamp: datetime
    
    # Input snapshot
    price: float
    session: str
    regime: MarketRegime
    regime_confidence: float
    
    # Feature snapshot
    structure_score: float
    liquidity_score: float
    flow_score: float
    trend_score: float
    momentum_score: float
    volatility_score: float
    gsi_score: float
    
    # Evidence snapshot
    evidence_families: dict[str, float]  # family_name -> score
    
    # Probability snapshot
    p_long: float
    p_short: float
    p_no_trade: float
    probability_confidence: float
    calibration_status: str
    ece_score: Optional[float] = None
    
    # Setup snapshot
    setup_valid: bool
    setup_quality: float
    setup_direction: Optional[str] = None
    entry_trigger: Optional[str] = None
    rr_ratio: float = 0.0
    
    # Risk snapshot
    position_size: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    risk_amount: float = 0.0
    
    # No-Trade snapshot
    no_trade_severity: NoTradeSeverity = NoTradeSeverity.GREEN
    no_trade_conditions: tuple[str, ...] = ()
    
    # Decision
    decision: DecisionType = DecisionType.NO_TRADE
    decision_reasons: tuple[str, ...] = ()
    
    # Execution
    execution_result: Optional[str] = None
    fill_price: Optional[float] = None
    slippage: Optional[float] = None
    latency_ms: Optional[float] = None
    
    # Versions
    model_version: str = ""
    parameter_version: str = ""
    formula_version: str = ""
    spec_version: str = ""
    
    version: str = "1.0"


@dataclass(frozen=True)
class ExecutionAudit:
    """Audit record for an execution event."""
    execution_id: str
    order_id: str
    decision_id: str
    
    timestamp: datetime
    
    action: str  # "submit", "fill", "cancel", "modify", "close"
    
    # Order details
    symbol: str
    side: str
    volume: float
    price: Optional[float] = None
    
    # Result
    status: str
    fill_price: Optional[float] = None
    slippage: Optional[float] = None
    
    # Error
    error: Optional[str] = None
    
    version: str = "1.0"


class StructuredLogger:
    """Interface for structured logging.
    
    Implementation will write to file, database, or external service.
    """
    
    def log_event(self, event: AuditEvent) -> None:
        """Log an audit event."""
        ...
    
    def log_decision(self, audit: DecisionAudit) -> None:
        """Log a decision audit record."""
        ...
    
    def log_execution(self, audit: ExecutionAudit) -> None:
        """Log an execution audit record."""
        ...
    
    def get_decision_audit(self, decision_id: str) -> Optional[DecisionAudit]:
        """Retrieve a decision audit record."""
        ...
    
    def get_decisions(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[DecisionAudit]:
        """Retrieve decisions in time range."""
        ...
