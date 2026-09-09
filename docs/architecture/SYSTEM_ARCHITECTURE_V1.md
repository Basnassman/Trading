# SYSTEM ARCHITECTURE V1.0

## XAUUSD Quantitative Trading System
## Technical Architecture Specification

**Version:** 1.0.0
**Date:** 2026-08-31
**Status:** ARCHITECTURE DESIGN — PENDING REPOSITORY SCAFFOLDING
**Classification:** Pre-Implementation — Architecture Only

---

# 1. ARCHITECTURE OVERVIEW

## 1.1 Architectural Principles

| # | Principle | Description | Enforcement |
|---|-----------|-------------|-------------|
| P1 | Separation of Concerns | Each module has a single responsibility | Module boundaries |
| P2 | Deterministic Calculations | Same input → same output (where possible) | Immutability + versioning |
| P3 | Event-Driven Data Flow | Data flows through pipeline via events | Event bus architecture |
| P4 | Reproducibility | Any backtest can be re-run with same results | Version pinning |
| P5 | Testability | Every module independently testable | Interface contracts |
| P6 | Versioned Specifications | All formulas, features, models are versioned | Model version registry |
| P7 | Dependency Inversion | Modules depend on abstractions, not implementations | Provider interfaces |
| P8 | Source Abstraction | Trading logic never depends on specific data source | Adapter pattern |
| P9 | Fail-Safe Execution | Default to NO_TRADE on uncertainty | Fail-closed design |
| P10 | Temporal Correctness | Data used only after availability timestamp | Temporal enforcement |
| P11 | Auditability | Every decision is traceable to inputs | Audit trail |

## 1.2 System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                    XAUUSD TRADING SYSTEM                         │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ MT5      │  │ FRED API │  │ News     │  │ GC       │       │
│  │ (Broker) │  │ (Yields) │  │ Provider │  │ Futures  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │              │              │              │              │
│  ┌────▼──────────────▼──────────────▼──────────────▼─────┐      │
│  │              DATA INGESTION LAYER                      │      │
│  └────────────────────┬──────────────────────────────────┘      │
│                       │                                          │
│  ┌────────────────────▼──────────────────────────────────┐      │
│  │              FEATURE ENGINEERING LAYER                  │      │
│  └────────────────────┬──────────────────────────────────┘      │
│                       │                                          │
│  ┌────────────────────▼──────────────────────────────────┐      │
│  │              DECISION ENGINE LAYER                      │      │
│  └────────────────────┬──────────────────────────────────┘      │
│                       │                                          │
│  ┌────────────────────▼──────────────────────────────────┐      │
│  │              EXECUTION LAYER                            │      │
│  └────────────────────┬──────────────────────────────────┘      │
│                       │                                          │
│  ┌────────────────────▼──────────────────────────────────┐      │
│  │              PERSISTENCE & AUDIT LAYER                  │      │
│  └───────────────────────────────────────────────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

# 2. HIGH-LEVEL ARCHITECTURE

## 2.1 Data Flow Pipeline

```
DATA SOURCES
├── MT5 (OHLCV, Ticks, Spread, Account)
├── FRED API (Treasury Yields)
├── News Provider (Economic Events)
└── GC Futures (Gold Futures Volume — optional)

        ↓

DATA INGESTION LAYER
├── Market Data Ingestor
├── Macro Data Ingestor
├── News Data Ingestor
└── Futures Data Ingestor

        ↓

DATA VALIDATION LAYER
├── Schema Validation
├── Temporal Validation
├── Range Validation
├── Completeness Check
└── Freshness Check

        ↓

CANONICAL DATA LAYER
├── CanonicalBar
├── CanonicalTick
├── CanonicalNewsEvent
├── CanonicalMacroObservation
└── CanonicalSession

        ↓

FEATURE ENGINEERING LAYER
├── Market Structure Engine (Phase 2)
├── Liquidity Engine (Phase 3)
├── Flow Engine (Phase 4) — Institutional Flow Proxy
├── Trend Engine (Phase 5)
├── Momentum Engine (Phase 5)
├── Volatility Engine (Phase 5)
├── News/Macro Engine (Phase 7)
├── Historical Similarity Engine (Phase 8)
├── Regime Detection Engine (Phase 9)
└── Feature Store

        ↓

EVIDENCE & PROBABILITY LAYER
├── Evidence Family Aggregator (Phase 10)
├── GSI Calculator (Phase 6) — Diagnostic only
├── Probability Engine (Phase 10)
└── Calibration Manager

        ↓

DECISION LAYER
├── Setup Engine (Phase 11)
├── Risk Engine (Phase 12)
├── No-Trade Condition Evaluator (Phase 14)
├── Trade Management Engine (Phase 13)
└── Decision Engine (Phase 15) — SOLE decision maker

        ↓

EXECUTION LAYER
├── Execution Interface (abstract)
├── MT5 Execution Adapter
├── Paper Execution Adapter
└── Backtest Execution Adapter

        ↓

PERSISTENCE & AUDIT LAYER
├── Trade Database (PostgreSQL)
├── Feature Store (PostgreSQL)
├── Audit Trail (PostgreSQL)
├── Model Version Registry
└── Parameter Registry

        ↓

FEEDBACK & RESEARCH LAYER
├── Performance Analyzer (Phase 21)
├── Weakness Detector
├── Parameter Stability Monitor
└── Research Pipeline
```

---

# 3. MODULE BOUNDARIES

## 3.1 Module Definitions

| Module | Type | Responsibility | Dependencies |
|--------|------|---------------|-------------|
| `data_ingestion` | Library | Fetch data from providers | Provider interfaces |
| `data_validation` | Library | Validate data quality | Canonical data model |
| `canonical_data` | Library | Data representations | None (foundation) |
| `market_data` | Library | OHLCV, Tick, Spread processing | canonical_data |
| `macro_data` | Library | DXY, Yields, FFR processing | canonical_data |
| `news_data` | Library | News events, surprises | canonical_data |
| `feature_engine` | Library | Feature computation pipeline | canonical_data |
| `market_structure` | Library | Swing points, BOS, MSS | market_data |
| `liquidity` | Library | Liquidity levels, sweeps | market_structure |
| `flow` | Library | Institutional Flow Proxy | market_data, liquidity |
| `trend` | Library | Trend scoring | market_data |
| `momentum` | Library | Momentum scoring | market_data |
| `volatility` | Library | Volatility scoring | market_data |
| `gsi` | Library | Gold Smart Index | trend, momentum, volatility, flow |
| `historical` | Library | Historical similarity | feature_engine |
| `regime` | Library | Regime detection | market_structure, liquidity, flow, trend, momentum, volatility |
| `evidence` | Library | Evidence family aggregation | All feature engines |
| `probability` | Library | Bayesian probability + calibration | evidence |
| `setup` | Library | Setup validation | probability, market_structure, liquidity, flow, regime |
| `risk` | Library | Position sizing, SL/TP | setup, market_structure, liquidity, regime |
| `no_trade` | Library | No-trade condition evaluation | risk, flow, regime, news_data |
| `decision` | Library | Final decision generation | setup, risk, no_trade, probability |
| `execution` | Library + Adapter | Order execution interface | Execution adapters |
| `trade_management` | Library | Position management | execution, market_structure, liquidity |
| `portfolio` | Library | Multi-position management | trade_management |
| `backtest` | Library | Historical simulation | All engines (same logic) |
| `paper_trading` | Library | Paper trading simulation | All engines + paper adapter |
| `monitoring` | Service | Health, metrics, alerts | All modules |
| `research` | Library | Performance analysis | portfolio, feature_engine |
| `audit` | Library | Audit trail recording | All modules |

