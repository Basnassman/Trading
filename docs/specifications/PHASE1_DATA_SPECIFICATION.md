# PHASE 1 — DATA SPECIFICATION

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 2.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define **every data point** the system requires, its source hierarchy, resolution, necessity, downstream usage, availability timeline, provenance tracking, quality scoring, and associated risk.

This specification is the foundation for all subsequent engines (Market Structure, Liquidity, Flow, Momentum, Volatility, GSI, News, Historical, Regime, Probability).

**Scope Boundary:**
- This specification covers **data acquisition, representation, and provenance only**.
- Feature engineering, scoring, and processing belong to their respective engine phases.
- No data source is assumed available unless explicitly stated with a source hierarchy.
- All data sources are provisional until the Data Architecture phase finalizes them.

---

## B — INPUTS

The system requires data across five orthogonal domains:

| Domain | Purpose | Update Frequency |
|--------|---------|-----------------|
| A. Market Data | Price action, microstructure, volume | Real-time / Tick |
| B. Macro Data | Interest rates, currency indices | Intraday / Daily |
| C. Economic News | Scheduled releases, surprises, revisions | Event-driven |
| D. Historical Data | Training, backtesting, similarity | Static / Batch |
| E. Session Data | Trading session boundaries (timezone-aware) | Daily / Weekly |

**Existing Codebase Data Capabilities (from `src/`):**

| Module | Current Capability | Gap vs. This Spec |
|--------|-------------------|-------------------|
| `mt5_connector.py` | OHLCV (M1–MN1), Tick data (bid/ask/spread/volume), Account info | No Treasury Yields, no DXY, no DST-aware sessions |
| `event_intelligence.py` | MacroEvent ingestion (CPI, NFP, FOMC, RATES, GEOPOLITICAL, USD_MACRO) | No Revision tracking, no provenance, no quality scoring |
| `event_models.py` | MacroEvent schema (name, category, impact, timestamp, actual/forecast/previous) | Missing: Revision field, release_timestamp, unit, source, quality |
| `config.py` | Symbol (XAUUSD), Timeframes (M1–MN1), Risk params | No session timezone config, no yield config, no source hierarchy |
| `schemas.py` | TradeSignal, ExecutionDecision | N/A for data spec |

---

## C — MATHEMATICAL DEFINITIONS

### C.1 — Notation Convention

Let $t$ denote a timestamp. Let $O_t, H_t, L_t, C_t, V_t$ denote Open, High, Low, Close, Volume at time $t$.

For a sequence of bars: $\{b_t\}_{t=1}^{N}$ where $b_t = (O_t, H_t, L_t, C_t, V_t, \tau_t, \pi_t)$ and:
- $\tau_t$ = bar timestamp (UTC)
- $\pi_t$ = provenance record (see Section N)

### C.2 — Data Point Definitions

#### Market Data Fields

| Symbol | Definition | Type | Precision |
|--------|-----------|------|-----------|
| $O_t$ | Open price of bar $t$ | float64 | 2 decimals (XAUUSD) |
| $H_t$ | High price of bar $t$ | float64 | 2 decimals |
| $L_t$ | Low price of bar $t$ | float64 | 2 decimals |
| $C_t$ | Close price of bar $t$ | float64 | 2 decimals |
| $V_{tick,t}$ | Tick volume of bar $t$ (count of price changes) | int64 | Exact count |
| $V_{broker,t}$ | Broker real volume (if available) | int64 or None | Exact contracts |
| $V_{exchange,t}$ | Exchange volume (from GC futures, if used) | int64 or None | Exact contracts |
| $\text{Bid}_t$ | Bid price at tick $t$ | float64 | 2 decimals |
| $\text{Ask}_t$ | Ask price at tick $t$ | float64 | 2 decimals |
| $S_t = \text{Ask}_t - \text{Bid}_t$ | Spread at tick $t$ | float64 | 2 decimals |
| $\tau_t$ | UTC timestamp | datetime64[ns, UTC] | Nanosecond precision |

**Volume Classification (Rule 3 Compliance):**

| Volume Type | Definition | Availability | Label | Institutional Flow? |
|-------------|-----------|-------------|-------|---------------------|
| Tick Volume | Count of price changes per bar | Always (MT5) | `tick_volume` | ❌ **No** — Proxy only |
| Broker Real Volume | Actual contracts traded (broker-specific) | Broker-dependent | `broker_real_volume` | ⚠️ Partial — Broker scope only |
| Exchange Volume | CME GC futures volume | Requires exchange feed | `exchange_volume` | ✅ Closest proxy — Centralized |
| Composite Volume | Weighted combination | Derived | `composite_volume` | Derived — Not raw |

**Critical Distinction:**
- XAUUSD spot does **not** have a centralized order book or unified volume.
- Tick volume is a **proxy** for activity, not institutional order flow.
- Gold Futures (GC) on CME provides the closest centralized volume reference.
- The system must **never** label tick volume as "institutional order flow."

#### Macro Data Fields

| Symbol | Definition | Type | Precision | Source Hierarchy |
|--------|-----------|------|-----------|-----------------|
| $D_t$ | DXY (US Dollar Index) value | float64 | 2 decimals | Primary → Secondary → Fallback |
| $Y_{2,t}$ | US 2-Year Treasury Yield (%) | float64 | 3 decimals | Primary → Secondary → Fallback |
| $Y_{10,t}$ | US 10-Year Treasury Yield (%) | float64 | 3 decimals | Primary → Secondary → Fallback |
| $\text{FFR}_t$ | Fed Funds Rate (%) | float64 | 2 decimals | Primary → Secondary → Fallback |
| $\text{FFE}_t$ | Fed Funds Expected (implied from futures) | float64 | 3 decimals | Primary → Secondary → Fallback |

