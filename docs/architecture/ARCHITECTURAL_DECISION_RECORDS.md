# ARCHITECTURAL DECISION RECORDS

## XAUUSD Quantitative Trading System

**Version:** 1.0.0
**Date:** 2026-08-31

---

## ADR-001: Database Technology

**Status:** Accepted

**Context:**
The system needs persistent storage for market data, features, decisions, trades, and audit trails. Data volume is moderate (M5 bars = ~50K/year, trades = ~1K/year).

**Decision:**
Use PostgreSQL as the primary database.

**Rationale:**
- ACID compliance for financial data integrity
- JSON support for flexible audit snapshots
- Mature Python ecosystem (SQLAlchemy, Alembic)
- Can handle expected data volume easily
- Existing project infrastructure uses PostgreSQL

**Alternatives Considered:**
- SQLite: Rejected — concurrent access limitations, no network access for monitoring
- TimescaleDB: Considered — PostgreSQL extension, can add later if time-series performance needed
- In-memory (Redis): Rejected — data loss risk, not suitable for audit trail

**Consequences:**
- Need PostgreSQL server in deployment
- Can migrate to TimescaleDB later if needed
- SQLAlchemy ORM provides database-agnostic code

---

## ADR-002: Data Provider Abstraction

**Status:** Accepted

**Context:**
Trading logic must not depend on specific data sources (MT5, FRED, etc.) to allow broker switching and provider changes.

**Decision:**
Use abstract base classes (interfaces) for all data providers. Concrete implementations are injected at runtime.

**Rationale:**
- Dependency Inversion Principle
- Enables backtest/paper/live parity
- Allows provider switching without code changes
- Testable with mock providers

**Alternatives Considered:**
- Direct MT5 calls: Rejected — tight coupling
- Configuration-based routing: Rejected — too complex, abstraction is cleaner

**Consequences:**
- Each provider needs a concrete implementation
- Slight overhead from interface indirection (negligible)
- Testing is straightforward with mock providers

---

## ADR-003: Event Processing Model

**Status:** Accepted

**Context:**
The system processes market data sequentially. Need to decide between synchronous and asynchronous processing.

**Decision:**
Use synchronous, sequential processing pipeline.

**Rationale:**
- Simplicity: Easier to debug and maintain
- Determinism: Same input order → same output order
- Replayability: Can replay historical data deterministically
- M5 timeframe = 288 bars/day; processing time << 5 minutes per bar
- No need for sub-second latency on M5

**Alternatives Considered:**
- Asynchronous (asyncio): Rejected — unnecessary complexity for M5 timeframe
- Message queue (Kafka/RabbitMQ): Rejected — overkill, adds failure modes
- Event sourcing: Rejected — too complex for current needs

**Consequences:**
- Simple codebase
- Easy to reason about execution order
- May need optimization if processing time approaches bar interval
- Can migrate to async later if timeframe decreases

---

## ADR-004: Execution Isolation

**Status:** Accepted

**Context:**
Trading logic must not directly call MT5 API. Need to support backtest, paper, and live with same logic.

**Decision:**
Use abstract ExecutionProvider interface with concrete adapters (MT5, Paper, Backtest).

**Rationale:**
- Trading logic is broker-agnostic
- Can swap brokers by changing adapter only
- Can test with mock adapter
- Paper trading uses simulated adapter
- Backtest uses simulated adapter

**Alternatives Considered:**
- Direct MT5 calls: Rejected — tight coupling
- Strategy pattern: Same concept, ABC is cleaner in Python

**Consequences:**
- Need adapter implementations for each execution mode
- Trading logic is clean and testable
- Adding a new broker requires only a new adapter

---

## ADR-005: Temporal Architecture

**Status:** Accepted

**Context:**
The system must prevent look-ahead bias. Every data point has three timestamps: event_time, availability_time, ingestion_time.

**Decision:**
Implement a TemporalEnforcer that checks availability_time before allowing data usage.

**Rationale:**
- Prevents look-ahead bias systematically
- Enables correct backtest simulation
- Handles late data, revisions, and out-of-order data
- Clear, auditable temporal rules

**Alternatives Considered:**
- Manual temporal checks: Rejected — error-prone
- Time-travel debugging: Rejected — too complex

**Consequences:**
- Every data contract must include availability_time
- Temporal tests can verify correctness
- Slight overhead from timestamp checking (negligible)

---

## ADR-006: GSI Role in Architecture

**Status:** Accepted

**Context:**
GSI (Gold Smart Index) was causing double counting when used as input to Probability Engine alongside Evidence Families.

**Decision:**
GSI is a Diagnostic Index only. It is NEVER an input to the Probability Engine. Evidence Families are the sole input to Probability.

**Rationale:**
- Prevents double counting
- Clean separation of concerns
- GSI is useful for human interpretation and as a filter
- Probability Engine receives pure, uncorrelated evidence

**Alternatives Considered:**
- Use GSI directly in Probability: Rejected — double counting
- Decompose GSI into families: Same as current decision
- Remove GSI entirely: Rejected — useful diagnostic

**Consequences:**
- GSI is computed but not used in probability calculation
- GSI is used as filter in Setup Engine
- GSI is used in audit trail and research
- Clean mathematical architecture

---

## ADR-007: No-Trade Architecture

**Status:** Accepted

**Context:**
No-Trade Engine was outputting decisions, conflicting with Decision Engine.

**Decision:**
No-Trade Engine outputs conditions and severity only. Decision Engine is the SOLE decision maker.