## 3.2 Module Type Justification

| Module | Type | Justification |
|--------|------|---------------|
| `data_ingestion` | Library | No background processing needed; called by pipeline |
| `data_validation` | Library | Stateless validation functions |
| `canonical_data` | Library | Pure data classes; no behavior |
| `market_structure` through `regime` | Library | Pure computation; no I/O |
| `evidence` | Library | Aggregation logic only |
| `probability` | Library | Bayesian computation + calibration |
| `setup` through `decision` | Library | Decision logic only |
| `execution` | Library + Adapter | Abstract interface + concrete adapters |
| `trade_management` | Library | Position management logic |
| `portfolio` | Library | Portfolio-level logic |
| `backtest` | Library | Simulation engine |
| `paper_trading` | Library | Paper execution simulation |
| `monitoring` | Service | Background health checks + alerting |
| `research` | Library | Post-hoc analysis |
| `audit` | Library | Audit trail recording |

**Decision:** All modules are **Libraries** except `monitoring` (Service). No microservices. No message queues. Simple synchronous processing pipeline.

---

# 4. DATA CONTRACTS

## 4.1 Contract Structure

Every data contract between modules follows this structure:

```python
@dataclass(frozen=True)
class DataContract:
    """Base for all data contracts."""
    # Identity
    contract_id: str                    # Unique identifier
    version: str                        # Contract version
    
    # Temporal
    event_time: datetime                # When the event occurred
    availability_time: datetime         # When data became available
    ingestion_time: datetime            # When system received it
    
    # Quality
    data_quality: str                   # "observed" / "inferred" / "unavailable"
    confidence: float                   # [0, 1]
    source: str                         # Data source identifier
    
    # Metadata
    precision: int                      # Decimal places
    units: str                          # "pips", "%", "index", etc.
    missing_state: str | None           # "complete" / "partial" / "imputed"
```

## 4.2 Key Contracts

### CanonicalBar

```python
@dataclass(frozen=True)
class CanonicalBar:
    """Standardized OHLCV bar."""
    # Identity
    bar_id: str
    symbol: str                         # "XAUUSD"
    timeframe: str                      # "M5", "H1", "D1", etc.
    
    # OHLCV
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    tick_volume: int
    real_volume: int | None
    
    # Temporal
    bar_time: datetime                  # Bar open time (UTC)
    bar_close_time: datetime            # Bar close time (UTC)
    availability_time: datetime         # bar_close_time + confirmation delay
    ingestion_time: datetime
    
    # Quality
    data_quality: str
    is_confirmed: bool                  # Whether bar is finalized
    
    # Spread
    spread_at_close: Decimal | None
    
    # Metadata
    version: str
```

### CanonicalTick

```python
@dataclass(frozen=True)
class CanonicalTick:
    """Single tick data point."""
    tick_id: str
    symbol: str
    
    bid: Decimal
    ask: Decimal
    spread: Decimal                     # ask - bid
    volume: int | None
    
    timestamp: datetime                 # Tick time (UTC)
    ingestion_time: datetime
    
    data_quality: str
    version: str
```

### CanonicalNewsEvent

```python
@dataclass(frozen=True)
class CanonicalNewsEvent:
    """Economic news event."""
    event_id: str
    name: str
    currency: str
    category: str                       # "CPI", "NFP", "FOMC", etc.
    importance: int                     # 1-4
    
    # Timing
    release_time: datetime              # Scheduled release (UTC)
    actual_release_time: datetime | None  # Actual release (if different)
    availability_time: datetime         # = actual_release_time
    
    # Values
    actual: Decimal | None
    forecast: Decimal | None
    previous: Decimal | None
    previous_revised: Decimal | None
    revision: Decimal | None
    revision_time: datetime | None
    revision_availability_time: datetime | None
    
    # Metadata
    unit: str
    source: str
    ingestion_time: datetime
    
    data_quality: str
    version: str
```

### CanonicalMacroObservation

```python
@dataclass(frozen=True)
class CanonicalMacroObservation:
    """Macro data point (DXY, Yield, FFR)."""
    observation_id: str
    indicator: str                      # "DXY", "US_2Y_YIELD", "US_10Y_YIELD", "FFR"
    
    value: Decimal
    observation_date: datetime          # When data was published
    availability_time: datetime         # When system can use it
    ingestion_time: datetime
    
    source: str                         # "primary", "secondary", "fallback"
    data_quality: str
    freshness_seconds: float            # Age at ingestion
    
    version: str
```

### CanonicalSession

```python
@dataclass(frozen=True)
class CanonicalSession:
    """Trading session definition."""
    session_id: str
    name: str                           # "asian", "london", "newyork"
    
    open_time_local: time               # Session open (local time)
    close_time_local: time              # Session close (local time)
    timezone: str                       # IANA timezone
    
    open_time_utc: datetime             # Computed UTC open
    close_time_utc: datetime            # Computed UTC close
    dst_active: bool                    # DST state for this date
    
    date: date                          # Which date this session applies to
    
    version: str
```

### CanonicalSwing

```python
@dataclass(frozen=True)
class CanonicalSwing:
    """Swing point (high or low)."""
    swing_id: str
    symbol: str
    timeframe: str
    
    swing_type: str                     # "high" or "low"
    price: Decimal
    bar_time: datetime                  # Bar where swing occurred
    confirmation_time: datetime         # When swing was confirmed (bar_time + k bars)
    is_confirmed: bool
    
    strength: float                     # [0, 1]
    
    version: str
```

### CanonicalLiquidityLevel

```python
@dataclass(frozen=True)
class CanonicalLiquidityLevel:
    """Liquidity level."""
    level_id: str
    level_type: str                     # "pdh", "pdl", "swing_high", "eqh", etc.
    
    price: Decimal
    strength: float                     # [0, 100]
    formation_time: datetime
    availability_time: datetime
    
    touch_count: int
    last_test_time: datetime | None
    
    version: str
```

### CanonicalFlowObservation

```python
@dataclass(frozen=True)
class CanonicalFlowObservation:
    """Institutional Flow Proxy observation."""
    observation_id: str
    symbol: str
    timeframe: str
    
    # Features
    rvol: float
    buying_pressure: float
    selling_pressure: float
    candle_efficiency: float
    volume_acceleration: float
    mv_relationship: str
    
    # Proxy
    ifp_score: float                    # [-100, +100]
    ifp_direction: str                  # "bullish", "bearish", "neutral"
    
    # Quality
    data_quality: str                   # "observed", "inferred", "unavailable"
    confidence: float                   # [0, 1]
    volume_source: str
    
    bar_time: datetime
    availability_time: datetime
    ingestion_time: datetime
    
    version: str
```

### CanonicalEvidence

```python
@dataclass(frozen=True)
class CanonicalEvidence:
    """Evidence from a single family."""
    evidence_id: str
    family_name: str                    # "structure", "liquidity", "flow", etc.
    
    family_score: float                 # [-100, +100]
    members: dict[str, float]           # Member scores within family
    
    direction: str                      # "bullish", "bearish", "neutral"
    confidence: float                   # [0, 1]
    
    bar_time: datetime
    availability_time: datetime
    
    version: str
```

### CanonicalSignal