**Source Hierarchy Design:**

```
┌─────────────────────────────────────────────────────┐
│              MACRO DATA SOURCE HIERARCHY             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  PRIMARY (Real-time, Intraday)                      │
│  ├── Direct Broker Feed (if available)              │
│  ├── MetaAPI Cloud (DXY, some yields)               │
│  └── Priority: Latency < 60s                        │
│                                                     │
│  SECONDARY (Delayed, Daily)                         │
│  ├── FRED API (Treasury yields, official)           │
│  ├── Investing.com API (DXY, yields)                │
│  └── Priority: Latency < 30min                      │
│                                                     │
│  FALLBACK (Static, End-of-Day)                      │
│  ├── Yahoo Finance API (delayed EOD)                │
│  ├── CSV/JSON manual curation                       │
│  └── Priority: Latency < 24h                        │
│                                                     │
│  SELECTION RULE:                                    │
│  1. Try Primary → if fresh (< threshold) → use     │
│  2. Try Secondary → if fresh → use                 │
│  3. Fall back to Fallback → flag quality: degraded  │
│  4. If all fail → skip macro-dependent features     │
└─────────────────────────────────────────────────────┘
```

**Source Hierarchy Decision Log:**

| Data Point | Primary | Secondary | Fallback | Intraday Available? |
|------------|---------|-----------|----------|-------------------|
| DXY | Broker feed / MetaAPI | Investing.com | Yahoo Finance | Yes (if broker) |
| US 2Y Yield | Broker feed | FRED API | Yahoo Finance | No (daily only) |
| US 10Y Yield | Broker feed | FRED API | Yahoo Finance | No (daily only) |
| Fed Funds Rate | FRED API | Central bank site | Manual | No (event-driven) |
| Fed Funds Expected | CME FedWatch | Bloomberg | Manual | Yes (if available) |

**Timing Mismatch Handling:**
- Yields are typically daily values (published after market close).
- DXY may be available intraday via broker.
- **Resolution:** Macro data is forward-filled from its publication timestamp. In backtesting, use the **publication date** not the reference date.

#### Economic News Fields

| Symbol | Definition | Type | Precision |
|--------|-----------|------|-----------|
| $\text{event\_id}_i$ | Unique identifier for event $i$ | string | UUID |
| $\text{release\_ts}_i$ | Scheduled release timestamp (UTC) | datetime64[ns, UTC] | Nanosecond |
| $\text{currency}_i$ | Currency affected (e.g., "USD") | string | ISO 4217 |
| $\text{event\_name}_i$ | Event name (e.g., "CPI m/m") | string | Free text |
| $\text{importance}_i$ | Impact level | int (1–4) | Enum |
| $A_i$ | Actual value | float64 or None | Per-event unit |
| $F_i$ | Forecast (consensus) value | float64 or None | Per-event unit |
| $P_i$ | Previous value (as originally released) | float64 or None | Per-event unit |
| $R_i$ | Revision to previous value | float64 or None | Per-event unit |
| $\text{unit}_i$ | Unit of measurement (e.g., "%", "K", "index") | string | Standardized |
| $\text{source}_i$ | Data provider | string | Enum |

**Revision Handling (Critical for Backtest Integrity):**

| Field | Definition | When Available | Backtest Rule |
|-------|-----------|---------------|---------------|
| $P_i$ (first release) | Value as originally published | At release time | ✅ Use in real-time |
| $P_i^{revised}$ | Revised value (if any) | At revision timestamp | ❌ **Not** available at release time |
| $R_i$ | $P_i^{revised} - P_i$ (first release) | At revision timestamp | ❌ **Not** available at release time |
| $\text{revision\_ts}_i$ | When revision was published | Post-event | Store for provenance |

**Backtest Rule for Revisions:**
- At time $t < \text{revision\_ts}_i$: Use $P_i$ (first release)
- At time $t \geq \text{revision\_ts}_i$: System may optionally use $P_i^{revised}$ for analysis, but must log that the value changed
- **Never** use revised values in real-time signal generation if the revision hasn't occurred yet

#### Session Fields (Timezone-Aware)

| Symbol | Definition | Type |
|--------|-----------|------|
| $\text{session\_id}$ | Unique session identifier | string |
| $\text{T}_{open}$ | Session open time | time |
| $\text{T}_{close}$ | Session close time | time |
| $\text{TZ}$ | Timezone identifier | string (IANA) |
| $\text{DST}$ | Daylight Saving Time state | boolean |
| $\text{T}_{open,UTC}$ | Open time converted to UTC | datetime |
| $\text{T}_{close,UTC}$ | Close time converted to UTC | datetime |

**Session Definition Schema:**

```json
{
  "session_id": "london",
  "name": "London Session",
  "open": "08:00",
  "close": "16:00",
  "timezone": "Europe/London",
  "dst_aware": true,
  "notes": "UTC offset varies: GMT+0 (winter) / BST+1 (summer)"
}
```

**DST Handling:**
- Sessions are defined in **local time** with IANA timezone.
- UTC conversion is computed **dynamically** at runtime based on the bar's date.
- The system must store both local and UTC representations.
- DST transitions are handled by the timezone library (pytz / zoneinfo).

