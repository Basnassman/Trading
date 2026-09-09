"""Domain contracts for the XAUUSD Trading System.

Every entity in the system is represented as a frozen dataclass.
Each contract defines:
- Identity (id)
- Temporal bounds (event_time, availability_time, ingestion_time)
- Source and version
- Data quality and confidence

Where a field is not applicable to an entity, it is documented why.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional

from src.canonical.enums import (
    DataQuality, Direction, StructureState, SwingType, MarketRegime,
    FlowState, VolumeSource, DecisionType, SetupType, ExitReason,
    NoTradeSeverity, OrderType, OrderSide, OrderStatus, PositionStatus,
    NewsCategory, NewsImpact, SessionType, Timeframe, EvidenceFamily,
)
from src.canonical.time import TemporalBounds


# ─────────────────────────────────────────────
# MARKET DATA
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalBar:
    """Standardized OHLCV bar."""
    bar_id: str
    symbol: str
    timeframe: Timeframe
    temporal: TemporalBounds
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    tick_volume: int
    real_volume: Optional[int] = None
    spread_at_close: Optional[Decimal] = None
    bid_at_close: Optional[Decimal] = None
    ask_at_close: Optional[Decimal] = None
    data_quality: DataQuality = DataQuality.OBSERVED
    version: str = "1.0"


@dataclass(frozen=True)
class CanonicalTick:
    """Single tick data point."""
    tick_id: str
    symbol: str
    bid: Decimal
    ask: Decimal
    spread: Decimal
    temporal: TemporalBounds
    volume: Optional[int] = None
    data_quality: DataQuality = DataQuality.OBSERVED
    version: str = "1.0"


# ─────────────────────────────────────────────
# NEWS
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalNewsEvent:
    """Economic news event."""
    event_id: str
    name: str
    currency: str
    category: NewsCategory
    importance: NewsImpact
    release_time: datetime
    temporal: TemporalBounds
    actual_release_time: Optional[datetime] = None
    actual: Optional[Decimal] = None
    forecast: Optional[Decimal] = None
    previous: Optional[Decimal] = None
    previous_revised: Optional[Decimal] = None
    revision: Optional[Decimal] = None
    revision_time: Optional[datetime] = None
    unit: str = ""
    source: str = ""
    data_quality: DataQuality = DataQuality.OBSERVED
    version: str = "1.0"


@dataclass(frozen=True)
class CanonicalNewsRevision:
    """Revision to a previously published news event."""
    revision_id: str
    event_id: str
    original_value: Decimal
    revised_value: Decimal
    revision_amount: Decimal
    temporal: TemporalBounds
    data_quality: DataQuality = DataQuality.OBSERVED
    version: str = "1.0"


# ─────────────────────────────────────────────
# MACRO
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalMacroObservation:
    """Macro data point (DXY, Yield, FFR)."""
    observation_id: str
    indicator: str
    value: Decimal
    observation_date: datetime
    temporal: TemporalBounds
    source: str = ""
    freshness_seconds: float = 0.0
    data_quality: DataQuality = DataQuality.OBSERVED
    confidence: float = 1.0
    version: str = "1.0"


# ─────────────────────────────────────────────
# SESSION
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalSession:
    """Trading session definition."""
    session_id: str
    name: str
    session_type: SessionType
    open_time_local: time
    close_time_local: time
    timezone: str
    open_time_utc: datetime
    close_time_utc: datetime
    dst_active: bool
    date: date
    version: str = "1.0"


# ─────────────────────────────────────────────
# STRUCTURE
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalSwing:
    """Swing point (high or low)."""
    swing_id: str
    symbol: str
    timeframe: Timeframe
    swing_type: SwingType
    price: Decimal
    bar_time: datetime
    confirmation_time: datetime
    is_confirmed: bool
    strength: float
    temporal: TemporalBounds
    data_quality: DataQuality = DataQuality.INFERRED
    confidence: float = 1.0
    version: str = "1.0"


# ─────────────────────────────────────────────
# LIQUIDITY
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalLiquidityLevel:
    """Liquidity level."""
    level_id: str
    level_type: str
    price: Decimal
    strength: float
    formation_time: datetime
    temporal: TemporalBounds
    touch_count: int = 0
    last_test_time: Optional[datetime] = None
    data_quality: DataQuality = DataQuality.INFERRED
    confidence: float = 0.8
    version: str = "1.0"


@dataclass(frozen=True)
class CanonicalSweep:
    """Liquidity sweep event."""
    sweep_id: str
    sweep_type: str
    level_id: str
    level_price: Decimal
    penetration_depth: Decimal
    return_bars: int
    sweep_strength: float
    temporal: TemporalBounds
    data_quality: DataQuality = DataQuality.INFERRED
    confidence: float = 0.7
    version: str = "1.0"


# ─────────────────────────────────────────────
# FLOW
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalFlowObservation:
    """Institutional Flow Proxy observation."""
    observation_id: str
    symbol: str
    timeframe: Timeframe
    rvol: float
    buying_pressure: float
    selling_pressure: float
    candle_efficiency: float
    volume_acceleration: float
    mv_relationship: str
    ifp_score: float
    ifp_direction: Direction
    data_quality: DataQuality
    confidence: float
    volume_source: VolumeSource
    temporal: TemporalBounds
    version: str = "1.0"


# ─────────────────────────────────────────────
# FEATURES
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class FeatureRecord:
    """Single feature value with full metadata."""
    feature_id: str
    feature_name: str
    value: float
    source_engine: str
    formula_version: str
    quality: str
    confidence: float
    temporal: TemporalBounds
    input_features: tuple[str, ...] = ()
    input_data: tuple[str, ...] = ()
    version: str = "1.0"


# ─────────────────────────────────────────────
# EVIDENCE
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalEvidence:
    """Evidence from a single family."""
    evidence_id: str
    family: EvidenceFamily
    family_score: float
    members: dict[str, float]
    direction: Direction
    confidence: float
    temporal: TemporalBounds
    version: str = "1.0"


# ─────────────────────────────────────────────
# GSI
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalGSI:
    """Gold Smart Index observation.
    
    GSI is a DIAGNOSTIC INDEX only.
    GSI is NEVER an input to the Probability Engine.
    """
    gsi_id: str
    gsi_raw: float
    gsi_smooth: float
    direction: Direction
    confidence: float
    structure_score: float
    flow_score: float
    trend_score: float
    momentum_score: float
    volatility_score: float
    price_action_score: float
    weights: dict[str, float]
    temporal: TemporalBounds
    data_quality: DataQuality = DataQuality.INFERRED
    version: str = "1.0"


# ─────────────────────────────────────────────
# HISTORICAL
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalHistoricalMatch:
    """Historical similarity match."""
    match_id: str
    neighbor_index: int
    similarity: float
    outcome: str
    entry_price: Decimal
    target_price: Decimal
    stop_price: Decimal
    temporal: TemporalBounds
    data_quality: DataQuality = DataQuality.INFERRED
    version: str = "1.0"


# ─────────────────────────────────────────────
# PROBABILITY
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalProbability:
    """Probability prediction."""
    prediction_id: str
    p_long: float
    p_short: float
    p_no_trade: float
    confidence: float
    calibrated: bool
    temporal: TemporalBounds
    ece_score: Optional[float] = None
    calibration_method: Optional[str] = None
    families_active: int = 0
    families_aligned: int = 0
    data_quality: DataQuality = DataQuality.INFERRED
    version: str = "1.0"


# ─────────────────────────────────────────────
# REGIME
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalRegime:
    """Market regime observation."""
    regime_id: str
    regime: MarketRegime
    confidence: float
    duration_bars: int
    sl_multiplier: float
    tp_multiplier: float
    size_factor: float
    threshold_adjustment: float
    temporal: TemporalBounds
    is_no_trade: bool = False
    data_quality: DataQuality = DataQuality.INFERRED
    version: str = "1.0"


# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalSetup:
    """Setup validation result."""
    setup_id: str
    valid: bool
    quality: float
    temporal: TemporalBounds
    direction: Optional[Direction] = None
    setup_type: Optional[SetupType] = None
    checklist: dict[str, bool] = field(default_factory=dict)
    entry_price: Optional[Decimal] = None
    invalidation_price: Optional[Decimal] = None
    rr_ratio: Optional[float] = None
    data_quality: DataQuality = DataQuality.INFERRED
    version: str = "1.0"


# ─────────────────────────────────────────────
# RISK
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalRiskDecision:
    """Risk assessment for a potential trade."""
    risk_id: str
    approved: bool
    temporal: TemporalBounds
    rejection_reason: Optional[str] = None
    equity: Decimal = Decimal("0")
    risk_amount: Decimal = Decimal("0")
    stop_distance: Decimal = Decimal("0")
    position_size: Decimal = Decimal("0")
    stop_loss: Optional[Decimal] = None
    take_profit_1: Optional[Decimal] = None
    take_profit_2: Optional[Decimal] = None
    take_profit_3: Optional[Decimal] = None
    daily_loss_used: float = 0.0
    drawdown_current: float = 0.0
    open_positions: int = 0
    exposure_ratio: float = 0.0
    data_quality: DataQuality = DataQuality.INFERRED
    version: str = "1.0"


# ─────────────────────────────────────────────
# NO-TRADE
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalNoTradeCondition:
    """Single no-trade condition."""
    condition_name: str
    is_active: bool
    severity: NoTradeSeverity
    value: float
    threshold: float
    temporal: TemporalBounds
    version: str = "1.0"


@dataclass(frozen=True)
class CanonicalNoTradeFlags:
    """No-trade condition evaluation result."""
    flags_id: str
    conditions: dict[str, CanonicalNoTradeCondition]
    active_conditions: list[str]
    overall_severity: NoTradeSeverity
    position_size_factor: float
    signal_threshold_adjustment: float
    temporal: TemporalBounds
    data_quality: DataQuality = DataQuality.INFERRED
    version: str = "1.0"


# ─────────────────────────────────────────────
# DECISION
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalDecision:
    """Final trading decision."""
    decision_id: str
    decision: DecisionType
    decision_reasons: tuple[str, ...]
    price: Decimal
    session: SessionType
    regime: MarketRegime
    regime_confidence: float
    structure_score: float
    liquidity_score: float
    flow_score: float
    trend_score: float
    momentum_score: float
    volatility_score: float
    gsi_score: float
    p_long: float
    p_short: float
    p_no_trade: float
    probability_confidence: float
    setup_valid: bool
    setup_quality: float
    entry_trigger: Optional[str]
    rr_ratio: float
    position_size: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    no_trade_severity: NoTradeSeverity
    no_trade_conditions: tuple[str, ...]
    temporal: TemporalBounds
    execution_result: Optional[str] = None
    fill_price: Optional[Decimal] = None
    model_version: str = ""
    parameter_version: str = ""
    formula_version: str = ""
    data_quality: DataQuality = DataQuality.INFERRED
    version: str = "1.0"


# ─────────────────────────────────────────────
# ORDER
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class OrderRequest:
    """Order to be submitted."""
    order_id: str
    decision_id: str
    symbol: str
    order_type: OrderType
    side: OrderSide
    volume: Decimal
    price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    version: str = "1.0"


@dataclass(frozen=True)
class OrderResult:
    """Result of order submission."""
    result_id: str
    order_id: str
    status: OrderStatus
    temporal: TemporalBounds
    fill_price: Optional[Decimal] = None
    fill_volume: Optional[Decimal] = None
    slippage: Optional[Decimal] = None
    commission: Optional[Decimal] = None
    error_message: Optional[str] = None
    data_quality: DataQuality = DataQuality.OBSERVED
    version: str = "1.0"


# ─────────────────────────────────────────────
# POSITION
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalPosition:
    """Open position."""
    position_id: str
    trade_id: str
    symbol: str
    direction: Direction
    volume: Decimal
    entry_price: Decimal
    entry_time: datetime
    temporal: TemporalBounds
    current_sl: Optional[Decimal] = None
    current_tp1: Optional[Decimal] = None
    current_tp2: Optional[Decimal] = None
    current_tp3: Optional[Decimal] = None
    status: PositionStatus = PositionStatus.OPEN
    be_triggered: bool = False
    trailing_active: bool = False
    data_quality: DataQuality = DataQuality.OBSERVED
    version: str = "1.0"


# ─────────────────────────────────────────────
# TRADE
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class CanonicalTrade:
    """Completed trade record."""
    trade_id: str
    decision_id: str
    symbol: str
    direction: Direction
    entry_price: Decimal
    entry_time: datetime
    lots: Decimal
    temporal: TemporalBounds
    exit_price: Optional[Decimal] = None
    exit_time: Optional[datetime] = None
    exit_reason: Optional[ExitReason] = None
    contract_size: int = 100
    pnl: Optional[Decimal] = None
    pnl_pct: Optional[Decimal] = None
    r_multiple: Optional[float] = None
    tp1_hit: bool = False
    tp2_hit: bool = False
    tp3_hit: bool = False
    be_triggered: bool = False
    trailing_active: bool = False
    max_favorable_excursion: Decimal = Decimal("0")
    max_adverse_excursion: Decimal = Decimal("0")
    market_regime: Optional[MarketRegime] = None
    gsi_score: Optional[float] = None
    setup_quality: Optional[float] = None
    model_version: str = ""
    parameter_version: str = ""
    status: PositionStatus = PositionStatus.OPEN
    data_quality: DataQuality = DataQuality.OBSERVED
    version: str = "1.0"


# ─────────────────────────────────────────────
# ACCOUNT
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class AccountInfo:
    """Account state snapshot."""
    account_id: str
    balance: Decimal
    equity: Decimal
    margin: Decimal
    free_margin: Decimal
    temporal: TemporalBounds
    currency: str = "USD"
    leverage: int = 100
    data_quality: DataQuality = DataQuality.OBSERVED
    version: str = "1.0"
