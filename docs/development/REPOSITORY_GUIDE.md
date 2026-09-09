# Repository Guide

## XAUUSD Quantitative Trading System

This guide explains the repository structure, where to find things, and how modules relate to the specifications.

---

## Quick Reference

| What | Where |
|------|-------|
| Domain contracts (entities) | `src/canonical/contracts.py` |
| Enums (types) | `src/canonical/enums.py` |
| Time semantics | `src/canonical/time.py` |
| Provider interfaces | `src/providers/interfaces.py` |
| Engine interfaces | `src/engines/interfaces.py` |
| Configuration | `src/config/settings.py` |
| Error model | `src/errors/exceptions.py` |
| Temporal enforcer | `src/temporal/enforcer.py` |
| Audit contracts | `src/audit/contracts.py` |
| Tests | `tests/` |
| Specifications | `docs/specifications/` |
| Architecture | `docs/architecture/` |
| Configuration files | `configs/` |
| Database migrations | `migrations/` |

---

## Module → Phase Mapping

| Module | Phase | Description |
|--------|-------|-------------|
| `src/canonical/` | All | Data contracts shared across phases |
| `src/engines/market_structure.py` | Phase 2 | Swing points, BOS, MSS |
| `src/engines/liquidity.py` | Phase 3 | Liquidity levels, sweeps |
| `src/engines/flow.py` | Phase 4 | Institutional Flow Proxy |
| `src/engines/trend.py` | Phase 5 | Trend scoring |
| `src/engines/momentum.py` | Phase 5 | Momentum scoring |
| `src/engines/volatility.py` | Phase 5 | Volatility scoring |
| `src/engines/gsi.py` | Phase 6 | Gold Smart Index (diagnostic) |
| `src/engines/news_macro.py` | Phase 7 | News/Macro analysis |
| `src/engines/historical.py` | Phase 8 | Historical similarity |
| `src/engines/regime.py` | Phase 9 | Regime detection |
| `src/engines/evidence.py` | Phase 10 | Evidence family aggregation |
| `src/engines/probability.py` | Phase 10 | Probability computation |
| `src/engines/setup.py` | Phase 11 | Setup validation |
| `src/engines/risk.py` | Phase 12 | Risk management |
| `src/engines/no_trade.py` | Phase 14 | No-trade conditions |
| `src/engines/decision.py` | Phase 15 | Final decision |
| `src/engines/trade_management.py` | Phase 13 | Position management |
| `src/execution/` | Phase 19 | Execution adapters |
| `src/pipeline/` | Phase 16 | Backtest/paper/live pipelines |
| `src/persistence/` | Phase 1 | Database layer |
| `src/audit/` | Phase 21 | Audit trail |
| `src/monitoring/` | Phase 20 | Health monitoring |

---

## Architecture Documents

| Document | Location |
|----------|----------|
| System Specification V1 | `docs/specifications/SYSTEM_SPECIFICATION_V1.md` |
| System Architecture V1 | `docs/architecture/SYSTEM_ARCHITECTURE_V1.md` |
| ADRs | `docs/architecture/ARCHITECTURAL_DECISION_RECORDS.md` |
| Phase 1-21 Specs | `docs/specifications/PHASE{1-21}_*.md` |

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run only temporal tests
pytest tests/temporal/ -v -m temporal

# Run only contract tests
pytest tests/contracts/ -v -m contract

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## Key Architectural Rules

1. **GSI is diagnostic only** — never an input to Probability Engine
2. **Evidence Families are sole input to Probability** — no double counting
3. **Decision Engine is sole decision maker** — No-Trade outputs conditions only
4. **All timestamps are UTC** — naive datetime is rejected
5. **Fail-closed** — default to NO_TRADE on any uncertainty
6. **No secrets in code** — environment variables only
7. **Same logic for backtest/paper/live** — only adapters differ

---

## Adding New Features

1. Add contract to `src/canonical/contracts.py`
2. Add interface to `src/engines/interfaces.py`
3. Implement in `src/engines/`
4. Add tests in `tests/`
5. Update this guide
