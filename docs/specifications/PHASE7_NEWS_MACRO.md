# PHASE 7 — NEWS / MACRO ENGINE

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the mathematical framework for **News and Macroeconomic Analysis** — measuring how economic events and macro data affect XAUUSD through the USD and Yield transmission channels.

This engine produces:
1. News Surprise computation (Z-score)
2. Directional impact mapping (News → USD → Yield → Gold)
3. Macro data integration (DXY, Treasury Yields, Fed Funds)
4. Market reaction measurement windows
5. Confirmation / Divergence / Anomaly detection

**Scope Boundary:**
- This engine handles **data ingestion and surprise computation**.
- Market Reaction analysis (post-news monitoring) is handled in Phase 10 (Probability Engine).
- The engine does **not** generate trading signals — it provides macro context.

---

## B — INPUTS

### B.1 — Required Data

| Data | Source | Reference |
|------|--------|-----------|
| Economic Events (calendar) | News Data Source (Phase 1) | Phase 1, Section O |
| Actual / Forecast / Previous / Revision | News Data Source | Phase 1, Section O |
| DXY | Macro Data Source (Phase 1 hierarchy) | Phase 1, Section C |
| US Treasury Yields (2Y, 10Y) | Macro Data Source | Phase 1, Section C |
| Fed Funds Rate | Macro Data Source | Phase 1, Section C |
| OHLCV (Gold) | MT5 | Phase 1 |

### B.2 — Parameters

| Parameter | Initial Value | Description |
|-----------|--------------|-------------|
| `MIN_SURPRISE_SAMPLES` | 20 | Minimum historical surprises for Z-score |
| `SURPRISE_LOOKBACK_YEARS` | 3 | Years of historical surprises to track |
| `REACTION_WINDOWS` | [0.5, 1, 5, 15, 30] | Minutes after release to measure |
| `NEWS_BLOCK_PRE_MIN` | 60 | Minutes before high-impact event to halt |
| `NEWS_BLOCK_POST_MIN` | 30 | Minutes after high-impact event to halt |
| `MACRO_FRESHNESS_THRESHOLD` | 3600 | Max age (seconds) for macro data |

---

## C — NEWS DATA SCHEMA

### C.1 — Event Record

Each economic event is stored as:

```python
@dataclass(frozen=True)
class NewsEvent:
    """Complete news event record."""
    event_id: str                      # Unique identifier
    name: str                          # "CPI m/m", "NFP", etc.
    currency: str                      # "USD", "EUR", etc.
    category: EventCategory            # CPI, NFP, FOMC, RATES, etc.
    importance: EventImpact            # 1=Low, 2=Medium, 3=High, 4=Critical
    
    # Timing
    release_timestamp: datetime        # Scheduled release (UTC)
    end_timestamp: datetime | None     # Event end (if applicable)
    
    # Values
    actual: float | None               # Actual reported value
    forecast: float | None             # Consensus forecast
    previous: float | None             # Previous value (as first released)
    previous_revised: float | None     # Revised previous value
    revision: float | None             # Revision amount
    revision_timestamp: datetime | None # When revision was published
    
    # Metadata
    unit: str                          # "%", "K", "index", "points"
    source: str                        # Data provider
    description: str | None            # Extended details
    
    # Provenance
    provenance: DataProvenance
```

### C.2 — Event Categories (XAUUSD-Relevant)

| Category | Events | Gold Impact Direction |
|----------|--------|---------------------|
| **CPI** | CPI m/m, Core CPI m/m, CPI y/y | Inflation → Gold ↑ (typically) |
| **NFP** | Non-Farm Payrolls, Unemployment Rate | Employment → USD ↑ → Gold ↓ |
| **FOMC** | FOMC Statement, Fed Rate Decision, Powell | Hawkish → USD ↑ → Gold ↓ |
| **RATES** | Interest Rate Decision | Rate ↑ → USD ↑ → Gold ↓ |
| **GDP** | GDP q/q, GDP y/y | Growth → USD ↑ → Gold ↓ |
| **PMI** | ISM Manufacturing, ISM Services | Growth → USD ↑ → Gold ↓ |
| **Retail** | Retail Sales m/m | Consumption → USD ↑ → Gold ↓ |
| **Claims** | Jobless Claims | Weakness → USD ↓ → Gold ↑ |
| **Yields** | Treasury Auction, Yield Announcement | Yield ↑ → USD ↑ → Gold ↓ |