---

## D — FORMULAS

### D.1 — Spread Calculation

$$S_t = \text{Ask}_t - \text{Bid}_t$$

### D.2 — Volume Classification Formula

For any bar $t$, the available volume types are:

$$V_t = \begin{cases}
V_{tick,t} & \text{always available} \\
V_{broker,t} & \text{if broker provides real volume} \\
V_{exchange,t} & \text{if GC futures feed available} \\
V_{composite,t} = w_1 \cdot V_{tick,t} + w_2 \cdot V_{broker,t} + w_3 \cdot V_{exchange,t} & \text{derived}
\end{cases}$$

Where $w_1 + w_2 + w_3 = 1$ and weights are determined by availability and quality.

**Default weights (subject to testing):**
- If only tick volume: $w_1 = 1.0$
- If broker + tick: $w_1 = 0.4, w_2 = 0.6$
- If all three: $w_1 = 0.2, w_2 = 0.4, w_3 = 0.4$

### D.3 — News Surprise Z-Score

$$Z_i = \frac{A_i - F_i}{\sigma_{\text{surprise},i}}$$

Where:
- $A_i$ = Actual value
- $F_i$ = Forecast value
- $\sigma_{\text{surprise},i}$ = Standard deviation of historical surprises for event $i$

**Minimum Sample:** $n \geq 20$ historical surprises before computing $Z_i$. Below this threshold, use raw surprise: $S_i = A_i - F_i$.

### D.4 — Revision-Adjusted Surprise

$$Z_i^{adj} = \frac{A_i - (P_i^{revised})}{\sigma_{\text{surprise},i}}$$

Where $P_i^{revised} = P_i + R_i$ is the revised previous value.

**Availability Rule:**
- At release time: $Z_i = \frac{A_i - F_i}{\sigma_{\text{surprise},i}}$ (uses forecast)
- After revision: $Z_i^{adj} = \frac{A_i - P_i^{revised}}{\sigma_{\text{surprise},i}}$ (uses revised previous)
- The system logs which version was used and when.

### D.5 — Session Identification (Dynamic UTC)

Let $\tau_t$ be the UTC timestamp of bar $t$.

For each session $s \in \{\text{Asian}, \text{London}, \text{NewYork}\}$:

$$\text{Convert}(\text{T}_{open,s}, \text{TZ}_s, \text{date}_t) \rightarrow \text{T}_{open,s,UTC}$$
$$\text{Convert}(\text{T}_{close,s}, \text{TZ}_s, \text{date}_t) \rightarrow \text{T}_{close,s,UTC}$$

Then:

$$\text{Session}_t = \begin{cases}
s & \text{if } \text{T}_{open,s,UTC} \leq \tau_t < \text{T}_{close,s,UTC} \\
\text{Overlap}_{L/NY} & \text{if } \tau_t \in \text{T}_{open,NY,UTC} \cap \text{T}_{open,L,UTC} \\
\text{OffSession} & \text{otherwise}
\end{cases}$$

**DST State Storage:**

$$\text{DST}_s(t) = \begin{cases}
\text{True} & \text{if } \text{TZ}_s \text{ is in DST at date}_t \\
\text{False} & \text{otherwise}
\end{cases}$$

This must be stored with each bar's session record for auditability.

### D.6 — Data Freshness Metric

$$\text{Age}_t = \text{now} - \tau_{\text{latest}}$$

If $\text{Age}_t > \text{Threshold}_{\text{source}}$, the system must flag stale data and potentially halt execution.

**Per-Source Freshness Thresholds:**

| Source | Max Age | Action if Exceeded |
|--------|---------|-------------------|
| MT5 OHLCV (real-time) | 300 seconds | Halt execution |
| MT5 Tick data | 60 seconds | Halt execution |
| DXY (Primary) | 600 seconds | Degrade macro features |
| DXY (Secondary) | 3600 seconds | Degrade macro features |
| Yields (all) | 86400 seconds (1 day) | Skip yield features |
| News events | Event-dependent | Skip news features |

---

## E — PARAMETERS

### E.1 — Initial Parameters (Subject to Testing — Rule 7)

| Parameter | Initial Value | Description |
|-----------|--------------|-------------|
| `ATR_PERIOD` | 14 | ATR lookback for spread/volume normalization |
| `RVOL_LOOKBACK` | 20 | EMA period for Relative Volume |
| `SESSION_ASIAN_OPEN` | 00:00 (Asia/Tokyo) | Asian session start (local time) |
| `SESSION_ASIAN_CLOSE` | 08:00 (Asia/Tokyo) | Asian session end (local time) |
| `SESSION_LONDON_OPEN` | 08:00 (Europe/London) | London session start (local time) |
| `SESSION_LONDON_CLOSE` | 16:00 (Europe/London) | London session end (local time) |
| `SESSION_NY_OPEN` | 08:00 (America/New_York) | New York session start (local time) |
| `SESSION_NY_CLOSE` | 17:00 (America/New_York) | New York session end (local time) |
| `MIN_SURPRISE_SAMPLES` | 20 | Minimum historical surprises for Z-score |
| `DATA_FRESHNESS_THRESHOLD` | 300 seconds | Max age before stale data alert (real-time) |
| `HISTORY_MIN_YEARS` | 5 | Minimum years for backtest |
| `HISTORY_TARGET_YEARS` | 10 | Target years for full analysis |
| `PRIMARY_TIMEFRAME` | M5 | Primary execution timeframe |
| `STRUCTURE_TIMEFRAMES` | D1, H4, H1, M15, M5 | Multi-timeframe analysis set |
| `TICK_RAW_RETENTION_DAYS` | 90–180 | Raw tick data retention (see storage analysis) |
| `TICK_FEATURE_RETENTION_DAYS` | 365 | Aggregated tick features retention |
| `VOLUME_WEIGHT_TICK` | 0.4 | Default weight for tick volume |
| `VOLUME_WEIGHT_BROKER` | 0.6 | Default weight for broker real volume |