```python
@dataclass(frozen=True)
class CanonicalSignal:
    """Trading signal (pre-decision)."""
    signal_id: str
    symbol: str
    
    direction: str                      # "long", "short"
    confidence: float                   # P(action)
    
    entry_price: Decimal
    stop_loss: Decimal
    take_profit_1: Decimal
    take_profit_2: Decimal
    take_profit_3: Decimal
    
    position_size: Decimal
    risk_amount: Decimal
    rr_ratio: float
    
    # Context
    setup_quality: float
    gsi_score: float
    regime: str
    
    bar_time: datetime
    availability_time: datetime
    
    version: str
```

### CanonicalDecision

```python
@dataclass(frozen=True)
class CanonicalDecision:
    """Final trading decision."""
    decision_id: str
    symbol: str
    
    decision: str                       # "long", "short", "no_trade"
    decision_reasons: list[str]
    
    # Full context snapshot
    price: Decimal
    session: str
    regime: str
    regime_confidence: float
    
    # All engine outputs
    structure_score: float
    liquidity_score: float
    flow_score: float
    trend_score: float
    momentum_score: float
    volatility_score: float
    gsi_score: float
    
    # Probability
    p_long: float
    p_short: float
    p_no_trade: float
    probability_confidence: float
    
    # Setup
    setup_valid: bool
    setup_quality: float
    entry_trigger: str | None
    rr_ratio: float
    
    # Risk
    position_size: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    
    # No-Trade
    no_trade_severity: int
    no_trade_conditions: list[str]
    
    # Execution
    execution_result: str | None        # "filled", "rejected", "timeout"
    fill_price: Decimal | None
    
    # Versions
    model_version: str
    parameter_version: str
    formula_version: str
    
    bar_time: datetime
    decision_time: datetime
    
    version: str
```

### CanonicalTrade

```python
@dataclass(frozen=True)
class CanonicalTrade:
    """Completed trade record."""
    trade_id: str
    decision_id: str                    # Link to decision
    
    symbol: str
    direction: str
    
    # Entry
    entry_price: Decimal
    entry_time: datetime
    
    # Exit
    exit_price: Decimal | None
    exit_time: datetime | None
    exit_reason: str | None
    
    # Position
    lots: Decimal
    contract_size: int
    
    # P&L
    pnl: Decimal | None
    pnl_pct: Decimal | None
    r_multiple: float | None
    
    # Management
    tp1_hit: bool
    tp2_hit: bool
    tp3_hit: bool
    be_triggered: bool
    trailing_active: bool
    
    # Outcome
    max_favorable_excursion: Decimal
    max_adverse_excursion: Decimal
    
    # Context (snapshot at entry)
    market_regime: str
    gsi_score: float
    setup_quality: float
    
    # Versions
    model_version: str
    parameter_version: str
    
    # Status
    status: str                         # "open", "closed", "cancelled"
    
    version: str
```

---

# 5. CANONICAL DATA MODEL

## 5.1 Entity Relationships

```
CanonicalBar ──→ 1:N ──→ CanonicalSwing
CanonicalBar ──→ 1:1 ──→ CanonicalFlowObservation
CanonicalBar ──→ 1:1 ──→ CanonicalEvidence (per family)
CanonicalBar ──→ 1:1 ──→ CanonicalGSI
CanonicalBar ──→ 1:1 ──→ CanonicalProbability
CanonicalBar ──→ 1:0..1 → CanonicalDecision
CanonicalDecision ──→ 1:1 ──→ CanonicalOrder
CanonicalOrder ──→ 1:0..1 → CanonicalTrade
CanonicalTrade ──→ 1:N ──→ CanonicalTradeEvent (partial closes, trailing updates)

CanonicalNewsEvent ──→ 1:N ──→ CanonicalNewsRevision
CanonicalMacroObservation ──→ 1:1 ──→ CanonicalBar (forward-filled)

CanonicalLiquidityLevel ──→ 1:N ──→ CanonicalSweep
CanonicalSession ──→ N:1 ──→ CanonicalBar (session classification)
```

## 5.2 ID Generation

| Entity | ID Format | Example |
|--------|-----------|---------|
| Bar | `{symbol}_{timeframe}_{bar_time_iso}` | `XAUUSD_M5_2026-08-31T14:30:00Z` |
| Tick | `{symbol}_{timestamp_iso}_{sequence}` | `XAUUSD_2026-08-31T14:30:00.123Z_001` |
| Swing | `{symbol}_{timeframe}_{bar_time}_{type}` | `XAUUSD_M5_2026-08-31T14:30:00Z_high` |
| Decision | `dec_{timestamp_iso}_{uuid4_short}` | `dec_2026-08-31T14:30:00Z_a1b2c3` |
| Trade | `trd_{decision_id}` | `trd_dec_2026-08-31T14:30:00Z_a1b2c3` |

---

# 6. TEMPORAL DATA ARCHITECTURE

## 6.1 Three Timestamps

Every observation has three timestamps:

| Timestamp | Definition | Purpose |
|-----------|-----------|---------|
| `event_time` | When the event occurred in the market | Causal ordering |
| `availability_time` | When the system can legitimately consume the data | Temporal correctness |
| `ingestion_time` | When our infrastructure received the data | Freshness monitoring |

## 6.2 Availability Rules

| Data Type | event_time | availability_time | Notes |
|-----------|-----------|-------------------|-------|
| OHLCV Bar | bar_open_time | bar_close_time + confirm_delay | Bar must be confirmed |
| Tick | tick_timestamp | tick_timestamp | Real-time |
| News Actual | release_time | release_time | **Never before** |
| News Forecast | publication_time | publication_time | Known in advance |
| News Revision | revision_time | revision_time | **Never before** |
| DXY (Primary) | publication_time | publication_time | Forward-fill |
| DXY (Secondary) | observation_date | observation_date + eod_delay | Daily |
| Yield | observation_date | publication_time (~16:00 ET) | Daily |
| Swing Point | bar_time | bar_time + k × bar_duration | k-bar confirmation |
| Sweep | penetration_time | penetration_time + n × bar_duration | n-bar return window |
| Regime | bar_time | bar_time + 5 × bar_duration | 5-bar confirmation |

## 6.3 Temporal Enforcement

```python
class TemporalEnforcer:
    """Ensures data is only used after availability_time."""
    
    def is_available(self, observation, current_time):
        """Check if observation is available at current_time."""
        return observation.availability_time <= current_time
    
    def get_available_data(self, observations, current_time):
        """Filter observations to only those available at current_time."""
        return [o for o in observations if self.is_available(o, current_time)]
```

## 6.4 Late Data Handling

| Scenario | Handling |
|----------|----------|
| Data arrives after availability_time | Process normally; log delay |
| Data arrives before availability_time | Queue until availability_time |
| Data never arrives | Flag as missing; use last known value with staleness flag |

## 6.5 Revision Handling

```python
class RevisionHandler:
    """Handles data revisions (e.g., news revisions)."""
    
    def process_revision(self, original, revision):
        """Process a revision to previously published data."""
        # Store revision as separate record
        # Do NOT overwrite original
        # Update availability for revised value
        return RevisionRecord(
            original_id=original.id,
            revision_value=revision.value,
            revision_time=revision.time,
            availability_time=revision.time  # Available only after revision
        )
```

## 6.6 Duplicate Data Handling

```python
class DeduplicationHandler:
    """Handles duplicate data points."""
    
    def is_duplicate(self, existing, new):
        """Check if new data is a duplicate of existing."""
        return (existing.event_time == new.event_time and
                existing.source == new.source)
    
    def resolve(self, existing, new):
        """Resolve duplicate: keep newer ingestion, log conflict."""
        if new.ingestion_time > existing.ingestion_time:
            return new  # Newer ingestion wins
        return existing
```