### C.3 — Event Completeness Requirements

| Field | Required? | Fallback |
|-------|----------|---------|
| event_id | ✅ Yes | Generate UUID |
| name | ✅ Yes | — |
| currency | ✅ Yes | Default "USD" for US events |
| importance | ✅ Yes | Default LOW if unknown |
| release_timestamp | ✅ Yes | — |
| actual | ❌ No (may be missing) | Skip surprise computation |
| forecast | ❌ No (may be missing) | Use raw surprise if actual available |
| previous | ❌ No (may be missing) | Skip revision handling |
| unit | ❌ No | Infer from event name |

---

## D — NEWS SURPRISE COMPUTATION

### D.1 — Raw Surprise

$$S_i = A_i - F_i$$

Where:
- $A_i$ = Actual value
- $F_i$ = Forecast value

**If $F_i$ is unavailable:** $S_i = \text{None}$ (skip computation).

### D.2 — Surprise Z-Score

$$Z_i = \frac{A_i - F_i}{\sigma_{\text{surprise},i}}$$

Where:
- $\sigma_{\text{surprise},i}$ = Standard deviation of historical surprises for event $i$

**Minimum Sample Requirement:**

$$n_i \geq \text{MIN\_SURPRISE\_SAMPLES} = 20$$

If $n_i < 20$: Use raw surprise $S_i$ instead of Z-score.

### D.3 — Historical Surprise Database

For each event type $i$, maintain:

$$\mathcal{H}_i = \{S_{i,1}, S_{i,2}, ..., S_{i,n}\}$$

Where $S_{i,j}$ are historical surprises for event $i$.

**Update Rule:**
$$\mathcal{H}_i \leftarrow \mathcal{H}_i \cup \{S_{i,\text{new}}\}$$

**Retention:** Last 3 years of surprises (approximately 36 monthly CPI releases, 12 NFP releases, etc.).

### D.4 — Revision-Adjusted Surprise

When revision data is available:

$$Z_i^{\text{adj}} = \frac{A_i - (P_i + R_i)}{\sigma_{\text{surprise},i}}$$

Where:
- $P_i$ = Previous value (as first released)
- $R_i$ = Revision to previous value
- $P_i + R_i$ = Revised previous value

**Availability Rule (Phase 1 Compliance):**
- At release time: Use $Z_i$ (forecast-based)
- After revision timestamp: System may use $Z_i^{\text{adj}}$ for analysis
- **Never** use revised values before revision timestamp

### D.5 — Surprise Classification

| Z-Score | Classification | Interpretation |
|---------|---------------|---------------|
| > +2.0 | Extreme Positive Surprise | Actual much better than expected |
| +1.0 to +2.0 | Positive Surprise | Actual better than expected |
| -1.0 to +1.0 | In-Line | Within normal range |
| -2.0 to -1.0 | Negative Surprise | Actual worse than expected |
| < -2.0 | Extreme Negative Surprise | Actual much worse than expected |

---

## E — DIRECTIONAL IMPACT MAPPING

### E.1 — The Transmission Chain

Economic data affects Gold through a chain:

$$\text{News} \rightarrow \text{USD Strength} \rightarrow \text{Yield Direction} \rightarrow \text{Gold Price}$$

### E.2 — News → USD Direction

Not all news affects USD in the same direction:

| Event | Strong Actual → USD | Weak Actual → USD |
|-------|-------------------|-------------------|
| CPI (inflation) | ↑ (hawkish) | ↓ (dovish) |
| NFP (employment) | ↑ (strong economy) | ↓ (weak economy) |
| GDP (growth) | ↑ (strong economy) | ↓ (weak economy) |
| Retail Sales | ↑ (strong consumption) | ↓ (weak consumption) |
| ISM Manufacturing | ↑ (expansion) | ↓ (contraction) |
| Jobless Claims | ↓ (fewer claims = strong) | ↑ (more claims = weak) |
| FOMC (hawkish) | ↑ (higher rates) | ↓ (lower rates) |

**USD Direction Function:**

$$\text{USD}_{\text{dir},i} = \begin{cases}
+1 & \text{if strong actual → USD strengthens (e.g., NFP, GDP)} \\
-1 & \text{if strong actual → USD weakens (e.g., Jobless Claims)} \\
\text{context-dependent} & \text{if direction depends on other factors}
\end{cases}$$

### E.3 — USD → Gold Direction

USD and Gold have an **inverse relationship** (typically):

$$\text{Gold}_{\text{dir}} = -\text{USD}_{\text{dir}}$$

**Exception:** During risk-off events, both USD and Gold may rise (safe haven).

### E.4 — USD → Yield Direction

USD strength typically correlates with higher yields:

$$\text{Yield}_{\text{dir}} \approx \text{USD}_{\text{dir}}$$

**Exception:** Flight-to-safety may push yields down while USD rises.

### E.5 — Combined Direction Table

| Event Type | Strong Actual | USD Dir | Yield Dir | Gold Dir (Expected) |
|-----------|--------------|---------|-----------|-------------------|
| CPI (high) | Higher inflation | ↑ | ↑ | ↓ (rate hike fear) |
| NFP (strong) | More jobs | ↑ | ↑ | ↓ (strong economy) |
| GDP (strong) | Growth | ↑ | ↑ | ↓ (risk-on) |
| FOMC (hawkish) | Higher rates | ↑ | ↑ | ↓ (yield appeal) |
| Jobless Claims (low) | Fewer claims | ↑ | ↑ | ↓ (strong economy) |
| ISM (high) | Expansion | ↑ | ↑ | ↓ (risk-on) |
| Retail Sales (high) | Strong consumption | ↑ | ↑ | ↓ (risk-on) |

**Note:** These are **expected** directions. The Market Reaction Engine (Phase 10) measures **actual** directions, which may differ.

---

## F — MACRO DATA INTEGRATION

### F.1 — DXY Analysis

#### DXY Trend

$$\text{DXY}_{\text{trend}} = \text{sign}(\text{EMA}(D, 20) - \text{EMA}(D, 50))$$

Where $D$ = DXY values.

#### DXY Momentum

$$\text{DXY}_{\text{mom}} = \frac{D_t - D_{t-5}}{D_{t-5}} \times 100$$

#### DXY → Gold Implication

$$\text{Gold}_{\text{from\_DXY}} = -\text{DXY}_{\text{trend}} \times |\text{DXY}_{\text{mom}}|$$

**Interpretation:**
- DXY rising → Gold pressure down
- DXY falling → Gold pressure up

### F.2 — Treasury Yield Analysis

#### Yield Spread (10Y - 2Y)

$$\text{Spread}_t = Y_{10,t} - Y_{2,t}$$

**Interpretation:**
- Spread > 0: Normal curve (economic expansion)
- Spread < 0: Inverted curve (recession risk)
- Spread widening: Steepening (growth预期)
- Spread narrowing: Flattening ( slowdown预期)

#### Yield Trend

$$\text{Yield}_{\text{trend}} = \text{sign}(\text{EMA}(Y_{10}, 20) - \text{EMA}(Y_{10}, 50))$$

#### Yield → Gold Implication

$$\text{Gold}_{\text{from\_yield}} = -\text{Yield}_{\text{trend}} \times |Y_{10,t} - Y_{10,t-5}|$$

