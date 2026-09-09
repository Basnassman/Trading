# PHASE 25 — News Data Availability Report

**Date:** 2026-09-01
**Status:** UNAVAILABLE — No news provider implemented

---

## 1. Summary

| Aspect | Status |
|--------|--------|
| News Provider Interface | ✅ Defined (NewsProvider ABC) |
| News Contract | ✅ Defined (CanonicalNewsEvent) |
| News Provider Implementation | ❌ Not implemented |
| Historical News Data | ❌ Not available |
| Real-time News Feed | ❌ Not implemented |

---

## 2. Required News Data

Based on **PHASE 7 — News & Macro Engine**:

| Data Type | Source Options | Availability |
|-----------|---------------|--------------|
| Economic Calendar | ForexFactory, Investing.com | ❌ Not implemented |
| High-impact news events | Multiple sources | ❌ Not implemented |
| News revisions (actual vs forecast) | ForexFactory, Investing.com | ❌ Not implemented |
| FOMC/NFP/CPI specific events | Multiple sources | ❌ Not implemented |
| News impact classification | Source-provided | ❌ Not implemented |

---

## 3. Data Requirements

### Economic Calendar Events
| Field | Required | Source |
|-------|----------|--------|
| event_name | ✅ | Provider |
| currency | ✅ | Provider |
| category | ✅ | Provider |
| importance | ✅ | Provider |
| release_time | ✅ | Provider |
| forecast | ✅ | Provider |
| actual | ✅ | Provider (after release) |
| previous | ✅ | Provider |

### News Revisions
| Field | Required | Source |
|-------|----------|--------|
| event_id | ✅ | Provider |
| revision_time | ✅ | Provider |
| new_actual | ✅ | Provider |
| is_revision | ✅ | Provider |

---

## 4. Temporal Requirements

| Rule | Implementation |
|------|---------------|
| News availability = release_time | Must be enforced |
| Revision availability = revision_time | Must be enforced |
| No future news in backtest | TemporalEnforcer |
| Late-arriving news | Handled as late data |

---

## 5. Architecture Notes

- `NewsProvider` ABC defined in `src/providers/interfaces.py`
- `CanonicalNewsEvent` and `CanonicalNewsRevision` defined in `src/canonical/contracts.py`
- Temporal enforcement will check `availability_time = release_time`

---

## 6. Impact on Trading System

| Phase | Dependency on News | Impact |
|-------|-------------------|--------|
| Phase 7 | News Engine | Cannot run without news data |
| Phase 10 | Evidence Family: News/Macro | Missing evidence family |
| Phase 14 | No-Trade: News risk | Cannot detect news risk |
| Phase 15 | Decision Engine | Partial evidence only |

---

## 7. Recommendation

**Priority:** MEDIUM

Before implementing Phase 7 (News Engine):
1. Choose news data provider (ForexFactory recommended)
2. Implement historical news data collection
3. Test temporal availability enforcement
4. Document data gaps and limitations

**Alternative:** Start with XAUUSD-specific events only (FOMC, NFP, CPI, Gold-specific news).

---

## 8. Classification

**UNAVAILABLE** — No news data collected or provider implemented.