## 6.7 Out-of-Order Data

```python
class OutOfOrderHandler:
    """Handles data arriving out of chronological order."""
    
    def __init__(self, buffer_size=100):
        self.buffer = []
        self.buffer_size = buffer_size
    
    def ingest(self, observation):
        """Buffer and reorder observations."""
        self.buffer.append(observation)
        self.buffer.sort(key=lambda o: o.event_time)
        
        # Emit observations that are now in order
        ready = []
        while self.buffer and self._can_emit(self.buffer[0]):
            ready.append(self.buffer.pop(0))
        
        return ready
    
    def _can_emit(self, observation):
        """Check if observation can be emitted (no earlier data pending)."""
        return True  # Simplified; actual impl checks buffer
```

---

# 7. DATA SOURCE ABSTRACTION

## 7.1 Provider Interfaces

### MarketDataProvider

```python
class MarketDataProvider(ABC):
    """Abstract interface for market data."""
    
    @abstractmethod
    def get_bars(self, symbol, timeframe, start, end) -> list[CanonicalBar]:
        """Fetch historical bars."""
        pass
    
    @abstractmethod
    def get_ticks(self, symbol, start, end) -> list[CanonicalTick]:
        """Fetch tick data."""
        pass
    
    @abstractmethod
    def get_spread(self, symbol, timestamp) -> Decimal:
        """Get current spread."""
        pass
    
    @abstractmethod
    def get_account_info(self) -> AccountInfo:
        """Get account balance, equity, etc."""
        pass
    
    @abstractmethod
    def subscribe_bars(self, symbol, timeframe, callback):
        """Subscribe to real-time bar updates."""
        pass
    
    @abstractmethod
    def subscribe_ticks(self, symbol, callback):
        """Subscribe to real-time tick updates."""
        pass
```

### NewsProvider

```python
class NewsProvider(ABC):
    """Abstract interface for news data."""
    
    @abstractmethod
    def get_events(self, start, end, currencies=None) -> list[CanonicalNewsEvent]:
        """Fetch economic events."""
        pass
    
    @abstractmethod
    def get_upcoming_events(self, hours_ahead=24) -> list[CanonicalNewsEvent]:
        """Fetch upcoming events."""
        pass
    
    @abstractmethod
    def subscribe_events(self, callback):
        """Subscribe to real-time event updates."""
        pass
```

### MacroProvider

```python
class MacroProvider(ABC):
    """Abstract interface for macro data."""
    
    @abstractmethod
    def get_indicator(self, indicator, start, end) -> list[CanonicalMacroObservation]:
        """Fetch macro indicator values."""
        pass
    
    @abstractmethod
    def get_latest(self, indicator) -> CanonicalMacroObservation:
        """Get latest value for indicator."""
        pass
```

### ExecutionProvider

```python
class ExecutionProvider(ABC):
    """Abstract interface for order execution."""
    
    @abstractmethod
    def send_order(self, order: OrderRequest) -> OrderResult:
        """Send an order."""
        pass
    
    @abstractmethod
    def modify_position(self, position_id, sl=None, tp=None) -> bool:
        """Modify SL/TP of existing position."""
        pass
    
    @abstractmethod
    def close_position(self, position_id) -> OrderResult:
        """Close a position."""
        pass
    
    @abstractmethod
    def get_positions(self) -> list[Position]:
        """Get all open positions."""
        pass
    
    @abstractmethod
    def get_account(self) -> AccountInfo:
        """Get account info."""
        pass
```

## 7.2 Concrete Implementations

| Interface | MT5 | Paper | Backtest |
|-----------|-----|-------|----------|
| MarketDataProvider | MT5MarketProvider | PaperMarketProvider | BacktestMarketProvider |
| NewsProvider | MT5NewsProvider | PaperNewsProvider | BacktestNewsProvider |
| MacroProvider | MT5MacroProvider | PaperMacroProvider | BacktestMacroProvider |
| ExecutionProvider | MT5ExecutionProvider | PaperExecutionProvider | BacktestExecutionProvider |

**Key:** Trading logic (Phase 2-15) depends ONLY on abstract interfaces. Concrete providers are injected at runtime.

---

# 8. XAUUSD + GOLD FUTURES ARCHITECTURE

## 8.1 Instrument Model

```
Instrument: XAUUSD
├── Primary Source: MT5 (Spot Gold)
├── Secondary Source: GC Futures (if available)
└── Relationship: Independent markets; correlated but not identical
```

## 8.2 Separation

| Concept | Definition | Example |
|---------|-----------|---------|
| **Instrument** | What we trade | XAUUSD |
| **Source** | Where we get data | MT5, GC Futures |
| **Market** | The actual market | Spot Gold, COMEX Futures |

**Rule:** Never assume XAUUSD spot price = GC futures price. They are related but distinct.

## 8.3 GC Futures as Reference

```
IF GC Futures Available:
    GC_Volume = GC_Futures_Volume
    GC_Correlation = Corr(IFP_Score, GC_Direction, window=20)
    
    IF GC_Correlation > 0.5:
        IFP_Confidence += 0.10
        Log("IFP validated by GC futures")
    
ELSE:
    GC_Volume = None
    GC_Correlation = None
    Log("GC futures not available; IFP proceeds without validation")
```

## 8.4 Volume Source Hierarchy

| Priority | Source | Label | Confidence |
|----------|--------|-------|-----------|
| 1 | Exchange Volume (GC) | "exchange" | 0.90 |
| 2 | Broker Real Volume | "broker_real" | 0.80 |
| 3 | Composite (weighted) | "composite" | 0.70 |
| 4 | Tick Volume | "tick_proxy" | 0.50 |
| 5 | None | "none" | 0.00 |

---

# 9. FEATURE STORE

## 9.1 Feature Record

```python
@dataclass(frozen=True)
class FeatureRecord:
    """Single feature value with full metadata."""
    feature_id: str
    feature_name: str                   # "structure_score", "gsi", etc.
    
    value: float
    bar_time: datetime                  # Which bar this feature belongs to
    availability_time: datetime         # When feature became available
    computation_time: datetime          # When feature was computed
    
    source: str                         # Which engine computed it
    formula_version: str                # Version of formula used
    
    quality: str                        # "computed", "imputed", "unavailable"
    confidence: float                   # [0, 1]
    
    # Input trace
    input_features: list[str]           # Features that inputs to this one
    input_data: list[str]               # Raw data that inputs to this one
```

## 9.2 Feature Registry

| Feature Name | Source Engine | Formula Version | Dependencies |
|-------------|---------------|----------------|-------------|
| `structure_score` | market_structure | v1.0 | OHLCV |
| `structure_state` | market_structure | v1.0 | structure_score |
| `swing_highs` | market_structure | v1.0 | OHLCV |
| `swing_lows` | market_structure | v1.0 | OHLCV |
| `bos_detected` | market_structure | v1.0 | swing_highs, swing_lows |
| `liquidity_score` | liquidity | v1.0 | swing_highs, swing_lows, OHLCV |
| `liquidity_levels` | liquidity | v1.0 | OHLCV, sessions |
| `sweep_detected` | liquidity | v1.0 | liquidity_levels, OHLCV |
| `ifp_score` | flow | v1.0 | OHLCV, volume |
| `flow_state` | flow | v1.0 | ifp_score |
| `trend_score` | trend | v1.0 | OHLCV |
| `momentum_score` | momentum | v1.0 | OHLCV |
| `volatility_score` | volatility | v1.0 | OHLCV |
| `atr` | volatility | v1.0 | OHLCV |
| `gsi` | gsi | v1.0 | structure_score, flow_score, trend_score, momentum_score, volatility_score |
| `news_score` | news_macro | v1.0 | news_events |
| `macro_score` | news_macro | v1.0 | dxy, yields, ffr |
| `historical_p_long` | historical | v1.0 | feature_vector |
| `regime` | regime | v1.0 | structure, liquidity, flow, trend, volatility |
| `regime_confidence` | regime | v1.0 | regime |