**Interpretation:**
- Yields rising → Gold pressure down (opportunity cost)
- Yields falling → Gold pressure up (safe haven)

### F.3 — Fed Funds Analysis

#### Rate Direction

$$\text{FFR}_{\text{dir}} = \begin{cases}
+1 & \text{if rate hike expected/announced} \\
-1 & \text{if rate cut expected/announced} \\
0 & \text{if unchanged}
\end{cases}$$

#### Policy Bias (from FOMC statement)

$$\text{Bias} = \begin{cases}
\text{Hawkish} & \text{if statement signals tighter policy} \\
\text{Dovish} & \text{if statement signals looser policy} \\
\text{Neutral} & \text{if no clear signal}
\end{cases}$$

**Detection:** Keyword analysis of FOMC statement:
- Hawkish: "inflation", "tightening", "restrictive", "higher for longer"
- Dovish: "accommodative", "supportive", "patient", "data-dependent"

### F.4 — Macro Score

$$\text{MacroScore} = w_1 \cdot \text{DXY}_{\text{score}} + w_2 \cdot \text{Yield}_{\text{score}} + w_3 \cdot \text{FFR}_{\text{score}}$$

| Component | Weight | Description |
|-----------|--------|-------------|
| DXY | 0.40 | Dollar strength |
| Yields | 0.35 | Interest rate environment |
| Fed Funds | 0.25 | Policy direction |

$$\text{MacroScore} \in [-100, +100]$$

**Direction:** Positive = Gold bullish (weak USD, low yields), Negative = Gold bearish (strong USD, high yields).

---

## G — MARKET REACTION WINDOWS

### G.1 — Reaction Measurement Points

After a news release at time $t_0$, measure market reaction at:

| Window | Time | Purpose |
|--------|------|---------|
| $W_1$ | $t_0 + 30\text{sec}$ | Immediate reaction |
| $W_2$ | $t_0 + 1\text{min}$ | Initial absorption |
| $W_3$ | $t_0 + 5\text{min}$ | First wave complete |
| $W_4$ | $t_0 + 15\text{min}$ | Secondary reaction |
| $W_5$ | $t_0 + 30\text{min}$ | Digestion complete |

### G.2 — Reaction Metrics

For each window $W_k$, compute:

$$\Delta \text{Gold}_k = \frac{C_{W_k} - C_{t_0}}{C_{t_0}} \times 100$$

$$\Delta \text{DXY}_k = \frac{D_{W_k} - D_{t_0}}{D_{t_0}} \times 100$$

$$\Delta \text{Yield}_k = Y_{10,W_k} - Y_{10,t_0}$$

### G.3 — Reaction Classification

| Gold | DXY | Yield | Classification |
|------|-----|-------|---------------|
| ↑ | ↓ | ↓ | **Confirmation** — Expected direction |
| ↑ | ↑ | ↑ | **Divergence** — USD and Gold both up (safe haven) |
| ↑ | ↓ | ↑ | **Partial Confirmation** — Mixed signals |
| ↓ | ↑ | ↑ | **Confirmation** — Expected direction |
| ↓ | ↓ | ↓ | **Divergence** — Both falling |
| No move | No move | No move | **No Reaction** — Data was in-line |
| Large move | No move | No move | **Gold-Specific** — Not macro-driven |
| Reversal after initial move | — | — | **Overreaction → Reversal** |

### G.4 — Anomaly Detection

$$\text{Anomaly} \iff \text{Expected Direction} \neq \text{Actual Direction}$$

**Example:**
- CPI Higher than expected → Expected: USD ↑, Gold ↓
- Actual: USD ↓, Gold ↑
- **Classification:** Market Reaction Anomaly

**Logging:** All anomalies are recorded with:
- Event details
- Expected vs. actual directions
- Magnitude of divergence
- Market context (regime, GSI, etc.)

### G.5 — Response Time Analysis

