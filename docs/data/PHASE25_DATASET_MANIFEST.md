# PHASE 25 — Dataset Manifest

**Date:** 2026-09-01
**Status:** MOCK DATA ONLY — No real dataset collected

---

## 1. Dataset Registry

| Dataset ID | Symbol | Source | Period | Timeframes | Status |
|------------|--------|--------|--------|------------|--------|
| MOCK-XAUUSD-v1 | XAUUSD | Mock Provider | Synthetic | M1, M5, M15, H1, H4, D1 | ✅ Available |
| REAL-XAUUSD-v1 | XAUUSD | MT5 | 2016-2026 | M5, M15, H1, H4, D1 | ❌ Not collected |
| MACRO-DXY-v1 | DXY | FRED | 2016-2026 | Daily | ❌ Not collected |
| NEWS-CALENDAR-v1 | All | ForexFactory | 2016-2026 | Event-based | ❌ Not collected |

---

## 2. Mock Dataset Details

### MOCK-XAUUSD-v1
| Field | Value |
|-------|-------|
| Dataset ID | MOCK-XAUUSD-v1 |
| Symbol | XAUUSD |
| Source | MockMarketDataProvider |
| Base Price | 1850.0 |
| Seed | 42 |
| Volatility | σ = 2.0 per bar |
| Schema Version | 1.0 |
| Record Count | Variable (per request) |
| Timezone | UTC |
| Data Quality | SYNTHETIC |
| Purpose | Testing validation pipeline only |

**⚠️ DO NOT use mock data for trading decisions or strategy evaluation.**

---

## 3. Real Dataset (Projected)

### REAL-XAUUSD-v1 (When MT5 Available)
| Field | Expected Value |
|-------|---------------|
| Dataset ID | REAL-XAUUSD-v1 |
| Symbol | XAUUSD |
| Source | MT5 (broker-dependent) |
| Period | 2016-01-01 to 2026-08-31 |
| Timeframes | M5, M15, H1, H4, D1 |
| Tick Availability | Broker-dependent |
| Volume Type | tick_volume (primary) |
| Spread Availability | Broker-dependent |
| Schema Version | 1.0 |

---

## 4. Data Version Tracking

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-09-01 | Initial schema — RawBar, CanonicalBar, validators |

---

## 5. Reproducibility

| Requirement | Status |
|-------------|--------|
| Dataset ID recorded | ✅ |
| Source recorded | ✅ |
| Period recorded | ✅ |
| Schema version recorded | ✅ |
| Quality summary | ✅ (mock only) |
| Missing ranges | ✅ (mock: none) |

---

## 6. Manifest Usage

Every backtest run MUST reference a dataset by its ID:
```
dataset_id: REAL-XAUUSD-v1
schema_version: 1.0
period: 2016-01-01 to 2026-08-31
```

This ensures reproducibility and prevents silent data changes.