---

# 10. FEATURE LINEAGE

## 10.1 Lineage Graph

```
RAW DATA
├── OHLCV (MT5)
├── Tick Data (MT5)
├── News Events (NewsProvider)
├── DXY (MacroProvider)
├── Yields (MacroProvider)
├── FFR (MacroProvider)
├── GC Volume (MT5 — optional)
└── Sessions (Configuration)

        ↓

LEVEL 1 FEATURES
├── RVOL ← OHLCV, Volume
├── BP/SP ← OHLCV, Volume
├── CE ← OHLCV
├── VA ← Volume
├── ATR ← OHLCV
├── EMA_20 ← OHLCV
├── EMA_50 ← OHLCV
├── RSI ← OHLCV
├── MACD ← OHLCV
└── ADX ← OHLCV

        ↓

LEVEL 2 FEATURES
├── Structure Score ← Swing Points, BOS, CHoCH
├── Liquidity Score ← Liquidity Levels, Clusters
├── IFP Score ← RVOL, BP, SP, CE, VA, MV
├── Trend Score ← EMA_20, EMA_50, ADX
├── Momentum Score ← RSI, MACD
├── Volatility Score ← ATR, Bollinger
├── News Score ← News Events, Surprises
├── Macro Score ← DXY, Yields, FFR
├── Historical Probability ← Feature Vector, KNN
└── Regime ← Structure, Liquidity, Flow, Trend, Volatility

        ↓

LEVEL 3 FEATURES
├── GSI ← Structure, Flow, Trend, Momentum, PA, Volatility (DIAGNOSTIC ONLY)
├── Evidence Families ← Structure, Liquidity, Flow, Trend/Mom, Macro, Historical, Volatility, Context
└── Probability ← Evidence Families (NOT GSI)

        ↓

DECISION
├── Setup ← Probability, Structure, Liquidity, Flow, Regime
├── Risk ← Setup, Structure, Liquidity, Regime
├── No-Trade Flags ← Risk, Flow, Regime, News
└── Decision ← Setup, Risk, No-Trade Flags
```

## 10.2 Lineage Rules

| Rule | Description |
|------|-------------|
| L1 | Every feature must have a documented lineage |
| L2 | Lineage is immutable once recorded |
| L3 | GSI is derived from Level 2 features but is NOT an input to Probability |
| L4 | Evidence Families are the SOLE input to Probability |
| L5 | If a feature is missing, its lineage is flagged as "imputed" |

---

# 11. MODEL VERSIONING

## 11.1 Version Types

| Entity | Version Format | Example |
|--------|---------------|---------|
| Formula | `v{major}.{minor}` | `v1.0`, `v1.1`, `v2.0` |
| Feature Schema | `v{major}.{minor}` | `v1.0` |
| GSI | `v{major}.{minor}` | `v1.0` |
| Probability Model | `v{major}.{minor}` | `v1.0` |
| Calibration | `v{major}.{minor}.{patch}` | `v1.0.0` |
| Parameters | `v{major}.{minor}.{patch}` | `v1.0.0` |
| Strategy | `v{major}.{minor}` | `v1.0` |
| Risk Model | `v{major}.{minor}` | `v1.0` |

## 11.2 Version Registry

```python
@dataclass(frozen=True)
class ModelVersion:
    """Record of a model/formula version."""
    entity_type: str                    # "formula", "gsi", "probability", etc.
    entity_name: str                    # "gsi_v1", "bayesian_v1"
    version: str                        # "1.0.0"
    
    # What changed
    description: str
    changes: list[str]
    
    # When
    created_at: datetime
    deprecated_at: datetime | None
    
    # Who
    author: str                         # "buffy" or "human"
    
    # Reproducibility
    code_commit: str | None             # Git commit hash
    spec_version: str                   # Which spec version this implements
```

## 11.3 Trade → Version Link

Every trade must record:

```python
trade.model_version = "gsi_v1.0"
trade.formula_version = "probability_v1.0"
trade.parameter_version = "params_v1.0.0"
trade.spec_version = "SYSTEM_SPECIFICATION_V1.md"
```

**Purpose:** Given a trade, we can reconstruct exactly which formulas, parameters, and models produced it.

---

# 12. CONFIGURATION

## 12.1 Configuration Categories

| Category | Description | Mutability |
|----------|-------------|-----------|
| **Fixed** | Instrument, timeframes, timezone | Immutable |
| **Initial** | Phase 17 optimization targets | Mutable with versioning |
| **Research** | Testing parameters | Mutable, not used in live |
| **Risk Limits** | Max DD, daily loss, etc. | Mutable with approval |
| **Execution** | Slippage, spread thresholds | Mutable with versioning |

## 12.2 Configuration Schema

```python
@dataclass(frozen=True)
class SystemConfig:
    """Complete system configuration."""
    # Fixed
    instrument: str = "XAUUSD"
    primary_timeframe: str = "M5"
    analysis_timeframes: list[str] = field(default_factory=lambda: ["D1", "H4", "H1", "M15", "M5"])
    timezone: str = "UTC"
    
    # Initial Parameters
    params: dict[str, float] = field(default_factory=dict)
    
    # Risk Limits
    risk_per_trade: float = 0.01
    max_daily_loss: float = 0.05
    max_drawdown: float = 0.20
    max_positions: int = 5
    max_exposure: float = 0.50
    
    # Versioning
    config_version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
```

## 12.3 Parameter Logging

Every parameter change is logged:

```python
@dataclass(frozen=True)
class ParameterChange:
    """Record of a parameter change."""
    parameter_name: str
    old_value: float
    new_value: float
    reason: str
    approved_by: str
    timestamp: datetime
    version_before: str
    version_after: str
```

---

# 13. DATABASE LOGICAL ARCHITECTURE

## 13.1 Entity Groups

### Market Data

| Entity | Description | Key Fields |
|--------|-------------|-----------|
| `market_bars` | OHLCV bars | bar_id, symbol, timeframe, ohlcv, bar_time |
| `ticks` | Tick data | tick_id, symbol, bid, ask, volume, timestamp |
| `spreads` | Spread observations | spread_id, symbol, spread, timestamp |

### Reference Data

| Entity | Description | Key Fields |
|--------|-------------|-----------|
| `sessions` | Trading sessions | session_id, name, open_utc, close_utc, dst |
| `news_events` | Economic events | event_id, name, importance, release_time |
| `news_revisions` | Event revisions | revision_id, event_id, revised_value, revision_time |
| `macro_observations` | Macro data points | observation_id, indicator, value, observation_date |

### Features

| Entity | Description | Key Fields |
|--------|-------------|-----------|
| `swings` | Swing points | swing_id, type, price, bar_time, confirmation_time |
| `liquidity_levels` | Liquidity levels | level_id, type, price, strength |
| `flow_observations` | IFP observations | observation_id, ifp_score, data_quality |
| `evidence` | Evidence families | evidence_id, family_name, family_score |
| `gsi_observations` | GSI values | gsi_id, gsi_score, direction |
| `historical_matches` | KNN matches | match_id, feature_vector, neighbors |
| `probability_predictions` | Probability outputs | prediction_id, p_long, p_short, p_no_trade |
| `regime_observations` | Regime states | regime_id, regime_type, confidence |