### E.2 — Parameter Justification

| Parameter | Why This Value | What Could Change It |
|-----------|---------------|---------------------|
| ATR_PERIOD=14 | Industry standard; balances responsiveness vs. noise | Optimization phase (Phase 17) |
| RVOL_LOOKBACK=20 | ~1 trading day on M5; smooths intraday noise | Statistical analysis of volume autocorrelation |
| Session times (local) | Standard institutional sessions; DST-aware | Broker-specific session data |
| MIN_SURPRISE_SAMPLES=20 | Minimum for CLT approximation to hold | Sensitivity analysis |
| TICK_RAW_RETENTION=90–180d | Balance between analysis depth and storage cost | Storage capacity analysis |

---

## F — NORMALIZATION

### F.1 — Price Data

Price data enters the system in raw form (XAUUSD, 2 decimals). No normalization at ingestion; normalization happens in engine phases.

### F.2 — Volume Data

For Relative Volume calculation (to be implemented in Flow Engine):

$$\text{RVOL}_t = \frac{V_t}{\text{EMA}(V, \text{lookback})_t}$$

This produces a unitless ratio where:
- RVOL = 1.0 → average volume
- RVOL > 1.0 → above average
- RVOL < 1.0 → below average

**Volume Source Selection:** The system uses the highest-quality available volume source (see D.2).

### F.3 — Yield Data

Yields enter as percentages (e.g., 4.25%). No conversion needed at ingestion.

### F.4 — News Surprise

Z-scores are already normalized (mean=0, std=1 by construction). Raw surprises ($A_i - F_i$) require normalization per-event in the News Engine.

### F.5 — DXY

DXY enters as a raw index value (e.g., 104.50). Normalization deferred to macro engine.

---

## G — EDGE CASES

### G.1 — Missing Data Points

| Scenario | Handling | Risk |
|----------|----------|------|
| MT5 returns `None` for OHLCV | Retry up to 3 times; if persistent, flag and skip bar | Gap in structure analysis |
| No tick data available | Use OHLCV close as proxy; flag `data_quality: "degraded"` | Reduced microstructure analysis |
| DXY feed fails (all sources) | Use last known value with staleness flag; max staleness = 4 hours | Macro engine degradation |
| Yield data unavailable | Skip yield-dependent features; do not impute | Reduced macro context |
| News event missing forecast | Skip Z-score for that event; use raw surprise if actual available | Reduced surprise signal |
| Revision data unavailable | Use first-release value; log `revision_status: "unrevised"` | Backtest may differ from real-time |
| Session DST transition | Re-compute UTC boundaries for each bar's date | Edge case: bars near transition may be misclassified |

### G.2 — Data Alignment

Different data sources have different timestamps:
- MT5 OHLCV: Bar close timestamp (UTC)
- Macro data: Daily values (typically end-of-day UTC)
- News events: Scheduled release time (UTC)
- Session times: Dynamic UTC based on timezone + DST

**Alignment Rule:** All data is aligned to the **bar timestamp** of the primary timeframe (M5). Macro and news data are forward-filled to the next bar, with a staleness flag if the gap exceeds the source's freshness threshold.

### G.3 — Weekend / Holiday Gaps

- MT5 does not provide weekend data (Forex closed Saturday–Sunday).
- Holiday data may have early closes or no data.
- **Handling:** Gaps are detected and flagged. Structure and liquidity calculations must account for time gaps.

### G.4 — Session Overlap Handling

When London and NY overlap:
- Volume and spread data are combined.
- Session label = `Overlap`.
- DST affects overlap duration (summer: 13:00–16:00 UTC; winter: 12:00–17:00 UTC approximately).
- **Risk:** Overlap periods have highest liquidity but also highest volatility.

### G.5 — Data Frequency Mismatch

MT5 provides tick data and OHLCV at various timeframes. Macro data is daily.
- **Resolution:** All data is resampled to the primary timeframe (M5) using appropriate aggregation rules:
  - OHLCV: Direct (already at timeframe)
  - Tick: Aggregated to bar (Open=first, High=max, Low=min, Close=last, Volume=sum)
  - Macro: Forward-fill until next update

### G.6 — Volume Source Unavailability

If only tick volume is available:
- Use tick volume as the sole volume measure.
- Flag `volume_type: "tick_proxy"`.
- Do **not** use for institutional flow analysis.
- Consider using GC futures volume as a proxy if exchange feed is available.

---

## H — BIAS PREVENTION

### H.1 — Look-Ahead Bias Prevention

**Definition:** Using data that would not have been available at time $t$.

**Prevention Measures:**

1. **Bar Confirmation Rule:** A bar at time $t$ is only available for analysis after $\tau_t + \text{bar\_duration}$. For M5, this means bar at 10:00 is confirmed at 10:05.

2. **Event Data Timing:** News event data (actual, revision) is only available after the release time. The system must not use actual values before the scheduled release.