$$\text{ResponseTime} = \min_k \{W_k : |\Delta \text{Gold}_k| > \text{threshold}\}$$

Where threshold = 0.10% (10 pips for XAUUSD).

**Interpretation:**
- Fast response (< 1 min): Market had strong consensus
- Slow response (> 5 min): Market digesting, may be uncertain
- No response: Data was fully anticipated

---

## H — NEWS IMPACT SCORING

### H.1 — News Impact Score

$$\text{NewsImpact}_i = \text{Importance}_i \times |Z_i|$$

Where:
- $\text{Importance}_i \in \{1, 2, 3, 4\}$ (from EventImpact enum)
- $|Z_i|$ = absolute surprise Z-score

$$\text{NewsImpact}_i \in [0, 8]$$

### H.2 — Composite News Score

For all events in a time window (e.g., today):

$$\text{NewsScore}_t = \sum_{i \in \text{active}} \text{NewsImpact}_i \times \text{USD}_{\text{dir},i} \times (-1)$$

Where the $(-1)$ converts USD direction to Gold direction.

$$\text{NewsScore}_t \in [-100, +100]$$

**Normalization:** Divide by maximum possible impact and scale to [-100, +100].

### H.3 — News Score Interpretation

| Score | Interpretation |
|-------|---------------|
| +60 to +100 | Strong bullish news for Gold |
| +30 to +59 | Moderately bullish news |
| -30 to +30 | Neutral or mixed news |
| -59 to -30 | Moderately bearish news |
| -100 to -60 | Strong bearish news for Gold |

---

## I — EDGE CASES

### I.1 — Missing Data

| Scenario | Handling |
|----------|----------|
| Actual not released yet | Skip surprise; use forecast as baseline |
| Forecast not available | Use raw surprise (A - P) if previous available |
| Revision not available | Use first-release value |
| DXY feed fails | Skip DXY-dependent features |
| Yield data unavailable | Skip yield features |
| Multiple events same time | Sum impacts; highest importance dominates |

### I.2 — Data Conflicts

| Scenario | Handling |
|----------|----------|
| CPI high + NFP low | Mixed signals; compute net NewsScore |
| FOMC dovish + CPI high | Contradictory; flag as `conflicting_news` |
| Revision changes sign of surprise | Log both original and revised surprises |

### I.3 — Timing Issues

| Scenario | Handling |
|----------|----------|
| Event released early | Use actual release timestamp |
| Event released late | Use scheduled timestamp for blocking; actual for surprise |
| Revision after trading hours | Store; apply at next session open |

---

## J — BIAS PREVENTION

### J.1 — Look-Ahead Bias

**Prevention:**
1. Actual values used only after release_timestamp
2. Revisions used only after revision_timestamp
3. In backtesting, strict temporal ordering enforced

### J.2 — Data Leakage

**Prevention:**
1. Historical surprises are from past events only
2. Walk-forward calibration of surprise distributions
3. No future event information in training

### J.3 — Overreaction Bias

**Prevention:**
1. Market reaction measured at multiple windows
2. Initial reaction may be overreaction — wait for digestion
3. Anomaly detection flags unexpected reactions

---

## K — BACKTESTABILITY

### K.1 — Backtest Requirements

| Requirement | Implementation |
|-------------|---------------|
| Event timing | Use release_timestamp strictly |
| Revision timing | Use revision_timestamp strictly |
| Surprise computation | Only from available historical data |
| Macro data timing | Forward-fill from publication timestamp |
| Reaction windows | Simulate using bar data at each window |

### K.2 — Backtest Data Flow

```
News Calendar (historical)
    ↓
Event Records (with actual/forecast/previous/revision)
    ↓
Surprise Computation (Z-score)
    ↓
Directional Mapping (News → USD → Gold)
    ↓
Macro Data (DXY, Yields, FFR)
    ↓
Macro Score
    ↓
News Score (composite)
    ↓
Reaction Measurement (at each window)
    ↓
Anomaly Detection
    ↓
Final News/Macro Output
```