### Decisions

| Entity | Description | Key Fields |
|--------|-------------|-----------|
| `setups` | Setup validation | setup_id, valid, quality, direction |
| `risk_decisions` | Risk assessment | risk_id, position_size, sl, tp, approved |
| `no_trade_flags` | No-trade conditions | flag_id, conditions, severity |
| `decisions` | Final decisions | decision_id, decision, reasons |
| `orders` | Order records | order_id, type, price, status |
| `positions` | Open positions | position_id, entry, sl, tp, pnl |
| `trades` | Completed trades | trade_id, entry, exit, pnl, duration |

### System

| Entity | Description | Key Fields |
|--------|-------------|-----------|
| `model_versions` | Model registry | entity_type, version, description |
| `parameter_versions` | Parameter registry | version, parameters_json |
| `data_quality` | Quality tracking | source, completeness, timeliness |
| `audit_events` | Audit trail | event_type, decision_id, snapshot |

---

# 14. EVENT PROCESSING

## 14.1 Processing Model

**Decision:** Synchronous, sequential processing pipeline.

**Rationale:**
- Simplicity: Easier to debug, test, and maintain
- Determinism: Same input order → same output order
- Reliability: No message queue failures
- Replayability: Can replay historical data deterministically

**Trade-off:** Lower throughput than async. Acceptable because:
- M5 timeframe = 288 bars/day
- Processing time per bar << 5 minutes
- No need for sub-second latency on M5

## 14.2 Pipeline Architecture

```python
class TradingPipeline:
    """Synchronous trading pipeline."""
    
    def __init__(self, config, providers):
        self.config = config
        self.providers = providers
        self.feature_store = FeatureStore()
        self.audit_trail = AuditTrail()
    
    def process_bar(self, bar: CanonicalBar) -> CanonicalDecision | None:
        """Process a single bar through the entire pipeline."""
        
        # 1. Validate
        validated_bar = self.validate(bar)
        if not validated_bar:
            return None
        
        # 2. Feature Engineering
        features = self.compute_features(validated_bar)
        self.feature_store.store(features)
        
        # 3. Evidence
        evidence = self.compute_evidence(features)
        
        # 4. Probability
        probability = self.compute_probability(evidence)
        
        # 5. GSI (diagnostic)
        gsi = self.compute_gsi(features)
        
        # 6. Setup
        setup = self.evaluate_setup(probability, features)
        
        # 7. Risk
        risk = self.evaluate_risk(setup, features)
        
        # 8. No-Trade
        no_trade = self.evaluate_no_trade(features, risk)
        
        # 9. Decision (SOLE decision maker)
        decision = self.make_decision(setup, risk, no_trade, probability, gsi)
        
        # 10. Audit
        self.audit_trail.record(decision, features, evidence, probability, gsi)
        
        return decision
```

## 14.3 Idempotency

Each bar is processed exactly once. The pipeline checks:

```python
if self.feature_store.has_features(bar.bar_id):
    return self.feature_store.get_features(bar.bar_id)
```

## 14.4 Replayability

The pipeline can replay historical data:

```python
for bar in historical_bars:
    decision = pipeline.process_bar(bar)
    if decision and decision.decision != "no_trade":
        execution.simulate(decision)
```

---

# 15. BACKTEST ARCHITECTURE

## 15.1 Core Principle

**Same Strategy Logic + Different Data Adapter = Backtest**

```python
class BacktestEngine:
    """Backtest using the same pipeline as live."""
    
    def __init__(self, config, historical_data):
        self.config = config
        self.pipeline = TradingPipeline(
            config=config,
            providers={
                'market': BacktestMarketProvider(historical_data),
                'news': BacktestNewsProvider(historical_data),
                'macro': BacktestMacroProvider(historical_data),
                'execution': BacktestExecutionProvider()
            }
        )
    
    def run(self, start_date, end_date):
        """Run backtest over date range."""
        for bar in self.get_bars(start_date, end_date):
            decision = self.pipeline.process_bar(bar)
            if decision and decision.decision != "no_trade":
                self.pipeline.providers['execution'].execute(decision)
```

## 15.2 No Backtest-Only Logic

**Rule:** There must be NO code paths that exist only in backtest and not in live.

| Allowed | Not Allowed |
|---------|-------------|
| BacktestExecutionProvider (simulates fills) | Different SL calculation in backtest |
| HistoricalDataProvider (reads from DB) | Different feature computation in backtest |
| Backtest clock (fast-forward) | Different risk limits in backtest |

## 15.3 Walk-Forward Implementation

```python
class WalkForwardEngine:
    """Walk-forward backtest."""
    
    def __init__(self, config, data, window_config):
        self.config = config
        self.data = data
        self.window_config = window_config  # train_years, test_years, step_years
    
    def run(self):
        """Run walk-forward backtest."""
        results = []
        
        for window in self.generate_windows():
            # Train on window.train_period
            trained_config = self.train(window.train_period)
            
            # Test on window.test_period (same pipeline, different config)
            test_result = self.test(window.test_period, trained_config)
            results.append(test_result)
        
        return WalkForwardResults(results)
```

---

# 16. PAPER/LIVE PARITY

## 16.1 Shared Components

| Component | Backtest | Paper | Live |
|-----------|----------|-------|------|
| Feature Computation | ✅ Same | ✅ Same | ✅ Same |
| Evidence Families | ✅ Same | ✅ Same | ✅ Same |
| GSI | ✅ Same | ✅ Same | ✅ Same |
| Probability | ✅ Same | ✅ Same | ✅ Same |
| Setup | ✅ Same | ✅ Same | ✅ Same |
| Risk | ✅ Same | ✅ Same | ✅ Same |
| No-Trade | ✅ Same | ✅ Same | ✅ Same |
| Decision | ✅ Same | ✅ Same | ✅ Same |

## 16.2 Different Components

| Component | Backtest | Paper | Live |
|-----------|----------|-------|------|
| Data Adapter | BacktestMarketProvider | MT5MarketProvider | MT5MarketProvider |
| Execution Adapter | BacktestExecutionProvider | PaperExecutionProvider | MT5ExecutionProvider |
| Clock | Fast-forward | Real-time | Real-time |
| Data Source | Historical DB | Live MT5 | Live MT5 |

---

# 17. EXECUTION ISOLATION

## 17.1 Architecture

```
Decision Engine
    ↓
Execution Interface (abstract)
    ↓
┌─────────────────────────────────────┐
│ MT5ExecutionAdapter                 │
│ ├── connect()                       │
│ ├── send_order()                    │
│ ├── modify_position()               │
│ ├── close_position()                │
│ ├── get_positions()                 │
│ └── get_account()                   │
└─────────────────────────────────────┘
```

## 17.2 Benefits

- Trading logic never imports MT5 libraries
- Can swap broker by changing adapter only
- Can test with mock adapter
- Can run paper trading with simulated adapter

---

# 18. FAIL-SAFE DESIGN

## 18.1 Failure Modes and Responses