3. **Revision Timing:** Revised values are only available after the revision timestamp. In backtesting, use only the first-release value until the revision timestamp.

4. **Macro Data Timing:** Daily macro values (DXY, yields) are only available after market close. Forward-fill only from the publication timestamp onward.

5. **Implementation:** In backtesting, enforce strict temporal ordering. Each bar $t$ can only access data from bars $\{1, ..., t\}$ and events with release timestamps $\leq \tau_t$.

### H.2 — Data Leakage Prevention

**Definition:** Information from the test set leaking into training.

**Prevention Measures:**

1. **Temporal Split:** Historical data must be split chronologically, never randomly.
2. **Walk-Forward:** Training window → Validation window → Test window, with no overlap.
3. **Parameter Invalidation:** Any parameter derived from test data must be recalculated per walk-forward window.

### H.3 — Survivorship Bias Prevention

**Definition:** Only analyzing instruments/assets that "survived" (still exist).

**Relevance:** Low for XAUUSD (single instrument, no delisting risk). However, broker-specific instrument changes (symbol renames, contract spec changes) must be tracked.

### H.4 — Repainting Prevention

**Definition:** Historical data that changes after the fact.

**Prevention Measures:**

1. **Snapshot Logging:** Once a bar is confirmed, its OHLCV values are frozen in the database.
2. **No Revision of Confirmed Bars:** If a bar is later found to be incorrect (rare broker data issues), it is flagged but not silently overwritten.
3. **Tick Data:** Tick data is append-only; no modification of historical ticks.
4. **News Revisions:** Revised news values are stored as a **separate record** with a revision timestamp, not overwriting the original.

### H.5 — Double Counting Prevention

**Definition:**同一信息被多个特征重复计算。

**Data-Level Prevention:**
- Tick Volume and Real Volume measure overlapping aspects. The system must not use both as independent features without explicit deduplication.
- DXY and USD-related news may overlap. Evidence Families (Phase 10) will handle this.

---

## I — BACKTESTABILITY

### I.1 — Historical Data Requirements

| Requirement | Specification |
|-------------|--------------|
| **Minimum History** | 5 years (quality-dependent, see I.2) |
| **Target History** | 10 years (quality-dependent) |
| **Quality Over Quantity** | Data must cover multiple market regimes; 5 years of high-quality data > 10 years of degraded data |
| **Primary Timeframe** | M5 |
| **Secondary Timeframes** | M15, H1, H4, D1 |
| **Tick Data (Raw)** | 90–180 days rolling retention |
| **Tick Features (Aggregated)** | 1 year retention |
| **Data Quality** | < 1% missing bars per timeframe |
| **Source** | MT5 historical export or equivalent |

### I.2 — Historical Depth Priorities

| Priority | Regime | Minimum Coverage | Importance |
|----------|--------|-----------------|------------|
| 1 | Trending (Bull & Bear) | 1+ year each | High — Core strategy validation |
| 2 | Range-bound | 6+ months | High — No-trade validation |
| 3 | High Volatility (crisis) | 3+ events | Critical — Risk validation |
| 4 | Low Volatility | 3+ months | Medium — Edge case testing |
| 5 | News-driven | 20+ high-impact events | Medium — News engine validation |
| 6 | Session-specific | All sessions represented | Medium — Session analysis |

**5 years minimum should cover:** COVID-2020, Inflation-2022, Banking-2023, Rate Hike Cycle, Rate Cut Cycle, Geopolitical events.

### I.3 — Backtest Data Pipeline

```
Raw MT5 Data
    ↓
Quality Check (missing bars, gaps, anomalies)
    ↓
Provenance Tagging (source, timestamp, quality flag)
    ↓
Alignment to Primary Timeframe
    ↓
Feature Engineering (per engine)
    ↓
Temporal Split (In-Sample / Out-of-Sample)
    ↓
Walk-Forward Windows
```

### I.4 — Data Quality Metrics

| Metric | Threshold | Action |
|--------|-----------|--------|
| Missing bars per day | < 5% | Flag, continue |
| Missing bars per day | 5–20% | Degrade analysis quality |
| Missing bars per day | > 20% | Reject that day |
| Spread anomalies (0 or >100 pips) | Any | Flag as data error |
| Price jumps (> 5% in 1 bar) | Any | Flag for review |
| Volume = 0 for > 3 consecutive bars | Any | Flag as low-liquidity period |
| Source freshness exceeded | Any | Degrade or skip dependent features |

---

## J — WHAT IS FIXED

### J.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Instrument | XAUUSD | System scope |
| Primary Timeframe | M5 | Balance between signal quality and execution speed |
| Analysis Timeframes | D1, H4, H1, M15, M5 | Multi-timeframe structure analysis |
| UTC Timestamps | All times in UTC (computed dynamically) | Avoid timezone ambiguity |
| Bar Confirmation | Bar available after close | Prevent look-ahead |
| Session Definitions | Timezone-aware with DST | Accurate session classification |
| Data Format | Pandas DataFrames | Existing codebase convention |
| Database Storage | PostgreSQL | Existing infrastructure |
| Volume Classification | Tick / Broker / Exchange / Composite | Clear taxonomy |
| Revision Handling | First-release + revision timestamp | Backtest integrity |
| Source Hierarchy | Primary → Secondary → Fallback | Resilience |

### J.2 — Not Fixed (Deferred to Engine Phases or Data Architecture)