**Rationale:**
- Single authority for decisions
- Clear responsibility boundaries
- No conflicting decision vocabularies
- Decision Engine has complete context

**Alternatives Considered:**
- Keep both decision makers: Rejected — confusing
- Merge into one engine: Rejected — separation of concerns

**Consequences:**
- No-Trade Engine is a condition evaluator
- Decision Engine interprets severity into actions
- Clear audit trail

---

## ADR-008: Configuration Management

**Status:** Accepted

**Context:**
System has many parameters that need to be tracked, versioned, and potentially changed.

**Decision:**
Use YAML configuration files with version tracking. Parameters are logged with every decision.

**Rationale:**
- Human-readable format
- Version control friendly
- Easy to diff changes
- Can have environment-specific configs

**Alternatives Considered:**
- Database-stored config: Rejected — adds complexity
- Environment variables only: Rejected — not suitable for nested configs
- JSON: Rejected — YAML is more readable

**Consequences:**
- Config files in repository (excluding secrets)
- Parameter changes are tracked via git
- Each decision records which parameter version was used

---

## ADR-009: Feature Store Design

**Status:** Accepted

**Context:**
Features are computed from raw data and need to be stored, tracked, and versioned.

**Decision:**
Use a FeatureStore that stores FeatureRecords with full lineage and metadata.

**Rationale:**
- Every feature is traceable to its inputs
- Features can be recomputed from lineage
- Quality and confidence are tracked
- Supports debugging and research

**Alternatives Considered**
- In-memory only: Rejected — can't replay or audit
- Flat files: Rejected — query困难
- Database-only: Same as decision

**Consequences:**
- Feature computation is logged
- Lineage graph is maintainable
- Can identify which features contributed to a decision

---

## ADR-010: Backtest/Live Parity

**Status:** Accepted

**Context:**
Backtest results must match live trading results (modulo execution differences).

**Decision:**
Backtest uses the SAME pipeline code as live. Only the data and execution adapters differ.

**Rationale:**
- Prevents backtest-only logic
- Results are comparable
- Bugs in backtest are bugs in live
- Simplifies testing

**Alternatives Considered:**
- Separate backtest engine: Rejected — divergence risk
- Shared core with adapters: Same as decision

**Consequences:**
- One codebase for all modes
- Backtest is slower than optimized backtest engines
- But correctness is guaranteed

---

## ADR-011: Audit Trail Design

**Status:** Accepted

**Context:**
Every trading decision must be fully explainable after the fact.

**Decision:**
Store complete audit record for every decision, including all engine outputs, features, and versions.

**Rationale:**
- Regulatory compliance
- Debugging capability
- Research and improvement
- Trust and transparency

**Alternatives Considered:**
- Summary logging: Rejected — insufficient for debugging
- External audit system: Rejected — too complex

**Consequences:**
- Storage overhead (acceptable for M5 timeframe)
- Every decision is fully reconstructable
- Can answer "why did the bot make this trade?"

---

## ADR-012: Fail-Safe Design

**Status:** Accepted

**Context:**
The system handles real money. Failures must default to safe behavior.

**Decision:**
Implement fail-closed design. Default decision on any uncertainty is NO TRADE.

**Rationale:**
- Capital preservation is paramount
- False negatives (missed trades) are acceptable
- False positives (bad trades) are dangerous
- Every failure mode results in no trade or position closure

**Alternatives Considered:**
- Fail-open: Rejected — dangerous with real money
- Fail-degraded: Partially adopted — some failures degrade gracefully

**Consequences:**
- System is conservative
- May miss some trades during failures
- Capital is protected
- Requires monitoring to detect when system is degraded

---

## ADR-013: Testing Strategy

**Status:** Accepted

**Context:**
System needs comprehensive testing including temporal correctness.

**Decision:**
Use pytest with categories: unit, property, integration, temporal, backtest regression, e2e.

**Rationale:**
- Temporal tests are unique requirement
- Property tests verify mathematical properties
- Backtest regression ensures reproducibility
- E2E tests verify full pipeline

**Alternatives Considered:**
- unittest: Rejected — pytest is more powerful
- Separate test frameworks: Rejected — complexity

**Consequences:**
- Comprehensive test coverage
- Temporal correctness is enforceable
- Backtest results are reproducible

---

## ADR-014: Security Design

**Status:** Accepted

**Context:**
System handles real money and API credentials.

**Decision:**
Use environment variables for all secrets. No secrets in code or repository.

**Rationale:**
- Industry standard
- Simple to implement
- Compatible with Docker
- Git-compatible (secrets not committed)

**Alternatives Considered:**
- Secrets manager (Vault): Rejected — overkill for current scale
- Encrypted config files: Rejected — complexity

**Consequences:**
- Secrets must be set in environment
- Docker compose uses env_file
- Documentation must clearly list required env vars

---

## ADR-015: Deployment Model

**Status:** Accepted

**Context:**
System needs to run in multiple environments (dev, backtest, paper, production).

**Decision:**
Use Docker Compose with separate compose files per environment.

**Rationale:**
- Consistent environments
- Easy to deploy
- Compatible with VPS hosting
- Can run locally for development

**Alternatives Considered:**
- Kubernetes: Rejected — too complex for single-bot deployment
- Bare metal: Rejected — environment inconsistency
- Cloud functions: Rejected — not suitable for long-running trading bot

**Consequences:**
- Docker knowledge required
- Consistent deployment across environments
- Easy to scale later if needed

---

*All ADRs documented. Architecture is complete and ready for repository scaffolding.*