| Failure | Response | Fail Open/Closed |
|---------|----------|-----------------|
| Data unavailable | Skip bar; log warning | Fail Closed (no trade) |
| Stale data (> threshold) | Degrade features; log warning | Fail Closed |
| Invalid price (0, negative) | Skip bar; log error | Fail Closed |
| Extreme spread (> 5 pips) | No new entries | Fail Closed |
| Connection lost | Halt trading; SL/TP on broker | Fail Closed |
| Execution timeout | Retry once; then cancel | Fail Closed |
| Duplicate order | Reject; log error | Fail Closed |
| Partial fill | Log; adjust position | Fail Closed |
| Rejected order | Log; do not retry | Fail Closed |
| Position mismatch | Alert; reconcile | Fail Closed |
| Database unavailable | Buffer in memory; retry | Fail Closed |
| Clock drift | Use NTP; alert if drift > 1s | Fail Closed |

## 18.2 Default Decision

**When in doubt: NO TRADE.**

The system is designed to be **fail-closed** for trading. Every failure mode results in either:
- Skipping the current bar (no trade)
- Halting trading entirely
- Closing existing positions (if risk is at stake)

**Never:** Enter a trade when something is wrong.

---

# 19. OBSERVABILITY

## 19.1 Structured Logging

```python
@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: datetime
    level: str                          # "INFO", "WARNING", "ERROR"
    module: str                         # "market_structure", "probability", etc.
    event: str                          # "swing_detected", "bos_confirmed", etc.
    data: dict                          # Context data
    decision_id: str | None             # Link to decision
```

## 19.2 Metrics

| Category | Metrics |
|----------|---------|
| **Data** | Bars processed, ticks received, data quality score, freshness |
| **Features** | Features computed, missing features, computation time |
| **Signals** | Signals generated, signals blocked, signal quality |
| **Execution** | Orders sent, fills received, slippage, latency |
| **Risk** | Daily P&L, drawdown, positions, exposure |
| **System** | CPU usage, memory, database connections, uptime |

## 19.3 Health Checks

| Check | Frequency | Alert Threshold |
|-------|-----------|----------------|
| Data freshness | Every bar | > 5 minutes stale |
| Database connectivity | Every minute | Connection failed |
| MT5 connection | Every minute | Disconnected |
| Feature computation | Every bar | > 10 seconds |
| Decision generation | Every bar | > 5 seconds |

## 19.4 Decision Replay

Every decision can be fully reconstructed:

```python
class DecisionReplay:
    """Reconstruct a decision from audit trail."""
    
    def replay(self, decision_id):
        """Get full context for a decision."""
        decision = self.audit_trail.get(decision_id)
        return {
            'input_snapshot': decision.input_snapshot,
            'features': decision.features,
            'evidence': decision.evidence,
            'gsi': decision.gsi,
            'probability': decision.probability,
            'setup': decision.setup,
            'risk': decision.risk,
            'no_trade': decision.no_trade,
            'decision': decision.decision,
            'execution': decision.execution,
            'versions': decision.versions
        }
```

---

# 20. AUDIT TRAIL

## 20.1 Audit Record

```python
@dataclass(frozen=True)
class AuditRecord:
    """Complete audit trail for a decision."""
    decision_id: str
    timestamp: datetime
    
    # Input snapshot
    bar_snapshot: CanonicalBar
    session: CanonicalSession
    regime: str
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
    evidence_families: dict[str, CanonicalEvidence]
    
    # Probability snapshot
    p_long: float
    p_short: float
    p_no_trade: float
    probability_confidence: float
    calibration_status: str
    ece_score: float | None
    
    # Setup snapshot
    setup_valid: bool
    setup_quality: float
    setup_direction: str | None
    entry_trigger: str | None
    rr_ratio: float
    
    # Risk snapshot
    position_size: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    risk_amount: Decimal
    
    # No-Trade snapshot
    no_trade_severity: int
    no_trade_conditions: list[str]
    
    # Decision
    decision: str
    decision_reasons: list[str]
    
    # Execution
    execution_result: str | None
    fill_price: Decimal | None
    slippage: Decimal | None
    latency_ms: float | None
    
    # Versions
    model_version: str
    parameter_version: str
    formula_version: str
    spec_version: str
```

## 20.2 Question Answering

With the audit trail, we can answer:

| Question | How |
|----------|-----|
| "Why did the bot open this trade?" | Query decision record |
| "What was the GSI at entry?" | Check gsi_score in audit |
| "Was the spread normal?" | Check bar_snapshot.spread_at_close |
| "What regime was active?" | Check regime in audit |
| "Which version of the model was used?" | Check model_version |
| "Was the probability calibrated?" | Check calibration_status |

---

# 21. SECURITY

## 21.1 Secrets Management

| Secret | Storage | Access |
|--------|---------|--------|
| MT5 Login | Environment variable | Execution adapter only |
| MT5 Password | Environment variable | Execution adapter only |
| MT5 Server | Environment variable | Execution adapter only |
| FRED API Key | Environment variable | Macro provider only |
| Database URL | Environment variable | All modules (read-only for most) |
| Telegram Bot Token | Environment variable | Monitoring service only |

## 21.2 Principles

| Principle | Implementation |
|-----------|---------------|
| No secrets in code | All secrets in env vars or secrets manager |
| Least privilege | Database user has minimal permissions |
| Read/write separation | Trading logic reads; only execution writes to broker |
| Network isolation | VPS firewall; only required ports open |
| Audit logging | All secret access logged |

---

# 22. DEPLOYMENT ARCHITECTURE

## 22.1 Environments

| Environment | Purpose | Data | Execution |
|-------------|---------|------|-----------|
| **Development** | Local development | Sample data | Mock execution |
| **Backtest** | Historical testing | Historical DB | Simulated execution |
| **Paper** | Paper trading | Live MT5 data | Paper execution |
| **Production** | Live trading | Live MT5 data | Real execution |

## 22.2 Container Architecture

```
┌─────────────────────────────────────────┐
│ Docker Compose                           │
│                                          │
│ ┌──────────────┐  ┌──────────────┐      │
│ │ trading-bot  │  │ monitoring   │      │
│ │ (main)       │  │ (service)    │      │
│ └──────┬───────┘  └──────┬───────┘      │
│        │                  │              │
│ ┌──────▼──────────────────▼───────┐      │
│ │ PostgreSQL                       │      │
│ │ (database)                       │      │
│ └──────────────────────────────────┘      │
│                                          │
└─────────────────────────────────────────┘
```

---

# 23. REPOSITORY STRUCTURE