| Item | Deferred To |
|------|-------------|
| Specific data source selection (DXY, Yields) | Data Architecture phase |
| Feature engineering | Phase 2–5 (per engine) |
| Score normalization | Phase 6 (GSI) |
| Probability computation | Phase 10 (Probability Engine) |
| Signal thresholds | Phase 11 (Setup Engine) |
| Risk parameters | Phase 12 (Risk Engine) |
| Volume composite weights | Phase 4 (Flow Engine) |
| Tick retention final value | Storage capacity analysis |

---

## K — WHAT REQUIRES TESTING

### K.1 — Hypotheses to Validate

| # | Hypothesis | Test Method | Expected Outcome |
|---|-----------|-------------|-----------------|
| H1 | MT5 provides reliable tick data for XAUUSD | Fetch 30 days of tick data; check completeness | > 95% tick availability during trading hours |
| H2 | DXY feed is available with < 5min delay via Primary source | Compare DXY timestamps with bar timestamps | Latency < 300 seconds |
| H3 | Treasury yield data is available at daily resolution via FRED | Fetch 1 year of yield data; check gaps | < 2% missing values |
| H4 | Session time definitions (timezone-aware) match broker behavior | Compare session boundaries with actual volume patterns | Volume peaks align with session opens |
| H5 | News event data (actual/forecast/previous) is consistently available | Fetch 6 months of events; check field completeness | > 90% of high-impact events have all fields |
| H6 | Revision data is available for key events (CPI, NFP) | Check CPI, NFP revisions over 1 year | Revisions available for > 80% of events |
| H7 | OHLCV data has < 1% missing bars on M5 | Fetch 1 year of M5 data; count gaps | < 1% missing |
| H8 | Tick volume correlates with real volume (where available) | Compute correlation coefficient | ρ > 0.6 |
| H9 | GC futures volume correlates with XAUUSD activity | Fetch GC volume; compute correlation with XAUUSD tick volume | ρ > 0.5 |
| H10 | DST transitions don't cause session misclassification | Test across 2 DST transitions | 0 misclassified bars |

### K.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Does the broker provide real volume for XAUUSD? | Test during Phase 1 implementation |
| Q2 | What is the actual spread distribution across sessions? | Analyze after data collection |
| Q3 | Are there broker-specific session time variations? | Verify with broker documentation |
| Q4 | Can we get Fed Funds implied rates from free data sources? | Research alternative sources (CME FedWatch) |
| Q5 | Is GC futures volume accessible via our data pipeline? | Test MT5 GC symbol availability |
| Q6 | What is the storage cost of 180 days tick data? | Calculate before finalizing retention |

---

## L — APPROVAL GATE

### The Phase 1 — Data Specification v2.0 is now complete.

---

## M — DATA AVAILABILITY TIMELINE

For every data point, we define:
- **Available to Bot:** When the system can first use it in real-time
- **Available in Backtest:** When the system can use it in historical simulation

### M.1 — Market Data Availability

| Data Point | Available to Bot | Available in Backtest | Notes |
|------------|-----------------|----------------------|-------|
| OHLCV (M5) | After bar close ($\tau_t + 5\text{min}$) | At bar timestamp $\tau_t$ | Standard bar confirmation |
| OHLCV (H1) | After bar close ($\tau_t + 60\text{min}$) | At bar timestamp $\tau_t$ | Standard bar confirmation |
| OHLCV (D1) | After bar close (end of day) | At bar timestamp $\tau_t$ | Standard bar confirmation |
| Tick Bid/Ask | Real-time (tick-by-tick) | At tick timestamp | No look-ahead |
| Tick Spread | Real-time | At tick timestamp | Derived from bid/ask |
| Tick Volume | After bar close | At bar timestamp | Aggregated from ticks |

### M.2 — Macro Data Availability

| Data Point | Available to Bot | Available in Backtest | Notes |
|------------|-----------------|----------------------|-------|
| DXY (Primary) | After publication (intraday if available) | At publication timestamp | Forward-filled |
| DXY (Secondary) | After daily close | At publication date | Daily value |
| US 2Y Yield | After FRED publication (~16:00 ET) | At publication timestamp | Daily only |
| US 10Y Yield | After FRED publication (~16:00 ET) | At publication timestamp | Daily only |
| Fed Funds Rate | At FOMC announcement | At announcement timestamp | Event-driven |
| Fed Funds Expected | If CME data available | At publication timestamp | Intraday if available |

### M.3 — News Data Availability

| Data Point | Available to Bot | Available in Backtest | Notes |
|------------|-----------------|----------------------|-------|
| Event Scheduled | At calendar publication (days/weeks ahead) | At calendar publication | Known in advance |
| Event Actual ($A_i$) | At release timestamp ($\text{release\_ts}_i$) | At release timestamp | **Never before** |
| Event Forecast ($F_i$) | Before release (consensus) | At calendar publication | Known in advance |
| Event Previous ($P_i$) | Before release | At previous release | First-release value only |
| Revision ($R_i$) | At revision timestamp ($\text{revision\_ts}_i$) | At revision timestamp | **Never before** |
| Surprise Z-score | After actual release | After actual release | Requires $A_i$ and $F_i$ |

### M.4 — Session Data Availability

| Data Point | Available to Bot | Available in Backtest | Notes |
|------------|-----------------|----------------------|-------|
| Session Open/Close | Pre-computed for each day | Pre-computed | Timezone-aware |
| DST State | At session boundary | At session boundary | Computed per bar date |
| Session Classification | At bar timestamp | At bar timestamp | Dynamic UTC conversion |