---

## L — WHAT IS FIXED

### L.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Min Surprise Samples | 20 | CLT approximation |
| Surprise Lookback | 3 years | Enough history for Z-score |
| Reaction Windows | 30s, 1m, 5m, 15m, 30m | Captures full reaction cycle |
| News Block Pre (High) | 60 min | Safety buffer before event |
| News Block Post (High) | 30 min | Digestion time |
| Macro Weights | DXY 40%, Yields 35%, FFR 25% | Dollar most important |
| USD→Gold Direction | Inverse (typical) | With anomaly detection |

### L.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal surprise samples | Phase 17 (Optimization) |
| Reaction window thresholds | Phase 17 |
| Macro weight optimization | Phase 17 |
| Keyword analysis for FOMC | Phase 7 implementation |
| Specific event direction mapping | Phase 7 implementation |

---

## M — WHAT REQUIRES TESTING

### M.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | Z-score > 1.5 predicts significant Gold moves | Statistical test | > 60% of extreme surprises cause > 10 pip move |
| H2 | DXY and Gold are inversely correlated | Correlation check | ρ < -0.5 |
| H3 | Yields and Gold are inversely correlated | Correlation check | ρ < -0.3 |
| H4 | News direction mapping is accurate | Backtest directional predictions | > 55% correct |
| H5 | 30-min window captures full reaction | Compare 30m vs. 60m reactions | 95% of reaction captured by 30m |
| H6 | Anomaly detection identifies genuine anomalies | Manual review | > 70% of flagged anomalies are genuine |

### M.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | What is the optimal minimum surprise sample size? | Test range [10–30] |
| Q2 | Should different events have different reaction windows? | Test per-event calibration |
| Q3 | How to handle overnight gaps in macro data? | Test gap handling approaches |
| Q4 | Can we predict anomaly direction from market context? | Feature importance analysis |

---

## N — OUTPUT SCHEMA

### N.1 — News Output per Event

```python
@dataclass(frozen=True)
class NewsOutput:
    """News analysis output for a single event."""
    event: NewsEvent
    
    # Surprise
    raw_surprise: float | None
    surprise_zscore: float | None
    revision_adjusted_zscore: float | None
    surprise_classification: str         # "extreme_positive", "positive", "inline", etc.
    
    # Direction
    usd_direction: int                   # +1, -1, 0
    gold_direction_expected: int         # +1, -1, 0
    yield_direction_expected: int        # +1, -1, 0
    
    # Impact
    news_impact: float                   # [0, 8]
    news_score_contribution: float       # Contribution to composite NewsScore
    
    # Provenance
    provenance: DataProvenance
```

### N.2 — Macro Output per Bar

```python
@dataclass(frozen=True)
class MacroOutput:
    """Macro data analysis output for a single bar."""
    timestamp: datetime
    
    # DXY
    dxy_value: float | None
    dxy_trend: str | None               # "bullish", "bearish", "neutral"
    dxy_momentum: float | None
    dxy_score: float                     # [-100, +100]
    dxy_source: str                      # "primary", "secondary", "fallback"
    dxy_freshness: float                 # Seconds since publication
    
    # Yields
    yield_2y: float | None
    yield_10y: float | None
    yield_spread: float | None           # 10Y - 2Y
    yield_trend: str | None
    yield_score: float                   # [-100, +100]
    yield_source: str
    yield_freshness: float
    
    # Fed Funds
    ffr_value: float | None
    ffr_direction: str | None            # "hike", "cut", "unchanged"
    policy_bias: str | None              # "hawkish", "dovish", "neutral"
    ffr_score: float                     # [-100, +100]
    
    # Composite
    macro_score: float                   # [-100, +100]
    macro_direction: str                 # "gold_bullish", "gold_bearish", "neutral"
    
    # Provenance
    provenance: DataProvenance
```