```
xauusd-trading-system/
├── src/
│   ├── canonical/              # Canonical data models
│   │   ├── bar.py
│   │   ├── tick.py
│   │   ├── news.py
│   │   ├── macro.py
│   │   ├── session.py
│   │   ├── swing.py
│   │   ├── liquidity.py
│   │   ├── flow.py
│   │   ├── evidence.py
│   │   ├── signal.py
│   │   ├── decision.py
│   │   ├── trade.py
│   │   └── __init__.py
│   │
│   ├── providers/              # Data source abstractions
│   │   ├── market_data.py      # Abstract MarketDataProvider
│   │   ├── news.py             # Abstract NewsProvider
│   │   ├── macro.py            # Abstract MacroProvider
│   │   ├── execution.py        # Abstract ExecutionProvider
│   │   ├── mt5/                # MT5 implementations
│   │   │   ├── market_data.py
│   │   │   ├── news.py
│   │   │   ├── macro.py
│   │   │   └── execution.py
│   │   ├── backtest/           # Backtest implementations
│   │   │   ├── market_data.py
│   │   │   ├── news.py
│   │   │   ├── macro.py
│   │   │   └── execution.py
│   │   └── paper/              # Paper trading implementations
│   │       └── execution.py
│   │
│   ├── ingestion/              # Data ingestion
│   │   ├── market.py
│   │   ├── news.py
│   │   ├── macro.py
│   │   └── futures.py
│   │
│   ├── validation/             # Data validation
│   │   ├── schema.py
│   │   ├── temporal.py
│   │   ├── range.py
│   │   └── completeness.py
│   │
│   ├── features/               # Feature engineering
│   │   ├── engine.py           # Feature computation pipeline
│   │   ├── store.py            # Feature store
│   │   ├── lineage.py          # Feature lineage tracking
│   │   └── registry.py         # Feature registry
│   │
│   ├── engines/                # Trading engines (Phase 2-15)
│   │   ├── market_structure.py
│   │   ├── liquidity.py
│   │   ├── flow.py
│   │   ├── trend.py
│   │   ├── momentum.py
│   │   ├── volatility.py
│   │   ├── gsi.py
│   │   ├── news_macro.py
│   │   ├── historical.py
│   │   ├── regime.py
│   │   ├── evidence.py
│   │   ├── probability.py
│   │   ├── setup.py
│   │   ├── risk.py
│   │   ├── no_trade.py
│   │   ├── trade_management.py
│   │   └── decision.py
│   │
│   ├── execution/              # Execution layer
│   │   ├── interface.py        # Abstract execution interface
│   │   ├── mt5_adapter.py      # MT5 adapter
│   │   ├── paper_adapter.py    # Paper adapter
│   │   └── backtest_adapter.py # Backtest adapter
│   │
│   ├── pipeline/               # Trading pipeline
│   │   ├── trading_pipeline.py
│   │   ├── backtest_pipeline.py
│   │   └── paper_pipeline.py
│   │
│   ├── persistence/            # Database
│   │   ├── database.py
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── repositories.py     # Data access
│   │   └── migrations/         # Alembic migrations
│   │
│   ├── audit/                  # Audit trail
│   │   ├── trail.py
│   │   └── recorder.py
│   │
│   ├── monitoring/             # Monitoring
│   │   ├── health.py
│   │   ├── metrics.py
│   │   └── alerts.py
│   │
│   ├── config/                 # Configuration
│   │   ├── settings.py
│   │   ├── parameters.py
│   │   └── registry.py
│   │
│   └── temporal/               # Temporal enforcement
│       ├── enforcer.py
│       ├── handler.py
│       └── protocol.py
│
├── tests/
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   ├── temporal/               # Temporal correctness tests
│   ├── property/               # Property-based tests
│   ├── backtest/               # Backtest regression tests
│   ├── execution/              # Execution simulation tests
│   └── e2e/                    # End-to-end tests
│
├── configs/
│   ├── default.yaml            # Default configuration
│   ├── backtest.yaml           # Backtest configuration
│   ├── paper.yaml              # Paper trading configuration
│   └── production.yaml         # Production configuration
│
├── docs/
│   ├── specifications/         # Phase 1-21 specifications
│   ├── architecture/           # Architecture documents
│   └── adr/                    # Architectural Decision Records
│
├── scripts/                    # Utility scripts
├── data/                       # Local data storage
├── migrations/                 # Database migrations
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

# 24. TESTING ARCHITECTURE

## 24.1 Test Categories

| Category | Purpose | Scope | Tools |
|----------|---------|-------|-------|
| **Unit** | Test individual functions | Single module | pytest |
| **Property** | Test mathematical properties | Feature engines | hypothesis |
| **Integration** | Test module interactions | Multiple modules | pytest |
| **Data Validation** | Test data quality | Data layer | pytest |
| **Temporal** | Test temporal correctness | All modules | pytest |
| **Backtest Regression** | Test backtest consistency | Full pipeline | pytest |
| **Execution Simulation** | Test execution logic | Execution layer | pytest |
| **End-to-End** | Test full pipeline | All layers | pytest |

## 24.2 Temporal Tests

```python
class TestTemporalCorrectness:
    """Tests that fail if data is used before availability_time."""
    
    def test_swing_not_available_before_confirmation(self):
        """Swing at bar t should not be available at bar t+1 if k>1."""
        # Create swing at bar 100 with k=3
        # Verify it's NOT available at bar 101, 102
        # Verify it IS available at bar 103
    
    def test_news_actual_not_available_before_release(self):
        """News actual should not be available before release_time."""
        # Create news event with release at 13:30
        # Verify actual is NOT available at 13:29
        # Verify actual IS available at 13:30
    
    def test_calibration_not_from_test_data(self):
        """Calibration parameters should come from training only."""
        # Run walk-forward
        # Verify calibration params at window w are from training of window w
        # Verify calibration params are NOT from test period
    
    def test_normalization_not_from_test_data(self):
        """Normalization params should come from training only."""
        # Run walk-forward
        # Verify median/IQR at window w are from training of window w
```

## 24.3 Backtest Regression Tests

```python
class TestBacktestRegression:
    """Tests that backtest results are reproducible."""
    
    def test_same_input_same_output(self):
        """Same data + same params = same result."""
        result1 = run_backtest(data, params)
        result2 = run_backtest(data, params)
        assert result1 == result2
    
    def test_no_look_ahead(self):
        """Feature at bar t uses only data through bar t."""
        # Run backtest with logging
        # Verify no feature uses data from bar > t
```

---

# 25. REPRODUCIBILITY

## 25.1 Reproducibility Requirements

Any backtest must be reproducible using:

| Component | Version Required |
|-----------|-----------------|
| Data version | Hash of input data |
| Feature version | Feature schema version |
| Formula version | Each formula's version |
| Model version | GSI, Probability model versions |
| Parameter version | Parameter snapshot |
| Code version | Git commit hash |

## 25.2 Reproducibility Record

```python
@dataclass(frozen=True)
class ReproducibilityRecord:
    """Record for reproducing a backtest."""
    run_id: str
    timestamp: datetime
    
    # Versions
    code_version: str                   # Git commit
    spec_version: str                   # SYSTEM_SPECIFICATION_V1.md
    data_version: str                   # Hash of input data
    feature_version: str                # Feature schema version
    parameter_version: str              # Parameter snapshot hash
    
    # Configuration
    config: SystemConfig
    
    # Results
    total_trades: int
    sharpe: float
    max_drawdown: float
    win_rate: float
    
    # Determinism
    random_seed: int | None             # For any stochastic elements
```

---

# 26. ARCHITECTURAL DECISION RECORDS

See companion document: `docs/architecture/ARCHITECTURAL_DECISION_RECORDS.md`

---

# 27. REMAINING ARCHITECTURE RISKS

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| R1 | MT5 API limitations may prevent required data access | HIGH | Test MT5 capabilities early; have fallback providers |
| R2 | PostgreSQL may be overkill for initial deployment | LOW | Can start with SQLite; migrate later |
| R3 | Synchronous pipeline may be too slow for live M5 | LOW | M5 = 288 bars/day; processing << 5 min/bar |
| R4 | Feature computation time may exceed bar interval | MEDIUM | Profile early; optimize hot paths |
| R5 | Walk-forward backtest may take hours | MEDIUM | Parallelize windows; use caching |
| R6 | GC Futures may not be available on MT5 | LOW | IFP proceeds without validation |
| R7 | News data quality may be insufficient | MEDIUM | Multiple providers; fallback to no-news mode |
| R8 | Calibration may be unstable with small datasets | MEDIUM | Minimum sample requirements enforced |

---

*Architecture designed. Ready for repository scaffolding.*
*No code has been written. All definitions are architectural specifications.*