### M.5 — Critical Timeline Rules

```
RULE 1: No data point is used before its availability timestamp.
RULE 2: In backtesting, enforce strict temporal ordering.
RULE 3: Revisions are NEVER used before revision timestamp.
RULE 4: Forecasts are available before release; actuals are NOT.
RULE 5: Session classification uses the bar's date for DST computation.
```

---

## N — DATA PROVENANCE

Every data point entering the system must carry a provenance record.

### N.1 — Provenance Schema

```python
@dataclass(frozen=True)
class DataProvenance:
    """Provenance record for every data point."""
    source: str                    # "mt5", "fred", "metaapi", "csv"
    source_type: str               # "primary", "secondary", "fallback"
    ingestion_timestamp: datetime  # When the data was ingested
    original_timestamp: datetime   # When the data was originally published
    is_revised: bool               # Whether this value has been revised
    revision_timestamp: datetime | None  # When the revision occurred
    quality_flag: str              # "verified", "degraded", "estimated", "interpolated"
    freshness_seconds: float       # Age of data at ingestion time
```

### N.2 — Provenance Tracking Rules

| Rule | Description |
|------|-------------|
| P1 | Every bar, tick, event, and macro value must have a provenance record |
| P2 | Provenance is **immutable** once attached (frozen dataclass) |
| P3 | `ingestion_timestamp` is set at the moment data enters the system |
| P4 | `is_revised` and `revision_timestamp` track whether the value changed |
| P5 | `quality_flag` is set based on source reliability and freshness |
| P6 | Provenance is stored alongside data in the database |
| P7 | Backtesting must reconstruct provenance for each historical bar |

### N.3 — Provenance for News Events (Extended)

```python
@dataclass(frozen=True)
class NewsProvenance(DataProvenance):
    """Extended provenance for news events."""
    event_id: str                  # Unique event identifier
    release_timestamp: datetime    # Scheduled release time
    first_release_value: float | None  # Original value as released
    revised_value: float | None    # Revised value (if any)
    revision_timestamp: datetime | None  # When revision was published
    unit: str                      # "%", "K", "index", etc.
```

---

## O — DATA QUALITY SCORE

Each data source and individual data series receives a quality score.

### O.1 — Source-Level Quality Score

$$\text{QS}_{\text{source}} = w_1 \cdot \text{Completeness} + w_2 \cdot \text{Timeliness} + w_3 \cdot \text{Accuracy} + w_4 \cdot \text{Consistency}$$

Where:
- **Completeness** = (non-null values / total expected values) ∈ [0, 1]
- **Timeliness** = 1 - (average latency / max acceptable latency) ∈ [0, 1]
- **Accuracy** = (validated values / total values) ∈ [0, 1]
- **Consistency** = (values passing cross-check / total values) ∈ [0, 1]

**Default weights:** $w_1 = 0.35, w_2 = 0.25, w_3 = 0.25, w_4 = 0.15$

### O.2 — Quality Score Thresholds

| QS Range | Classification | System Action |
|----------|---------------|---------------|
| 0.90 – 1.00 | Excellent | Full weight |
| 0.75 – 0.89 | Good | Full weight, monitor |
| 0.60 – 0.74 | Adequate | Reduced weight (×0.7) |
| 0.40 – 0.59 | Poor | Minimal weight (×0.4) |
| 0.00 – 0.39 | Unacceptable | **Exclude from analysis** |

### O.3 — Per-Series Quality Tracking

Each data series (e.g., "DXY via FRED", "US 10Y Yield via Yahoo") is tracked independently:

| Series | Source | Completeness | Timeliness | Last Updated | QS |
|--------|--------|-------------|-----------|-------------|-----|
| DXY | Primary | TBD | TBD | TBD | TBD |
| US 2Y Yield | Secondary | TBD | TBD | TBD | TBD |
| US 10Y Yield | Secondary | TBD | TBD | TBD | TBD |
| XAUUSD OHLCV | MT5 | TBD | TBD | TBD | TBD |
| News Events | MetaAPI | TBD | TBD | TBD | TBD |

**Note:** Quality scores are computed **after data collection** in the implementation phase. The thresholds and weights above are initial parameters subject to testing.

### O.4 — Quality Score Usage

- **Engine Weighting:** Engines can use QS to reduce the influence of low-quality data.
- **Fallback Decisions:** If Primary QS drops below threshold, auto-switch to Secondary.
- **Logging:** Quality scores are logged for every decision point.
- **Backtesting:** QS can be used to simulate realistic data degradation.

---

## P — FINAL SPECIFICATION SUMMARY

### P.1 — Fixed Decisions

| # | Decision | Value |
|---|----------|-------|
| F1 | Instrument | XAUUSD |
| F2 | Primary Timeframe | M5 |
| F3 | Analysis Timeframes | D1, H4, H1, M15, M5 |
| F4 | Timestamp Convention | All UTC, computed dynamically |
| F5 | Bar Confirmation | Available after bar close |
| F6 | Session Model | Timezone-aware + DST |
| F7 | Volume Classification | Tick / Broker / Exchange / Composite |
| F8 | Revision Handling | First-release + revision timestamp |
| F9 | Provenance | Immutable record per data point |
| F10 | Quality Scoring | Per-source and per-series |
| F11 | Source Hierarchy | Primary → Secondary → Fallback |
| F12 | Backtest Temporal Rule | Strict chronological ordering |
| F13 | Tick Raw Retention | 90–180 days |
| F14 | Tick Feature Retention | 1 year |