### N.3 — Composite News/Macro Output

```python
@dataclass(frozen=True)
class NewsMacroOutput:
    """Combined News + Macro output."""
    timestamp: datetime
    
    # Active Events
    active_events: list[NewsOutput]
    upcoming_events: list[NewsOutput]
    recent_events: list[NewsOutput]
    
    # Scores
    news_score: float                    # [-100, +100]
    macro_score: float                   # [-100, +100]
    combined_score: float                # [-100, +100]
    
    # Risk Status
    is_news_blocking: bool               # Trading blocked due to event
    blocking_event: NewsEvent | None
    news_risk_multiplier: float          # [0, 1]
    
    # Anomalies
    anomalies: list[NewsAnomaly]
    
    # Provenance
    provenance: DataProvenance
```

---

## O — DECISION OUTPUT

### O.1 — Per-Event Output

```
[13:30] CPI m/m Released
  Actual: 0.4% | Forecast: 0.3% | Previous: 0.2%
  Surprise: +0.1% | Z-Score: +1.35
  Classification: Positive Surprise
  USD Direction: +1 (Stronger)
  Gold Expected: -1 (Weaker)
  Impact: 3.2 (High × Surprise)
  
  Reaction @ 30s: Gold -8 pips, DXY +0.12%
  Reaction @ 5m:  Gold -15 pips, DXY +0.25%
  Reaction @ 30m: Gold -12 pips, DXY +0.18%
  Classification: Confirmation (Expected direction)
```

### O.2 — Daily Macro Summary

```
=== NEWS/MACRO SUMMARY ===
Active Events: 0
Upcoming: FOMC (2h 15min)
Recent: CPI (30min ago, Surprise +1.35σ)

=== MACRO SCORES ===
DXY: 104.85 (+0.25%) | Trend: Bullish | Score: +45
10Y Yield: 4.35% (+0.03%) | Trend: Rising | Score: -35
FFR: 5.25% | Bias: Hawkish | Score: -40

Macro Score: +8 (Neutral-Slightly Bullish Gold)
Combined News+Macro: -15 (Slightly Bearish Gold)
```

---

## P — APPROVAL GATE

### The Phase 7 — News / Macro Engine specification is now complete.

**Summary of what is defined:**

1. ✅ News Event schema with all fields (event_id, actual, forecast, previous, revision, etc.)
2. ✅ News Surprise Z-score formula with minimum sample requirement
3. ✅ Revision handling with temporal rules
4. ✅ Directional impact mapping (News → USD → Yield → Gold)
5. ✅ DXY analysis (trend, momentum, Gold implication)
6. ✅ Yield analysis (spread, trend, Gold implication)
7. ✅ Fed Funds analysis (direction, policy bias)
8. ✅ Macro Score composition
9. ✅ Market reaction windows (30s, 1m, 5m, 15m, 30m)
10. ✅ Reaction classification (Confirmation, Divergence, Anomaly)
11. ✅ News Impact scoring
12. ✅ Composite News Score
13. ✅ Edge cases and handling
14. ✅ Bias prevention measures
15. ✅ Backtest requirements
16. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **News Schema:** Are all required fields included? Missing any?

2. **Surprise Z-Score:** Is the minimum sample of 20 appropriate?

3. **Direction Mapping:** Are the News → USD → Gold directions correct for all event types?

4. **Macro Weights:** DXY 40%, Yields 35%, FFR 25% — acceptable?

5. **Reaction Windows:** 30s, 1m, 5m, 15m, 30m — appropriate for XAUUSD?

6. **Blocking Rules:** 60min pre / 30min post for high-impact events — appropriate?

7. **Anomaly Detection:** Is the expected vs. actual direction comparison sufficient?

8. **FOMC Keyword Analysis:** Is this approach feasible, or should we use a simpler method?

---

**Please review and approve (or request modifications) before I proceed to Phase 8 — Historical Engine.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
