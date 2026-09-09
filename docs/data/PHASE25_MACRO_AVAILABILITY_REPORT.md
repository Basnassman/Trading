# PHASE 25 — Macro Data Availability Report

**Date:** 2026-09-01
**Status:** UNAVAILABLE — No macro provider implemented

---

## 1. Summary

| Aspect | Status |
|--------|--------|
| Macro Provider Interface | ✅ Defined (MacroProvider ABC) |
| Macro Contract | ✅ Defined (CanonicalMacroObservation) |
| Macro Provider Implementation | ❌ Not implemented |
| Historical Macro Data | ❌ Not available |

---

## 2. Required Macro Data

Based on **PHASE 7 — News & Macro Engine**:

| Indicator | Source Options | Availability |
|-----------|---------------|--------------|
| DXY (US Dollar Index) | Investing.com, FRED | ❌ Not implemented |
| US 10Y Treasury Yield | FRED, Investing.com | ❌ Not implemented |
| US 2Y Treasury Yield | FRED, Investing.com | ❌ Not implemented |
| Yield Curve Spread | Derived (10Y - 2Y) | ❌ Not implemented |
| Real Rates | Derived (Nominal - Inflation) | ❌ Not implemented |
| VIX | CBOE, Investing.com | ❌ Not implemented |
| S&P 500 | Multiple sources | ❌ Not implemented |
| Gold Futures (GC) | CME, Investing.com | ❌ Not implemented |
| CPI / Inflation Data | FRED | ❌ Not implemented |
| FOMC Rate Decisions | FRED, Fed website | ❌ Not implemented |

---

## 3. Data Requirements

### Real-time/Live Macro Data
| Indicator | Update Frequency | Unit | Precision |
|-----------|-----------------|------|-----------|
| DXY | Real-time | Index | 2 decimals |
| 10Y Yield | Daily | % | 3 decimals |
| 2Y Yield | Daily | % | 3 decimals |
| VIX | Real-time | Index | 2 decimals |
| Gold Futures | Real-time | USD | 2 decimals |

### Historical Macro Data
| Indicator | Required Period | Min Frequency |
|-----------|----------------|---------------|
| DXY | 2016-2026 | Daily |
| Yields | 2016-2026 | Daily |
| CPI | 2016-2026 | Monthly |
| FOMC decisions | 2016-2026 | Event-based |
| Gold Futures | 2016-2026 | Daily |

---

## 4. Gold Futures (GC) — Special Case

Per **PHASE 22 (ADR-016)**: Gold Futures data is used as an independent reference, not as a primary data source.

| Aspect | Detail |
|--------|--------|
| Symbol | GC (CME) |
| Usage | Cross-reference for price, volume, sentiment |
| Independence | Yes — separate from XAUUSD spot |
| Availability | ❌ Not implemented |
| Source Options | Investing.com, CME, Yahoo Finance |

---

## 5. Temporal Requirements

| Rule | Implementation |
|------|---------------|
| Macro data availability = observation_time | Must be enforced |
| Revisions availability = revision_time | Must be enforced |
| No future macro in backtest | TemporalEnforcer |
| Late-arriving revisions | Handled as late data |

---

## 6. Architecture Notes

- `MacroProvider` ABC defined in `src/providers/interfaces.py`
- `CanonicalMacroObservation` defined in `src/canonical/contracts.py`
- Temporal enforcement: `availability_time = observation_time`

---

## 7. Impact on Trading System

| Phase | Dependency on Macro | Impact |
|-------|-------------------|--------|
| Phase 7 | Macro Engine | Cannot run without macro data |
| Phase 9 | Regime Detection | Missing regime inputs |
| Phase 10 | Evidence Family: Macro | Missing evidence family |
| Phase 15 | Decision Engine | Partial evidence only |

---

## 8. Recommendation

**Priority:** MEDIUM

Before implementing Phase 7 (Macro Engine):
1. Choose macro data provider (FRED API recommended for US rates)
2. Implement historical macro data collection
3. Test temporal availability enforcement
4. Document data gaps

**Minimum viable macro for XAUUSD:**
- DXY (US Dollar strength)
- US 10Y Treasury Yield
- US 2Y Treasury Yield
- Gold Futures (GC) — as independent reference

---

## 9. Classification

**UNAVAILABLE** — No macro data collected or provider implemented.