### P.2 — Initial Parameters

| Parameter | Value | Phase |
|-----------|-------|-------|
| ATR_PERIOD | 14 | Phase 17 (Optimization) |
| RVOL_LOOKBACK | 20 | Phase 17 |
| MIN_SURPRISE_SAMPLES | 20 | Phase 10 (Probability) |
| DATA_FRESHNESS_THRESHOLD | 300s | Phase 12 (Risk) |
| HISTORY_MIN_YEARS | 5 | Fixed |
| HISTORY_TARGET_YEARS | 10 | Fixed |
| TICK_RAW_RETENTION | 90–180 days | Storage analysis |
| TICK_FEATURE_RETENTION | 365 days | Fixed |
| QS Excellent | ≥ 0.90 | Phase 17 |
| QS Threshold | ≥ 0.60 | Phase 17 |

### P.3 — Open Decisions

| # | Decision | Options | Resolution |
|---|----------|---------|-----------|
| O1 | DXY Primary Source | Broker / MetaAPI / FRED / Investing.com | Data Architecture phase |
| O2 | Yield Primary Source | Broker / FRED / Yahoo Finance | Data Architecture phase |
| O3 | News Primary Source | MetaAPI / Investing.com / ForexFactory / Custom | Data Architecture phase |
| O4 | GC Futures Access | MT5 GC symbol / External feed / Not available | Implementation test |
| O5 | Tick Raw Retention Final | 90 / 120 / 180 days | Storage analysis |
| O6 | Volume Composite Weights | Per source availability | Flow Engine (Phase 4) |

### P.4 — Data Dependencies

```
Market Data (MT5)
    ↓
├── Market Structure Engine (Phase 2)
├── Liquidity Engine (Phase 3)
├── Flow Engine (Phase 4)
├── Trend/Momentum/Volatility Engine (Phase 5)
│
Macro Data (DXY, Yields)
    ↓
├── Macro Engine (Phase 7)
├── Historical Engine (Phase 8)
│
News Data (Events, Revisions)
    ↓
├── News Engine (Phase 7)
├── Market Reaction Engine (Phase 10)
│
Session Data (Timezone-aware)
    ↓
├── All Engines (session context)
├── Risk Engine (Phase 12)
│
Historical Data (5–10 years)
    ↓
├── Backtest Engine (Phase 16)
├── Historical Similarity Engine (Phase 8)
```

### P.5 — Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| MT5 data gaps during high volatility | High | Multi-source fallback, gap detection |
| Session misclassification during DST | Medium | Timezone-aware with DST flag |
| Revision data not available in real-time | High | Strict temporal rules in backtest |
| Tick volume misinterpreted as institutional flow | High | Explicit labeling, source hierarchy |
| DXY/yield source unavailability | Medium | Primary → Secondary → Fallback |
| Storage cost of tick data | Medium | Retention policy, aggregation |
| Quality score miscalibration | Medium | Conservative thresholds, monitoring |

### P.6 — Bias Prevention Summary

| Bias | Prevention |
|------|-----------|
| Look-ahead | Bar confirmation, event timing, revision timing |
| Data leakage | Temporal split, walk-forward |
| Survivorship | Track instrument changes |
| Repainting | Snapshot logging, append-only tick data |
| Double counting | Volume source deduplication, Evidence Families |
| Revision misuse | First-release only until revision timestamp |

---

## L — APPROVAL GATE (Final)

### The Phase 1 — Data Specification v2.0 is now complete.

**What has been defined:**
1. ✅ All data fields across 5 domains (Market, Macro, News, Historical, Session)
2. ✅ Timezone-aware session definitions with DST handling
3. ✅ Source Hierarchy for all macro data (Primary → Secondary → Fallback)
4. ✅ Volume classification (Tick / Broker / Exchange / Composite) with explicit labels
5. ✅ News Data Schema with event_id, revision tracking, unit, source
6. ✅ Revision handling with first-release + revision timestamp
7. ✅ Data Availability Timeline for every feature
8. ✅ Data Provenance schema (immutable, per data point)
9. ✅ Data Quality Score (per source and per series)
10. ✅ Historical depth priorities (quality over quantity)
11. ✅ Storage analysis for tick data retention
12. ✅ Bias prevention measures
13. ✅ Backtestability requirements
14. ✅ Fixed vs. deferred decisions

---

### 📋 Points Requiring Your Approval:

1. **Timezone-Aware Sessions:** Are the timezone definitions correct? (Asia/Tokyo for Asian, Europe/London for London, America/New_York for NY)

2. **Source Hierarchy:** Is the Primary → Secondary → Fallback pattern acceptable for all macro data?

3. **Volume Classification:** Is the Tick/Broker/Exchange/Composite taxonomy clear and sufficient?

4. **Revision Handling:** Is the first-release + revision timestamp approach acceptable for backtest integrity?

5. **Tick Data Retention:** Is 90–180 days raw + 1 year features acceptable pending storage analysis?

6. **Quality Score:** Are the QS thresholds (≥0.90 Excellent, ≥0.60 minimum) acceptable?

7. **Data Availability Timeline:** Are the availability rules correct (especially for news actuals and revisions)?

8. **Open Decisions:** Are you comfortable deferring source selection to the Data Architecture phase?

---

**Please review and approve (or request modifications) before I proceed to Phase 2 — Market Structure Engine.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
