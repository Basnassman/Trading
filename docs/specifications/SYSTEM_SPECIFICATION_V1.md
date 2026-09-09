# SYSTEM SPECIFICATION V1.0

## XAUUSD Quantitative Trading System
## Unified Mathematical & Engineering Specification

**Version:** 1.0.0-RESOLVED
**Date:** 2026-08-31
**Status:** CRITICAL ISSUES RESOLVED — PENDING ARCHITECTURE REVIEW
**Classification:** Pre-Implementation — No Code

---

# PART I — RESOLVED CRITICAL ISSUES

---

## 1. C1 — GOLD SMART INDEX (GSI) — RESOLVED

### 1.1 Official Naming

**Name:** Gold Smart Index
**Acronym:** GSI
**Version:** 1.0

The name "General Safety Index" is **INVALID** and must not appear in any specification, code, or documentation. GSI is not a safety metric — it is a directional evidence composite.

### 1.2 Formal Definition

$$\text{GSI}: \mathbb{R}^{n_t} \rightarrow [-100, +100]$$

Where $n_t$ is the number of available feature engines at time $t$.

### 1.3 What GSI Measures

GSI measures the **aggregate directional evidence** across multiple independent(ish) analytical engines for XAUUSD at a given point in time.

| Property | Definition |
|----------|-----------|
| **Direction** | Positive = bullish evidence aggregate, Negative = bearish evidence aggregate |
| **Strength** | Magnitude = how strong the aggregate evidence is |
| **Scope** | Price structure, volume flow, trend, momentum, volatility, price action |
| **Timeframe** | Per-bar on primary timeframe (M5) |
| **Nature** | Composite diagnostic index — NOT a probability |

### 1.4 What GSI Does NOT Measure

| Property | Why Not |
|----------|---------|
| **NOT a Probability** | GSI does not output "X% chance of success". Probability is computed in Phase 10 using Evidence Families. |
| **NOT a Risk Score** | GSI does not measure risk. Risk is computed in Phase 12. |
| **NOT a Safety Score** | GSI does not measure "safety" of a trade. Safety is assessed by Phase 14 (No-Trade). |
| **NOT a Signal** | GSI does not directly generate entry/exit signals. It is contextual input. |
| **NOT Static** | GSI weights are initial; optimization in Phase 17. |

### 1.5 GSI Role in Architecture

GSI serves as a **Diagnostic Index** and **Context Variable**:

```
Feature Engines (Phase 2-5)
    ↓
Evidence Families → Probability Engine (Phase 10)
    ↓
                    GSI (Diagnostic / Context / Filter)
                    ├── Human-readable aggregate
                    ├── Setup Engine filter (Phase 11)
                    ├── Decision Engine context (Phase 15)
                    └── Feedback/Research analysis (Phase 21)
```

**Critical Rule:** GSI is **NEVER** an input to the Probability Engine. GSI and the Probability Engine receive the same underlying features but process them independently.

### 1.6 GSI Formula

$$\text{GSI}_{\text{raw}} = \sum_{i=1}^{6} w_i \cdot S_i$$

Where:

| Component $i$ | Symbol | Source | Weight $w_i$ | Range |
|---------------|--------|--------|-------------|-------|
| Market Structure | $S_{\text{struct}}$ | Phase 2 | 0.25 | [-100, +100] |
| Flow | $S_{\text{flow}}$ | Phase 4 | 0.20 | [-100, +100] |
| Trend | $S_{\text{trend}}$ | Phase 5 | 0.15 | [-100, +100] |
| Momentum | $S_{\text{momentum}}$ | Phase 5 | 0.15 | [-100, +100] |
| Price Action | $S_{\text{PA}}$ | Derived | 0.15 | [-100, +100] |
| Volatility | $S_{\text{volatility}}$ | Phase 5 | 0.10 | [-100, +100] |

$$\sum_{i=1}^{6} w_i = 1.0$$

### 1.7 GSI Normalization

$$\text{GSI} = \text{clamp}\left(\text{EMA}\left(\text{GSI}_{\text{raw}}, n=3\right), -100, +100\right)$$

Where EMA smoothing reduces noise:

$$\text{GSI}_{\text{smooth},t} = \alpha \cdot \text{GSI}_{\text{raw},t} + (1 - \alpha) \cdot \text{GSI}_{\text{smooth},t-1}$$

$$\alpha = \frac{2}{n+1} = \frac{2}{4} = 0.5$$

### 1.8 GSI Interpretation

| GSI Range | Direction | Confidence | Interpretation |
|-----------|-----------|------------|---------------|
| +60 to +100 | Strong Bullish | High | Strong aggregate bullish evidence |
| +30 to +60 | Bullish | Moderate | Moderate bullish evidence |
| +10 to +30 | Weak Bullish | Low | Slight bullish bias |
| -10 to +10 | Neutral | Negligible | No net directional evidence |
| -30 to -10 | Weak Bearish | Low | Slight bearish bias |
| -60 to -30 | Bearish | Moderate | Moderate bearish evidence |
| -100 to -60 | Strong Bearish | High | Strong aggregate bearish evidence |

$$\text{GSI}_{\text{confidence}} = \frac{|\text{GSI}|}{100} \in [0, 1]$$

### 1.9 GSI Dependency Graph

```
Phase 2 (Structure Score) ──→ GSI
Phase 4 (Flow Score) ────────→ GSI
Phase 5 (Trend Score) ───────→ GSI
Phase 5 (Momentum Score) ────→ GSI
Derived (Price Action Score) ─→ GSI
Phase 5 (Volatility Score) ──→ GSI

Phase 2 (Structure Score) ──→ Evidence Family "Structure" ──→ Probability Engine
Phase 3 (Liquidity Score) ──→ Evidence Family "Liquidity" ──→ Probability Engine
Phase 4 (Flow Score) ────────→ Evidence Family "Flow" ───────→ Probability Engine
Phase 5 (Trend Score) ───────→ Evidence Family "Trend/Mom" ──→ Probability Engine
Phase 5 (Momentum Score) ────→ Evidence Family "Trend/Mom" ──→ Probability Engine
Phase 7 (News/Macro) ────────→ Evidence Family "Macro" ──────→ Probability Engine
Phase 8 (Historical) ────────→ Evidence Family "Historical" ─→ Probability Engine
Phase 5 (Volatility Score) ──→ Evidence Family "Volatility" ─→ Probability Engine
Phase 9 (Regime) ────────────→ Evidence Family "Context" ────→ Probability Engine

⚠️ GSI is NOT connected to Probability Engine ⚠️
```

---

## 2. C2 — INSTITUTIONAL FLOW PROXY — RESOLVED

### 2.1 Core Principle

Tick Volume is **NOT** Institutional Flow. The system must never label tick volume as institutional order flow. Instead, we construct an **Institutional Flow Proxy** through a layered inference architecture.

### 2.2 Data Classification Taxonomy

| Level | Label | Definition | Example |
|-------|-------|-----------|---------|
| **Observed** | Directly measured from market data | Tick count, OHLCV, spread |
| **Inferred** | Derived from observed data through mathematical transformation | RVOL, BP/SP, CE, Absorption |
| **Proxy** | Inferred signal that approximates an unobservable concept | Institutional Flow Proxy |
| **Unavailable** | Data that cannot be obtained from available sources | Actual order book, institutional positions |

### 2.3 Layered Architecture

```
LAYER 1: OBSERVED DATA
├── Tick Volume (V_tick)          — Count of price changes per bar
├── OHLCV                         — Open, High, Low, Close, Volume
├── Bid/Ask Spread                — S_t = Ask_t - Bid_t
├── Tick Data (bid/ask per tick)  — If available from MT5
└── Gold Futures Volume (V_GC)    — If GC symbol available on MT5

LAYER 2: FLOW FEATURES (Inferred)
├── Relative Volume (RVOL)        — V_t / EMA(V, 20)
├── Buying Pressure (BP)          — (C-L)/(H-L) × V
├── Selling Pressure (SP)         — (H-C)/(H-L) × V
├── Candle Efficiency (CE)        — |C-O|/(H-L)
├── Volume Acceleration (VA)      — (V_t - V_{t-1}) / V_{t-1}
├── MV Relationship               — sign(ΔP) × sign(ΔV)
├── Absorption Proxy              — High RVOL + Small Range + Near Level
├── Exhaustion Proxy              — Extreme RVOL + Small Range + At Extreme
└── Sweep Interaction             — RVOL during sweep bar

LAYER 3: INSTITUTIONAL FLOW PROXY
├── Flow Score                    — Weighted combination of Layer 2 features
├── Flow State Classification     — Buying/Selling/Absorption/Exhaustion/Continuation
├── Proxy Confidence Level        — Based on data quality and feature availability
└── Gold Futures Reference        — Independent validation (if available)
```

### 2.4 Flow Features — Mathematical Definitions

#### F1: Relative Volume (RVOL)

$$\text{RVOL}_t = \frac{V_t}{\text{EMA}(V, 20)_t}$$

**Interpretation:** Volume relative to recent average. RVOL > 1.0 = above average activity.

**Data Quality:** OBSERVED (directly from tick/broker volume).

#### F2: Buying Pressure (BP)

$$\text{BP}_t = \frac{C_t - L_t}{H_t - L_t} \times V_t$$

**Interpretation:** Proportion of bar range captured by buyers, weighted by volume.

**Data Quality:** INFERRED (derived from OHLCV + Volume).

**Edge Case:** If $H_t = L_t$ (doji), $\text{BP}_t = 0.5 \times V_t$.

#### F3: Selling Pressure (SP)

$$\text{SP}_t = \frac{H_t - C_t}{H_t - L_t} \times V_t$$

**Property:** $\text{BP}_t + \text{SP}_t = V_t$ (decomposition, not independent measures).

#### F4: Candle Efficiency (CE)

$$\text{CE}_t = \frac{|C_t - O_t|}{H_t - L_t}$$

**Interpretation:** How effectively price moved through the bar range. CE = 1.0 means full-range bar; CE = 0.0 means doji.

**Data Quality:** INFERRED.

#### F5: Volume Acceleration (VA)

$$\text{VA}_t = \frac{V_t - V_{t-1}}{V_{t-1}}$$

**Interpretation:** Rate of change in volume. Positive = accelerating, Negative = decelerating.

#### F6: MV Relationship

$$\text{MV}_{\text{type},t} = \text{sign}(\Delta P_t) \times \text{sign}(\Delta V_t)$$

Where $\Delta P_t = C_t - C_{t-1}$, $\Delta V_t = V_t - V_{t-1}$.

| $\Delta P$ | $\Delta V$ | Relationship | Interpretation |
|------------|------------|-------------|---------------|
| + | + | Confirmation | Strong bullish |
| + | - | Divergence | Weak bullish |
| - | + | Confirmation | Strong bearish |
| - | - | Divergence | Weak bearish |

#### F7: Absorption Proxy

$$\text{Absorption}_{\text{proxy},t} \iff \text{RVOL}_t > 1.5 \wedge \frac{H_t - L_t}{\text{ATR}_{14}} < 0.5 \wedge \text{NearLevel}(C_t, \mathcal{L})$$

Where $\mathcal{L}$ = active liquidity levels from Phase 3.

**Direction:**

$$\text{AbsDir}_t = \begin{cases} \text{BID\_ABSORPTION} & \text{if } C_t > O_t \text{ (selling pressure absorbed)} \\ \text{ASK\_ABSORPTION} & \text{if } C_t < O_t \text{ (buying pressure absorbed)} \end{cases}$$

**Data Quality:** INFERRED (proxy — true absorption requires order book data).

#### F8: Exhaustion Proxy

$$\text{Exhaustion}_{\text{proxy},t} \iff \text{RVOL}_t > 2.5 \wedge \frac{H_t - L_t}{\text{ATR}_{14}} < 0.3 \wedge \text{AtPriceExtreme}(C_t)$$

**Data Quality:** INFERRED (proxy — exhaustion is context-dependent).

### 2.5 Institutional Flow Proxy Score

$$\text{IFP}_{\text{score}} = w_1 \cdot \text{Pressure}_{\text{score}} + w_2 \cdot \text{Efficiency}_{\text{score}} + w_3 \cdot \text{RVOL}_{\text{score}} + w_4 \cdot \text{Acceleration}_{\text{score}} + w_5 \cdot \text{MV}_{\text{score}}$$

| Component | Weight | Range | Data Quality |
|-----------|--------|-------|-------------|
| Net Pressure Score | 0.30 | [-100, +100] | INFERRED |
| Candle Efficiency Score | 0.25 | [-100, +100] | INFERRED |
| RVOL Score | 0.20 | [-100, +100] | OBSERVED→INFERRED |
| Volume Acceleration Score | 0.10 | [-100, +100] | INFERRED |
| MV Relationship Score | 0.15 | [-100, +100] | INFERRED |

$$\text{IFP}_{\text{score}} \in [-100, +100]$$

**Direction:** Positive = net buying pressure, Negative = net selling pressure.

### 2.6 Proxy Confidence Level

$$\text{IFP}_{\text{confidence}} = f(\text{DataQuality}, \text{FeatureAvailability}, \text{VolumeSourceType})$$

| Condition | Confidence | Level |
|-----------|-----------|-------|
| Broker real volume + all features available | 0.90 | HIGH |
| Tick volume + all features available | 0.70 | MODERATE |
| Tick volume + some features missing | 0.50 | LOW |
| Only OHLCV (no volume) | 0.20 | VERY LOW |
| Volume data unavailable | 0.00 | UNAVAILABLE |

**Data Quality Label:**

$$\text{IFP}_{\text{quality}} = \begin{cases} \text{OBSERVED} & \text{if broker/exchange volume available} \\ \text{INFERRED} & \text{if tick volume used as proxy} \\ \text{UNAVAILABLE} & \text{if no volume data} \end{cases}$$

### 2.7 Gold Futures Reference (Independent Validation)

If Gold Futures (GC) volume is available via MT5:

$$\text{GC}_{\text{correlation}} = \text{Corr}(\text{IFP}_{\text{score}}, \text{GC}_{\text{direction}}, \text{window}=20)$$

**Usage:** GC volume provides independent validation of IFP direction. If correlation > 0.5, IFP confidence increases by 0.10.

**If GC is NOT available:** IFP proceeds without independent validation. No data is fabricated.

### 2.8 Institutional Flow Proxy — Output Schema

```python
@dataclass(frozen=True)
class InstitutionalFlowProxy:
    """Institutional Flow Proxy output for a single bar."""
    timestamp: datetime
    
    # Raw Features
    rvol: float                        # OBSERVED→INFERRED
    buying_pressure: float             # INFERRED
    selling_pressure: float            # INFERRED
    candle_efficiency: float           # INFERRED
    volume_acceleration: float         # INFERRED
    mv_relationship: str               # "confirmation" / "divergence"
    
    # Proxy Score
    ifp_score: float                   # [-100, +100]
    ifp_direction: str                 # "bullish" / "bearish" / "neutral"
    
    # Quality
    data_quality: str                  # "observed" / "inferred" / "unavailable"
    confidence: float                  # [0, 1]
    volume_source: str                 # "tick_proxy" / "broker_real" / "exchange" / "none"
    
    # Classification
    flow_state: str                    # "buying" / "selling" / "absorption" / "exhaustion" / "continuation" / "neutral"
    
    # Gold Futures Reference (if available)
    gc_available: bool
    gc_correlation: float | None
    
    # Provenance
    provenance: DataProvenance
```

### 2.9 Labeling Rules

| What We Observe | What We Label | What We Do NOT Label |
|-----------------|---------------|---------------------|
| Tick volume count | "Tick Volume (proxy)" | "Institutional Flow" |
| RVOL > 2.0 | "Above-average activity" | "Institutional accumulation" |
| Absorption pattern | "Absorption Proxy (inferred)" | "Institutional absorption" |
| Exhaustion pattern | "Exhaustion Proxy (inferred)" | "Institutional capitulation" |
| IFP Score > +50 | "Net buying pressure (inferred)" | "Institutional buying" |
| GC volume confirms | "IFP validated by GC futures" | "Confirmed institutional flow" |

**Rule:** Every output from this engine carries a `data_quality` label. The system never presents inferred data as observed fact.

---

## 3. C3 — DOUBLE COUNTING RESOLUTION — RESOLVED

### 3.1 The Problem

GSI = f(Structure, Trend, Momentum, Flow, PA, Volatility)

Evidence Families = {Structure, Liquidity, Flow, Trend/Momentum, Macro, Historical, Volatility, Context}

If both GSI and Families are inputs to the Probability Engine, the same evidence is counted twice with different weights.

### 3.2 The Solution: Separated Data Flow

```
RAW FEATURES (from engines)
    │
    ├──→ EVIDENCE FAMILIES ──→ PROBABILITY ENGINE ──→ P(Long), P(Short), P(NoTrade)
    │         │
    │         ├── Structure Family ← Structure Score (Phase 2)
    │         ├── Liquidity Family ← Liquidity Score (Phase 3)
    │         ├── Flow Family ← IFP Score (Phase 4)
    │         ├── Trend/Mom Family ← Trend + Momentum Scores (Phase 5)
    │         ├── Macro Family ← News + Macro Scores (Phase 7)
    │         ├── Historical Family ← Historical Probability (Phase 8)
    │         ├── Volatility Family ← Volatility Score (Phase 5)
    │         └── Context Family ← Regime + Session (Phase 1, 9)
    │
    └──→ GSI (DIAGNOSTIC INDEX)
              │
              ├── Human-readable aggregate
              ├── Setup Engine filter (Phase 11)
              ├── Decision Engine context (Phase 15)
              └── Feedback/Research analysis (Phase 21)
```

### 3.3 Formal Separation

**Theorem (No Double Counting):**

Let $\mathcal{F} = \{f_1, f_2, ..., f_8\}$ be the set of Evidence Families.
Let $\text{GSI} = g(f_1, f_2, ..., f_6)$ be the Gold Smart Index (using 6 of 8 families).
Let $\text{Prob} = p(f_1, f_2, ..., f_8)$ be the Probability Engine output.

**Requirement:** GSI and Prob must NOT share inputs in a way that causes double counting.

**Formal:** The Probability Engine receives $\{f_1, ..., f_8\}$ as inputs. The GSI receives $\{f_1, ..., f_6\}$ as inputs. GSI is **NOT** an input to Prob.

$$\text{Prob} = p(\mathcal{F}) \quad \text{where } \mathcal{F} \text{ are raw family scores}$$

$$\text{GSI} = g(\mathcal{F}_{\text{subset}}) \quad \text{where } \mathcal{F}_{\text{subset}} \subset \mathcal{F}$$

$$\text{GSI} \notin \text{inputs}(\text{Prob})$$

### 3.4 GSI Role Definition

| Role | Description | Used In |
|------|-------------|---------|
| **Diagnostic Index** | Human-readable aggregate of engine outputs | Dashboards, reports, research |
| **Filter** | Threshold-based pre-filter for Setup Engine | Phase 11: GSI must align with direction |
| **Context Variable** | Contextual modifier for Decision Engine | Phase 15: GSI direction noted in audit trail |
| **Analysis Dimension** | Performance analysis by GSI bucket | Phase 21: Win rate by GSI range |

**GSI is NEVER:**
- An input to the Probability Engine
- A direct component of Evidence Families
- A substitute for individual family scores

### 3.5 Evidence Family Architecture

#### Family Definition

An **Evidence Family** groups related evidence that shares information content. Each family contributes **once** to the Probability Engine.

| Family | Members | Intra-Family Weight | Direction Mapping |
|--------|---------|-------------------|-------------------|
| **Structure** | Structure Score, BOS/CHoCH | [0.60, 0.40] | Positive → Long evidence |
| **Liquidity** | Liquidity Score, Sweep | [0.50, 0.50] | Positive → Long evidence (support held) |
| **Flow** | IFP Score, Absorption, Exhaustion | [0.70, 0.20, 0.10] | Positive → Long evidence (buying pressure) |
| **Trend/Mom** | Trend Score, Momentum Score | [0.50, 0.50] | Positive → Long evidence (bullish) |
| **Macro** | News Score, Macro Score | [0.50, 0.50] | Positive → Long evidence (weak USD) |
| **Historical** | Historical Probability | [1.00] | P(Long) > P(Short) → Long evidence |
| **Volatility** | Volatility Score | [1.00] | Non-directional (context modifier) |
| **Context** | Regime, Session | [0.60, 0.40] | Non-directional (context modifier) |

#### Family Combination Rule

For each Family $f$, combine members into a single family score:

$$S_f = \frac{\sum_{i \in \text{Family}_f} w_{f,i} \cdot S_{f,i}}{\sum_{i \in \text{Family}_f} w_{f,i}}$$

Where:
- $S_{f,i}$ = score of member $i$ in family $f$ (range: [-100, +100])
- $w_{f,i}$ = intra-family weight of member $i$

#### Inter-Family Weights

| Family | Weight $w_f$ | Rationale |
|--------|-------------|-----------|
| Structure | 0.20 | Primary directional context |
| Flow | 0.18 | Volume confirmation |
| Trend/Momentum | 0.15 | Directional momentum |
| Macro | 0.15 | External factors |
| Historical | 0.15 | Empirical evidence |
| Liquidity | 0.10 | Level-based context |
| Volatility | 0.04 | Context modifier |
| Context | 0.03 | Environmental context |

$$\sum w_f = 1.00$$

### 3.6 Overlap Management

| Overlap | Families | Severity | Mitigation |
|---------|----------|----------|------------|
| Structure ↔ Trend | Structure, Trend/Mom | Partial | Different mechanisms (swings vs EMA) |
| Trend ↔ Momentum | Trend/Mom | Moderate | Different measures (direction vs rate) |
| Flow ↔ PA (CE) | Flow | Moderate | CE assigned to Flow Family only |

**Rule:** Each piece of evidence appears in **exactly one** Family. No evidence is shared across Families.

### 3.7 Dependency Graph

```
Phase 2 (Structure Score) ──────────────→ Family: Structure
Phase 3 (Liquidity Score) ──────────────→ Family: Liquidity
Phase 3 (Sweep Detection) ─────────────→ Family: Liquidity
Phase 4 (IFP Score) ───────────────────→ Family: Flow
Phase 4 (Absorption Proxy) ────────────→ Family: Flow
Phase 4 (Exhaustion Proxy) ───────────→ Family: Flow
Phase 5 (Trend Score) ─────────────────→ Family: Trend/Mom
Phase 5 (Momentum Score) ──────────────→ Family: Trend/Mom
Phase 7 (News Score) ──────────────────→ Family: Macro
Phase 7 (Macro Score) ─────────────────→ Family: Macro
Phase 8 (Historical Probability) ──────→ Family: Historical
Phase 5 (Volatility Score) ────────────→ Family: Volatility
Phase 9 (Regime) ──────────────────────→ Family: Context
Phase 1 (Session) ─────────────────────→ Family: Context

All Families → Probability Engine → P(Long), P(Short), P(NoTrade)

Phase 2-5 Scores ──→ GSI (Diagnostic Index, NOT connected to Probability Engine)
```

---

## 4. C4 — HISTORICAL FEATURE VECTOR — RESOLVED

### 4.1 Revised Feature Vector

**GSI is REMOVED** from the feature vector. Only individual components are used.

| # | Feature | Source | Range | Derived From | Potential Redundancy |
|---|---------|--------|-------|-------------|---------------------|
| 1 | Structure Score | Phase 2 | [-100, +100] | Swing points, BOS/CHoCH | Independent |
| 2 | Liquidity Score | Phase 3 | [-100, +100] | Liquidity levels, clusters | Independent |
| 3 | IFP Score | Phase 4 | [-100, +100] | BP, SP, CE, RVOL, VA, MV | Independent |
| 4 | Trend Score | Phase 5 | [-100, +100] | EMA crossover | Low overlap with Structure |
| 5 | Momentum Score | Phase 5 | [-100, +100] | RSI, MACD | Low overlap with Trend |
| 6 | Volatility Score | Phase 5 | [-100, +100] | ATR, Bollinger, GARCH | Independent |
| 7 | ATR (normalized) | Phase 5 | [0, +∞) | ATR₁₄ / Close | Low overlap with Volatility Score |
| 8 | News Score | Phase 7 | [-100, +100] | Surprise Z-scores | Independent |
| 9 | Macro Score | Phase 7 | [-100, +100] | DXY, Yields, FFR | Independent |
| 10 | Session | Phase 1 | Categorical | Time-of-day | Independent |
| 11 | Distance to Liquidity | Phase 3 | [0, +∞) | Nearest level | Independent |
| 12 | Regime | Phase 9 | Categorical | Regime classification | Independent |
| 13 | Day of Week | Phase 1 | Categorical | Calendar | Independent |
| 14 | Hour of Day | Phase 1 | Categorical | Calendar | Independent |

**Feature Vector:** $\mathbf{x}_t \in \mathbb{R}^{14}$

### 4.2 Redundancy Analysis

| Feature Pair | Overlap Level | Justification for Keeping Both |
|-------------|---------------|-------------------------------|
| Structure ↔ Trend | Low | Structure = discrete swings, Trend = continuous EMA |
| Trend ↔ Momentum | Low | Trend = direction (where), Momentum = rate (how fast) |
| IFP ↔ Structure | Low | IFP = volume-based, Structure = price-based |
| ATR ↔ Volatility Score | Low | ATR = absolute measure, Score = normalized composite |
| News ↔ Macro | Low | News = event-based, Macro = continuous data |

**Decision:** All 14 features are retained. No feature is a direct derivative of another in the vector.

### 4.3 Removed Features

| Removed Feature | Reason | Alternative |
|----------------|--------|-------------|
| GSI | Composite of Structure+Trend+Momentum+Flow+PA+Volatility — redundant with individual features | Use individual features directly |
| Price Action Score | Derived from CE (shared with IFP) + Rejection + Candle Pattern — redundant with IFP | IFP Score captures volume-weighted direction |
| GSI Confidence | Derived from GSI magnitude — redundant | Use individual feature magnitudes |

### 4.4 Feature Normalization

$$x_{\text{norm},i} = \frac{x_i - \text{median}_i}{\text{IQR}_i}$$

Where:
- $\text{median}_i$ = median of feature $i$ over **training window only**
- $\text{IQR}_i$ = interquartile range of feature $i$ over **training window only**

**Critical Rule:** Normalization parameters (median, IQR) are computed from the training window only. They are NEVER recomputed using test data.

### 4.5 Missing Feature Handling

If feature $i$ is unavailable at time $t$:

$$x_{t,i} = \text{median}_{i,\text{training}} \quad \text{(impute with training median)}$$

**Flag:** `features_missing: [list of missing features]`

**Rule:** If > 3 features are missing, the bar is excluded from similarity analysis.

---

## 5. C5 — PERFORMANCE ACCEPTANCE FRAMEWORK — RESOLVED

### 5.1 Framework Overview

The system uses a **multi-dimensional acceptance framework**. No single metric is sufficient for acceptance.

### 5.2 Acceptance Dimensions

| # | Dimension | Metric | Minimum | Target | Statistical Requirement |
|---|-----------|--------|---------|--------|------------------------|
| D1 | Profitability | Expectancy | > $0 per trade | > $20 per trade | Bootstrap 95% CI lower bound > $0 |
| D2 | Profitability | Profit Factor | > 1.0 | > 1.5 | Bootstrap 95% CI lower bound > 1.0 |
| D3 | Risk-Adjusted Return | Sharpe Ratio | > 0.5 | > 1.5 | Walk-forward median > 0.5 |
| D4 | Downside Risk | Sortino Ratio | > 0.8 | > 2.0 | Walk-forward median > 0.8 |
| D5 | Maximum Drawdown | Max DD | < 20% | < 12% | Monte Carlo 95th percentile < 25% |
| D6 | Recovery | Recovery Factor | > 1.0 | > 2.0 | Net Profit / Max DD > 1.0 |
| D7 | Tail Risk | P(Ruin) | < 5% | < 1% | Monte Carlo (1000 runs) P(DD>20%) < 5% |
| D8 | Out-of-Sample Stability | Degradation | < 40% | < 20% | OOS Sharpe > 0.6 × IS Sharpe |
| D9 | Monte Carlo Confidence | Sharpe 5th Percentile | > 0.0 | > 0.5 | Bootstrap (1000 samples) |
| D10 | Parameter Stability | Max Sensitivity | < 3.0 | < 1.5 | No parameter causes > 50% Sharpe degradation |

### 5.3 Metric Definitions

#### D1: Expectancy

$$\text{Expectancy} = \text{WinRate} \times \text{AvgWin} - (1 - \text{WinRate}) \times \text{AvgLoss}$$

**Minimum:** > $0 per trade (positive edge)
**Target:** > $20 per trade (meaningful edge)
**Statistical Requirement:** Bootstrap 95% confidence interval lower bound > $0

#### D2: Profit Factor

$$\text{ProfitFactor} = \frac{\sum \text{Winning Trades}}{\sum |\text{Losing Trades}|}$$

**Minimum:** > 1.0 (gross profit > gross loss)
**Target:** > 1.5 (meaningful profitability)
**Statistical Requirement:** Bootstrap 95% CI lower bound > 1.0

#### D3: Sharpe Ratio

$$\text{Sharpe} = \frac{R_p - R_f}{\sigma_p}$$

Where $R_f = 0$ (risk-free rate assumed 0 for simplicity).

**Minimum:** > 0.5 (better than random)
**Target:** > 1.5 (good risk-adjusted return)
**Statistical Requirement:** Walk-forward median across windows > 0.5

#### D4: Sortino Ratio

$$\text{Sortino} = \frac{R_p - R_f}{\sigma_{\text{downside}}}$$

Where $\sigma_{\text{downside}}$ = standard deviation of negative returns only.

**Minimum:** > 0.8
**Target:** > 2.0

#### D5: Maximum Drawdown

$$\text{MaxDD} = \max_t \left( \frac{\text{PeakEquity} - \text{Equity}_t}{\text{PeakEquity}} \right)$$

**Minimum:** < 20% (survival)
**Target:** < 12% (comfortable)
**Statistical Requirement:** Monte Carlo 95th percentile < 25%

#### D6: Recovery Factor

$$\text{RecoveryFactor} = \frac{\text{Net Profit}}{\text{Max Drawdown}}$$

**Minimum:** > 1.0 (can recover from drawdown)
**Target:** > 2.0 (strong recovery)

#### D7: Tail Risk — P(Ruin)

$$\text{P(Ruin)} = \frac{\text{Count}(\text{MaxDD} > 20\%)}{\text{Total Monte Carlo Runs}}$$

**Minimum:** < 5%
**Target:** < 1%
**Method:** Monte Carlo simulation (1000 trade sequence permutations)

#### D8: Out-of-Sample Stability

$$\text{Degradation} = \frac{\text{Sharpe}_{\text{IS}} - \text{Sharpe}_{\text{OOS}}}{\text{Sharpe}_{\text{IS}}}$$

**Minimum:** Degradation < 40% (OOS Sharpe > 0.6 × IS Sharpe)
**Target:** Degradation < 20% (OOS Sharpe > 0.8 × IS Sharpe)

#### D9: Monte Carlo Confidence

From bootstrap resampling (1000 samples):
- 5th percentile of Sharpe > 0.0 (minimum)
- 5th percentile of Sharpe > 0.5 (target)

#### D10: Parameter Stability

$$\text{Sensitivity}_p = \frac{\Delta \text{Sharpe}}{\Delta p / p_0}$$

**Minimum:** Max sensitivity < 3.0 for any parameter
**Target:** Max sensitivity < 1.5, Average sensitivity < 1.0

### 5.4 Acceptance Decision

$$\text{System Acceptable} \iff \bigwedge_{i=1}^{10} \text{Dimension}_i \geq \text{Minimum}$$

**All 10 dimensions must meet minimum criteria.** If any dimension fails, the system is NOT acceptable.

### 5.5 Phased Acceptance

| Phase | Required Dimensions | Minimum Criteria |
|-------|-------------------|-----------------|
| After Backtest (Phase 16) | D1–D6, D8–D10 | All minimums |
| After Robustness (Phase 17) | D7, D9, D10 | All minimums |
| After Paper Trading (Phase 18) | D1–D8 | Paper metrics vs backtest comparison |
| After Live Scaling (Phase 20) | D1–D10 | Live metrics vs paper comparison |

### 5.6 What Win Rate Replaces

**Old (INVALID):** "Win Rate > 50%" as acceptance criterion

**New (VALID):** Win Rate is reported but NOT used as acceptance criterion. Acceptance is based on Expectancy (which incorporates win rate AND average win/loss).

**Rationale:** A system with 40% win rate and 3:1 R:R is profitable (Expectancy > 0). A system with 60% win rate and 0.8:1 R:R is unprofitable (Expectancy < 0). Win rate alone is misleading.

---

## 6. C6 — NO-TRADE ARCHITECTURE — RESOLVED

### 6.1 Architectural Principle

**Decision Engine is the SOLE decision maker.** No-Trade Engine produces conditions and severity, NOT decisions.

### 6.2 Revised Data Flow

```
Evidence Engines (Phase 2-10)
    ↓
Setup Engine (Phase 11) ──→ Setup Valid/Invalid + Quality
    ↓
Risk Engine (Phase 12) ──→ Risk Approved/Rejected + Position Size
    ↓
Trade Management (Phase 13) ──→ TP₁/TP₂/TP₃, Trailing Rules
    ↓
No-Trade Engine (Phase 14) ──→ NoTradeFlags + NoTradeSeverity + NoTradeReasons
    ↓                                    ⚠️ NOT a decision ⚠️
Decision Engine (Phase 15) ──→ FINAL DECISION: LONG / SHORT / NO_TRADE
```

### 6.3 No-Trade Engine Output (Revised)

The No-Trade Engine outputs **conditions and metadata**, NOT decisions:

```python
@dataclass(frozen=True)
class NoTradeOutput:
    """No-Trade Engine output — conditions and severity only."""
    timestamp: datetime
    
    # Conditions (NOT decisions)
    conditions: dict[str, NoTradeCondition]
    active_conditions: list[str]
    
    # Severity (for Decision Engine to interpret)
    severity_per_condition: dict[str, int]
    overall_severity: int               # 0-4 (GREEN → CRITICAL)
    
    # Guidance (NOT decisions)
    position_size_factor: float         # [0, 1] — suggested multiplier
    signal_threshold_adjustment: float  # suggested adjustment
    
    # Resolution tracking
    estimated_resolution: dict[str, str | None]
    conditions_duration: dict[str, int]
    
    # Provenance
    provenance: DataProvenance
```

**Key Change:** The No-Trade Engine no longer outputs `decision: str`. It outputs `overall_severity: int` and `position_size_factor: float`. The Decision Engine interprets these.

### 6.4 Decision Engine Priority Logic (Revised)

```
PRIORITY 1: Emergency Halt
    IF Drawdown > MAX_DRAWDOWN OR Daily Loss > HARD STOP
    → DECISION = NO_TRADE (all positions closed)

PRIORITY 2: No-Trade Severity Check
    IF NoTradeOutput.overall_severity >= 3 (RED)
    → DECISION = NO_TRADE
    
    IF NoTradeOutput.overall_severity == 2 (ORANGE)
    → Apply position_size_factor, proceed with caution
    
    IF NoTradeOutput.overall_severity == 1 (YELLOW)
    → Apply signal_threshold_adjustment, proceed with caution

PRIORITY 3: Setup Validation
    IF SetupValid == False
    → DECISION = NO_TRADE
    
    IF SetupValid == True AND EntryTriggerFired == True
    → DECISION = LONG or SHORT (direction from Probability Engine)
    
    IF SetupValid == True AND EntryTriggerFired == False
    → DECISION = WAIT_FOR_TRIGGER

PRIORITY 4: Risk Validation
    IF RiskApproved == False
    → DECISION = NO_TRADE
```

### 6.5 Decision Vocabulary

The Decision Engine outputs exactly one of:

| Decision | Code | Description |
|----------|------|-------------|
| **LONG** | 1 | Enter long position |
| **SHORT** | 2 | Enter short position |
| **NO_TRADE** | 3 | Active decision not to trade (with reason) |

**Note:** WAIT_FOR_TRIGGER and MANAGE_EXISTING are intermediate states, not final decisions. The final decision at each bar is one of: LONG, SHORT, or NO_TRADE.

### 6.6 No-Trade Conditions (Unchanged)

The 9 conditions remain as defined in Phase 14. Only the output format changes.

| # | Condition | Severity Range | Block Type |
|---|-----------|---------------|-----------|
| 1 | Extreme Spread | 0–3 | Hard Block |
| 2 | Extreme Volatility | 0–3 | Hard Block |
| 3 | News Imminent | 0–3 | Hard Block |
| 4 | Poor Risk:Reward | 0–3 | Hard Block |
| 5 | Insufficient Liquidity | 0–3 | Soft Block |
| 6 | Conflicting Evidence | 0–2 | Soft Block |
| 7 | Daily Risk Limit | 0–4 | Hard Block |
| 8 | Execution Risk | 0–3 | Hard Block |
| 9 | Uncertain Regime | 0–2 | Soft Block |

### 6.7 No-Trade Logging

Every NO_TRADE decision must log:

```
Decision: NO_TRADE
Reasons:
  1. Extreme Spread: 3.5 pips > 3.0 threshold (Severity: RED)
  2. Conflicting Evidence: 4/8 families opposing (Severity: ORANGE)
Overall Severity: RED (3)
Position Size Factor: 0% (blocked)
Signal Threshold Adjustment: +0% (not applicable)
Conditions Active: [spread, conflict]
Expected Resolution: Spread normalizes; evidence alignment improves
```

---

## 7. C7 — TEMPORAL INFORMATION PROTOCOL — RESOLVED

### 7.1 Core Principle

At timestamp $t$, feature $i$ is available **if and only if**:

$$\text{Available}_i(t) = \begin{cases} 1 & \text{if } \text{AvailabilityTimestamp}_i \leq t \\ 0 & \text{if } \text{AvailabilityTimestamp}_i > t \end{cases}$$

### 7.2 Availability Timestamps by Data Type

| Data Type | Availability Timestamp | Notes |
|-----------|----------------------|-------|
| **OHLCV (M5)** | $\tau_t + 5\text{min}$ (bar close) | Bar must be confirmed |
| **OHLCV (H1)** | $\tau_t + 60\text{min}$ | Bar must be confirmed |
| **OHLCV (D1)** | End of day | Bar must be confirmed |
| **Tick Bid/Ask** | Real-time | No delay |
| **Tick Volume** | After bar close | Aggregated from ticks |
| **Swing Points** | $\tau_{\text{swing}} + k \times \text{bar\_duration}$ | k-bar confirmation |
| **BOS/CHoCH** | After confirmation bar | Close-based |
| **Session Levels** | After session close | Session must be finalized |
| **Weekly Levels** | After week close | Week must be finalized |
| **Sweep Classification** | $\tau_{\text{penetration}} + n \times \text{bar\_duration}$ | n-bar return window |
| **News Actual** | At $\text{release\_ts}_i$ | **Never before** |
| **News Forecast** | At calendar publication | Known in advance |
| **News Previous** | At previous release | First-release value only |
| **News Revision** | At $\text{revision\_ts}_i$ | **Never before** |
| **DXY (Primary)** | After publication | Forward-filled from publication |
| **DXY (Secondary)** | After daily close | Daily value |
| **Treasury Yields** | After FRED publication (~16:00 ET) | Daily only |
| **Fed Funds Rate** | At FOMC announcement | Event-driven |
| **Regime** | After 5-bar confirmation | Transition prevention |
| **GSI** | After component computation | Sequential |
| **Probability** | After Evidence Family computation | Sequential |
| **Calibration Parameters** | From training window only | **Never from test data** |
| **Normalization Parameters** | From training window only | **Never from test data** |
| **Walk-Forward Parameters** | From current training window only | **Never from future windows** |

### 7.3 Temporal Information Set

At each timestamp $t$, the system's information set is:

$$\mathcal{F}_t = \{d : \text{AvailabilityTimestamp}(d) \leq t\}$$

**Formal Rule:** For any computation at time $t$:

$$\text{Output}(t) = f(\mathcal{F}_t)$$

The function $f$ must NOT access any data $d \notin \mathcal{F}_t$.

### 7.4 Backtest Temporal Enforcement

```
For each bar t in test period:
    1. Determine which data is available at time t
    2. Compute all features using ONLY available data
    3. Apply calibration from TRAINING window only
    4. Apply normalization from TRAINING window only
    5. Record decision and outcome
    6. Move to next bar
```

### 7.5 Walk-Forward Temporal Protocol

```
Window w:
    Training: [t_start, t_end)
    Testing:  [t_end, t_end + test_duration)
    
    For each bar in Training:
        - Compute features from available data
        - Estimate parameters (normalization, calibration, etc.)
    
    For each bar in Testing:
        - Compute features from available data
        - Apply parameters from Training ONLY
        - Never access data from future windows
```

### 7.6 Specific Temporal Rules

#### News Revisions

$$\text{At time } t < \text{revision\_ts}_i: \quad \text{Use } P_i \text{ (first release)}$$

$$\text{At time } t \geq \text{revision\_ts}_i: \quad \text{May use } P_i^{revised} \text{ for analysis}$$

**Rule:** Revised values are NEVER used before their revision timestamp.

#### Historical Similarity

$$\mathcal{N}_K(\mathbf{x}_t) = \{\mathbf{x}_i : i < t \wedge d(\mathbf{x}_t, \mathbf{x}_i) \leq d_{\text{threshold}}\}$$

**Rule:** Neighbors are ONLY from before the current bar. No future neighbors.

#### Calibration

$$\text{CalibrationDataset} \subset \text{TrainingWindow}$$

**Rule:** Calibration data is from the training window only. Never from test data.

#### Normalization

$$\text{median}_{i,\text{training}}, \text{IQR}_{i,\text{training}} \quad \text{computed from training window only}$$

**Rule:** Normalization parameters are NEVER recomputed using test data.

---

# PART II — REVISED ARCHITECTURE

---

## 8. REVISED SYSTEM ARCHITECTURE

### 8.1 Complete Data Flow

```
PHASE 1: DATA SPECIFICATION
    └── OHLCV, Tick Data, News, Macro, Sessions
         │
PHASE 2: MARKET STRUCTURE ──────────────────→ Structure Score [-100,+100]
    │                                          Structure State
    │                                          Swing Points
    │                                          BOS/CHoCH
    │
PHASE 3: LIQUIDITY ────────────────────────→ Liquidity Score [-100,+100]
    │                                          Liquidity Levels
    │                                          Sweep Detection
    │                                          Absorption Detection
    │
PHASE 4: FLOW (Institutional Flow Proxy) ──→ IFP Score [-100,+100]
    │                                          Flow State
    │                                          Data Quality Level
    │
PHASE 5: TREND/MOMENTUM/VOLATILITY ────────→ Trend Score [-100,+100]
    │                                          Momentum Score [-100,+100]
    │                                          Volatility Score [-100,+100]
    │                                          ATR
    │
    ├──→ PHASE 6: GSI (Diagnostic Index) ──→ GSI [-100,+100] (NOT connected to Phase 10)
    │         │                                Human-readable aggregate
    │         │                                Filter for Phase 11
    │         │                                Context for Phase 15
    │
PHASE 7: NEWS/MACRO ──────────────────────→ News Score [-100,+100]
    │                                          Macro Score [-100,+100]
    │
PHASE 8: HISTORICAL SIMILARITY ───────────→ Historical Probability
    │                                          P(Long), P(Short), P(NoTrade)
    │                                          Feature Vector (14 dimensions)
    │
PHASE 9: REGIME DETECTION ────────────────→ Regime Type
    │                                          Regime Confidence
    │                                          Parameter Adjustments
    │
    ↓↓↓ EVIDENCE FAMILY AGGREGATION ↓↓↓
    
    Structure Score ─────→ Family: Structure (w=0.20)
    Liquidity Score ─────→ Family: Liquidity (w=0.10)
    IFP Score ───────────→ Family: Flow (w=0.18)
    Trend + Mom Scores ──→ Family: Trend/Mom (w=0.15)
    News + Macro Scores ─→ Family: Macro (w=0.15)
    Historical Prob ─────→ Family: Historical (w=0.15)
    Volatility Score ────→ Family: Volatility (w=0.04)
    Regime + Session ────→ Family: Context (w=0.03)
    
    ↓↓↓ PROBABILITY ENGINE ↓↓↓
    
PHASE 10: PROBABILITY ────────────────────→ P(Long), P(Short), P(NoTrade)
    │                                          Confidence
    │                                          Calibration Status
    │
PHASE 11: SETUP ENGINE ───────────────────→ Setup Valid/Invalid
    │                                          Setup Quality
    │                                          Entry Trigger
    │                                          Invalidation Level
    │
PHASE 12: RISK ENGINE ────────────────────→ Position Size
    │                                          SL/TP Levels
    │                                          Risk Limits Check
    │
PHASE 13: TRADE MANAGEMENT ───────────────→ TP₁/TP₂/TP₃
    │                                          Trailing Rules
    │                                          Emergency Conditions
    │
PHASE 14: NO-TRADE ENGINE ────────────────→ NoTradeFlags
    │    (Conditions & Severity ONLY)         NoTradeSeverity
    │    (NOT a decision maker)               NoTradeReasons
    │
PHASE 15: DECISION ENGINE ────────────────→ FINAL DECISION: LONG / SHORT / NO_TRADE
    │    (SOLE decision maker)                Trade Plan
    │                                          Audit Trail
    │
PHASE 16: BACKTEST ───────────────────────→ Backtest Results
    │
PHASE 17: ROBUSTNESS ────────────────────→ Robustness Report
    │
PHASE 18: PAPER TRADING ─────────────────→ Paper Results
    │
PHASE 19: EXECUTION ─────────────────────→ Execution Records
    │
PHASE 20: LIVE TRADING ──────────────────→ Live Performance
    │
PHASE 21: FEEDBACK ──────────────────────→ Improvement Recommendations
```

### 8.2 Critical Separation Points

| Separation | What | Why |
|-----------|------|-----|
| GSI ↔ Probability Engine | GSI is diagnostic, not an input | Prevents double counting |
| No-Trade ↔ Decision Engine | No-Trade outputs conditions, Decision outputs decisions | Single decision authority |
| Observed ↔ Inferred ↔ Proxy | Clear data quality taxonomy | Prevents mislabeling |
| Training ↔ Test data | Normalization/calibration from training only | Prevents data leakage |

---

# PART III — GSI SPECIFICATION

---

## 9. GSI COMPLETE SPECIFICATION

### 9.1 Definition

$$\text{GSI}: \mathbb{R}^{n_t} \rightarrow [-100, +100]$$

A composite diagnostic index measuring aggregate directional evidence for XAUUSD.

### 9.2 Formula

$$\text{GSI}_{\text{raw}} = \sum_{i=1}^{6} w_i \cdot S_i$$

| Component | Source | Weight | Range |
|-----------|--------|--------|-------|
| Structure | Phase 2 | 0.25 | [-100, +100] |
| Flow | Phase 4 | 0.20 | [-100, +100] |
| Trend | Phase 5 | 0.15 | [-100, +100] |
| Momentum | Phase 5 | 0.15 | [-100, +100] |
| Price Action | Derived | 0.15 | [-100, +100] |
| Volatility | Phase 5 | 0.10 | [-100, +100] |

### 9.3 Smoothing

$$\text{GSI}_{\text{smooth},t} = 0.5 \cdot \text{GSI}_{\text{raw},t} + 0.5 \cdot \text{GSI}_{\text{smooth},t-1}$$

### 9.4 Clamping

$$\text{GSI} = \text{clamp}(\text{GSI}_{\text{smooth}}, -100, +100)$$

### 9.5 Interpretation

| Range | Direction | Confidence | Use |
|-------|-----------|------------|-----|
| +60 to +100 | Strong Bullish | High | Setup filter, context |
| +30 to +60 | Bullish | Moderate | Setup filter, context |
| +10 to +30 | Weak Bullish | Low | Context only |
| -10 to +10 | Neutral | Negligible | No directional signal |
| -30 to -10 | Weak Bearish | Low | Context only |
| -60 to -30 | Bearish | Moderate | Setup filter, context |
| -100 to -60 | Strong Bearish | High | Setup filter, context |

### 9.6 Role

- **Diagnostic Index:** Human-readable aggregate
- **Filter:** Phase 11 requires GSI alignment with trade direction
- **Context:** Phase 15 notes GSI in audit trail
- **Analysis:** Phase 21 analyzes performance by GSI bucket

### 9.7 GSI is NOT

- ❌ An input to Probability Engine
- ❌ A probability
- ❌ A risk score
- ❌ A safety score
- ❌ A trading signal

---

# PART IV — INSTITUTIONAL FLOW PROXY SPECIFICATION

---

## 10. INSTITUTIONAL FLOW PROXY COMPLETE SPECIFICATION

### 10.1 Definition

The Institutional Flow Proxy (IFP) is a **layered inference system** that approximates institutional order flow from available market data. It is explicitly labeled as a **proxy**, not a direct observation.

### 10.2 Data Layers

| Layer | Label | Examples |
|-------|-------|---------|
| Observed | Directly measured | Tick Volume, OHLCV, Spread |
| Inferred | Derived from observed | RVOL, BP, SP, CE, VA, Absorption, Exhaustion |
| Proxy | Approximation of unobservable | IFP Score, Flow State |
| Unavailable | Cannot be obtained | Actual order book, institutional positions |

### 10.3 Feature Definitions

| Feature | Formula | Data Quality | Range |
|---------|---------|-------------|-------|
| RVOL | $V_t / \text{EMA}(V, 20)$ | OBSERVED→INFERRED | [0, +∞) |
| Buying Pressure | $(C-L)/(H-L) \times V$ | INFERRED | [0, V_t] |
| Selling Pressure | $(H-C)/(H-L) \times V$ | INFERRED | [0, V_t] |
| Candle Efficiency | $|C-O|/(H-L)$ | INFERRED | [0, 1] |
| Volume Acceleration | $(V_t - V_{t-1})/V_{t-1}$ | INFERRED | (-∞, +∞) |
| Absorption Proxy | High RVOL + Small Range + Near Level | INFERRED (proxy) | Boolean |
| Exhaustion Proxy | Extreme RVOL + Small Range + At Extreme | INFERRED (proxy) | Boolean |

### 10.4 IFP Score

$$\text{IFP}_{\text{score}} = 0.30 \cdot \text{Pressure}_{\text{score}} + 0.25 \cdot \text{Efficiency}_{\text{score}} + 0.20 \cdot \text{RVOL}_{\text{score}} + 0.10 \cdot \text{Acceleration}_{\text{score}} + 0.15 \cdot \text{MV}_{\text{score}}$$

Range: [-100, +100]

### 10.5 Confidence Levels

| Data Quality | Confidence | Use |
|-------------|-----------|-----|
| OBSERVED (broker/exchange volume) | 0.90 | Full weight |
| INFERRED (tick volume) | 0.70 | Reduced weight |
| PARTIAL (some features missing) | 0.50 | Minimal weight |
| UNAVAILABLE | 0.00 | Skip IFP |

### 10.6 Labeling Rules

- ✅ "Net buying pressure (inferred from tick volume)"
- ✅ "Absorption proxy detected"
- ❌ "Institutional accumulation detected"
- ❌ "Smart money is buying"

---

# PART V — EVIDENCE FAMILY ARCHITECTURE

---

## 11. EVIDENCE FAMILY ARCHITECTURE

### 11.1 Family Definitions

| Family | Members | Intra-Weights | Direction |
|--------|---------|--------------|-----------|
| Structure | Structure Score, BOS/CHoCH | [0.60, 0.40] | Positive → Long |
| Liquidity | Liquidity Score, Sweep | [0.50, 0.50] | Positive → Long |
| Flow | IFP Score, Absorption, Exhaustion | [0.70, 0.20, 0.10] | Positive → Long |
| Trend/Mom | Trend Score, Momentum Score | [0.50, 0.50] | Positive → Long |
| Macro | News Score, Macro Score | [0.50, 0.50] | Positive → Long |
| Historical | Historical Probability | [1.00] | P(Long) > P(Short) → Long |
| Volatility | Volatility Score | [1.00] | Non-directional |
| Context | Regime, Session | [0.60, 0.40] | Non-directional |

### 11.2 Inter-Family Weights

| Family | Weight |
|--------|--------|
| Structure | 0.20 |
| Flow | 0.18 |
| Trend/Mom | 0.15 |
| Macro | 0.15 |
| Historical | 0.15 |
| Liquidity | 0.10 |
| Volatility | 0.04 |
| Context | 0.03 |

### 11.3 No Double Counting Rule

Each piece of evidence appears in **exactly one** Family. Evidence Families are the **sole input** to the Probability Engine. GSI is **NEVER** an input to the Probability Engine.

---

# PART VI — HISTORICAL FEATURE SPECIFICATION

---

## 12. HISTORICAL FEATURE VECTOR

### 12.1 Revised Vector (14 dimensions)

| # | Feature | Source | Range | Redundancy |
|---|---------|--------|-------|-----------|
| 1 | Structure Score | Phase 2 | [-100, +100] | Independent |
| 2 | Liquidity Score | Phase 3 | [-100, +100] | Independent |
| 3 | IFP Score | Phase 4 | [-100, +100] | Independent |
| 4 | Trend Score | Phase 5 | [-100, +100] | Low overlap with #1 |
| 5 | Momentum Score | Phase 5 | [-100, +100] | Low overlap with #4 |
| 6 | Volatility Score | Phase 5 | [-100, +100] | Independent |
| 7 | ATR (normalized) | Phase 5 | [0, +∞) | Low overlap with #6 |
| 8 | News Score | Phase 7 | [-100, +100] | Independent |
| 9 | Macro Score | Phase 7 | [-100, +100] | Independent |
| 10 | Session | Phase 1 | Categorical | Independent |
| 11 | Distance to Liquidity | Phase 3 | [0, +∞) | Independent |
| 12 | Regime | Phase 9 | Categorical | Independent |
| 13 | Day of Week | Phase 1 | Categorical | Independent |
| 14 | Hour of Day | Phase 1 | Categorical | Independent |

### 12.2 Removed from Vector

| Removed | Reason |
|---------|--------|
| GSI | Redundant with features 1, 4, 5, 3, 6 |
| Price Action Score | Redundant with IFP Score (CE shared) |
| GSI Confidence | Derived from GSI magnitude |

### 12.3 Normalization

$$x_{\text{norm},i} = \frac{x_i - \text{median}_{i,\text{train}}}{\text{IQR}_{i,\text{train}}}$$

Parameters from training window only.

---

# PART VII — PROBABILITY & CALIBRATION ARCHITECTURE

---

## 13. PROBABILITY & CALIBRATION

### 13.1 Bayesian Model

$$P(\text{Long} | \mathbf{E}) = \frac{P_0(\text{Long}) \times \prod_{f} \text{LR}_{f,\text{long}}}{P_0(\text{Long}) \times \prod_{f} \text{LR}_{f,\text{long}} + P_0(\text{Short}) \times \prod_{f} \text{LR}_{f,\text{short}} + P_0(\text{NoTrade}) \times 1}$$

Where:
- $P_0(\text{Long}) = P_0(\text{Short}) = 0.33$, $P_0(\text{NoTrade}) = 0.34$
- $\text{LR}_{f} = \exp(S_f / 100 \times \lambda_f)$, $\lambda_f = 0.5$

### 13.2 Calibration Pipeline

```
Raw Bayesian Probability (from Evidence Families)
    ↓
Calibration Dataset (from training window)
    ↓
Calibration Model
    ├── Option A: Platt Scaling
    │   P_cal = 1 / (1 + exp(a × P_raw + b))
    │
    └── Option B: Isotonic Regression (preferred if non-monotonic)
        P_cal = IsotonicRegression(P_raw)
    ↓
Calibrated Probability
    ↓
Validation (ECE < 0.10 on separate calibration set)
```

### 13.3 Calibration Temporal Rules

| Rule | Description |
|------|-------------|
| R1 | Calibration dataset is from training window only |
| R2 | Calibration is re-estimated per walk-forward window |
| R3 | Test data is NEVER used for calibration |
| R4 | Calibration quality is measured on a held-out calibration set |
| R5 | If ECE > 0.15, flag `calibration_poor` and reduce confidence |

### 13.4 Walk-Forward Calibration

```
Window w:
    Training: [t_start, t_end)
    Calibration: [t_end - cal_duration, t_end)  ← subset of training
    Testing: [t_end, t_end + test_duration)
    
    1. Estimate Bayesian priors from Training
    2. Fit calibration model from Calibration set
    3. Apply to Testing period ONLY
    4. Never use Testing data for calibration
```

---

# PART VIII — NO-TRADE ARCHITECTURE

---

## 14. NO-TRADE ARCHITECTURE (REVISED)

### 14.1 Role

No-Trade Engine is a **condition evaluator**, NOT a decision maker.

### 14.2 Output

```python
@dataclass(frozen=True)
class NoTradeOutput:
    """Conditions and severity — NOT a decision."""
    timestamp: datetime
    conditions: dict[str, NoTradeCondition]
    active_conditions: list[str]
    severity_per_condition: dict[str, int]
    overall_severity: int               # 0-4
    position_size_factor: float         # [0, 1]
    signal_threshold_adjustment: float
    estimated_resolution: dict[str, str | None]
    conditions_duration: dict[str, int]
    provenance: DataProvenance
```

### 14.3 Decision Engine Integration

```
NoTradeOutput.overall_severity:
    0 (GREEN)    → Proceed normally
    1 (YELLOW)   → Apply signal_threshold_adjustment
    2 (ORANGE)   → Apply position_size_factor
    3 (RED)      → DECISION = NO_TRADE
    4 (CRITICAL) → DECISION = NO_TRADE (all positions closed)
```

---

# PART IX — TEMPORAL INFORMATION PROTOCOL

---

## 15. TEMPORAL INFORMATION PROTOCOL

### 15.1 Core Rule

$$\text{Available}_i(t) = \mathbb{1}[\text{AvailabilityTimestamp}_i \leq t]$$

### 15.2 Availability Table

| Data | Availability Timestamp |
|------|----------------------|
| OHLCV M5 | Bar close + 5min |
| Swing Points | Swing time + k bars |
| BOS/CHoCH | Confirmation bar |
| Session Levels | Session close |
| Sweep Classification | Penetration + n bars |
| News Actual | release_ts |
| News Revision | revision_ts |
| DXY/Yields | Publication timestamp |
| Regime | 5-bar confirmation |
| Calibration Parameters | Training window only |
| Normalization Parameters | Training window only |

### 15.3 Enforcement

Every computation at time $t$ uses ONLY data from $\mathcal{F}_t = \{d : \text{AvailabilityTimestamp}(d) \leq t\}$.

---

# PART X — BACKTEST PROTOCOL

---

## 16. BACKTEST PROTOCOL

### 16.1 Data Splits

| Split | Period | Purpose |
|-------|--------|---------|
| Training | 2016–2020 (5 years) | Parameter estimation |
| Validation | 2021–2022 (2 years) | Hyperparameter tuning |
| Test | 2023–2026-08-31 | Final evaluation |

**Note:** Test set ends at 2026-08-31 (current date), NOT 2026-12-31.

### 16.2 Walk-Forward

| Parameter | Value |
|-----------|-------|
| Training window | 3 years |
| Test window | 1 year |
| Step size | 1 year |
| Purge gap | Max lookback + Outcome horizon |
| Minimum windows | 5 |

### 16.3 Temporal Enforcement

- Bar $t$ uses only data from bars $\{1, ..., t\}$
- Entry at next bar open
- Swing confirmation requires k future bars
- Sweep classification requires n-bar return window
- Calibration from training window only
- Normalization from training window only

---

# PART XI — REVISED PERFORMANCE ACCEPTANCE

---

## 17. PERFORMANCE ACCEPTANCE FRAMEWORK

### 17.1 Dimensions

| # | Dimension | Metric | Minimum | Target |
|---|-----------|--------|---------|--------|
| D1 | Profitability | Expectancy | > $0/trade | > $20/trade |
| D2 | Profitability | Profit Factor | > 1.0 | > 1.5 |
| D3 | Risk-Adjusted | Sharpe | > 0.5 | > 1.5 |
| D4 | Downside Risk | Sortino | > 0.8 | > 2.0 |
| D5 | Max Drawdown | Max DD | < 20% | < 12% |
| D6 | Recovery | Recovery Factor | > 1.0 | > 2.0 |
| D7 | Tail Risk | P(Ruin) | < 5% | < 1% |
| D8 | OOS Stability | Degradation | < 40% | < 20% |
| D9 | MC Confidence | Sharpe 5th %ile | > 0.0 | > 0.5 |
| D10 | Param Stability | Max Sensitivity | < 3.0 | < 1.5 |

### 17.2 Acceptance Rule

$$\text{Acceptable} \iff \bigwedge_{i=1}^{10} D_i \geq \text{Minimum}_i$$

### 17.3 Statistical Requirements

| Metric | Statistical Test | Requirement |
|--------|-----------------|-------------|
| Expectancy | Bootstrap (1000) | 95% CI lower bound > $0 |
| Profit Factor | Bootstrap (1000) | 95% CI lower bound > 1.0 |
| Sharpe | Walk-forward median | Median > 0.5 |
| P(Ruin) | Monte Carlo (1000) | P(DD>20%) < 5% |
| Degradation | IS vs OOS comparison | OOS > 0.6 × IS |
| Sensitivity | Parameter perturbation | No param causes > 50% degradation |

---

# PART XII — FIXED DECISIONS

---

## 18. FIXED DECISIONS

| # | Decision | Value | Phase |
|---|----------|-------|-------|
| F1 | Instrument | XAUUSD | 1 |
| F2 | Primary Timeframe | M5 | 1 |
| F3 | Analysis Timeframes | D1, H4, H1, M15, M5 | 1 |
| F4 | Timestamp Convention | All UTC | 1 |
| F5 | GSI Name | Gold Smart Index | 6 |
| F6 | GSI Role | Diagnostic Index (NOT Probability input) | 6 |
| F7 | GSI Range | [-100, +100] | 6 |
| F8 | Evidence Families | 8 families (sole Probability input) | 10 |
| F9 | IFP Labeling | Proxy/Inferred (never "institutional") | 4 |
| F10 | No-Trade Role | Condition evaluator (NOT decision maker) | 14 |
| F11 | Decision Engine | Sole decision maker (LONG/SHORT/NO_TRADE) | 15 |
| F12 | Temporal Rule | Available(t) = 1 iff Timestamp ≤ t | All |
| F13 | Test Set | 2023–2026-08-31 | 16 |
| F14 | Performance Framework | 10-dimensional acceptance | 17 |
| F15 | Calibration | Training-window-only, walk-forward | 10 |

---

# PART XIII — INITIAL PARAMETERS

---

## 19. INITIAL PARAMETERS

| Phase | Parameter | Value | Classification |
|-------|-----------|-------|---------------|
| 2 | k (fractal) | 3 | INITIAL |
| 2 | BOS_tolerance | 0.05 ATR | INITIAL |
| 3 | EQHL_TOLERANCE | 0.10 ATR | INITIAL |
| 3 | SWEEP_RETURN | 5 bars | INITIAL |
| 4 | RVOL_LOOKBACK | 20 | INITIAL |
| 6 | GSI weights | [0.25,0.20,0.15,0.15,0.15,0.10] | INITIAL |
| 6 | GSI smoothing | 3 bars | INITIAL |
| 7 | MIN_SURPRISE_SAMPLES | 20 | INITIAL |
| 8 | K_NEIGHBORS | 250 | INITIAL |
| 8 | TARGET_ATR | 2.0 | INITIAL |
| 8 | STOP_ATR | 1.0 | INITIAL |
| 10 | Priors | [0.33, 0.33, 0.34] | INITIAL |
| 10 | α (sensitivity) | 0.5 | INITIAL |
| 10 | CALIBRATION_WINDOW | 500 bars | INITIAL |
| 11 | MIN_P_ACTION | 0.55 | INITIAL |
| 11 | MIN_RR_RATIO | 1.5 | INITIAL |
| 12 | RISK_PER_TRADE | 1% | INITIAL |
| 12 | MAX_DAILY_LOSS | 5% | INITIAL |
| 12 | MAX_DRAWDOWN | 20% | INITIAL |
| 13 | TP1_RATIO | 50% | INITIAL |
| 13 | BE_TRIGGER | 1.0 ATR | INITIAL |
| 13 | TRAIL_FIXED | 1.0 ATR | INITIAL |
| 13 | EMERGENCY_DROP | 3.0 ATR | INITIAL |
| 14 | SPREAD_HALT | 3.0 pips | INITIAL |
| 14 | VOL_HALT | 2.5 ATR ratio | INITIAL |

---

# PART XIV — REMAINING HYPOTHESES

---

## 20. HYPOTHESES

| # | Hypothesis | Phase | Test |
|---|-----------|-------|------|
| H1 | MT5 provides reliable tick data | 1 | Fetch 30 days |
| H2 | DXY feed <5min delay | 1 | Compare timestamps |
| H3 | Treasury yields via FRED | 1 | Fetch 1 year |
| H4 | Session definitions match broker | 1 | Compare with volume |
| H5 | News data consistently available | 1 | Fetch 6 months |
| H6 | Tick volume correlates with real volume | 1 | Correlation > 0.6 |
| H7 | EQHL tolerance captures meaningful levels | 3 | Visual + backtest |
| H8 | Sweep detection lower false positive | 3 | Backtest |
| H9 | RVOL 20 captures volume regime | 4 | Statistical analysis |
| H10 | Exhaustion precedes reversals | 4 | Statistical test |
| H11 | GSI weights well-calibrated | 6 | Reliability diagram |
| H12 | Structure highest feature importance | 6 | Random Forest |
| H13 | Z-score >1.5 predicts Gold moves | 7 | Statistical test |
| H14 | DXY-Gold inverse correlation | 7 | Correlation |
| H15 | Mahalanobis > Euclidean | 8 | Compare accuracy |
| H16 | 250 neighbors sufficient | 8 | Sample sensitivity |
| H17 | Regime classification stable | 9 | Duration analysis |
| H18 | News blocking improves returns | 9 | Backtest with/without |
| H19 | Bayesian > simple averaging | 10 | Backtest both |
| H20 | 8 Families prevent double counting | 10 | Correlation < 0.4 |
| H21 | Multi-factor setup > probability-only | 11 | Backtest both |
| H22 | 1% risk ensures survival | 12 | Monte Carlo |
| H23 | Structure SL > fixed ATR SL | 12 | Backtest both |
| H24 | Partial close > full close | 13 | Backtest both |
| H25 | Structure trailing > fixed trailing | 13 | Backtest both |
| H26 | No-Trade reduces drawdown | 14 | Backtest with/without |
| H27 | System robust to ±10% parameters | 17 | Sensitivity |
| H28 | Monte Carlo confirms stability | 17 | P(Ruin) < 1% |
| H29 | Paper consistent with backtest | 18 | Compare metrics |
| H30 | Phase 1 params ensure survival | 20 | Live monitoring |

---

# PART XV — REMAINING OPEN DECISIONS

---

## 21. OPEN DECISIONS

| # | Decision | Options | Resolution |
|---|----------|---------|-----------|
| O1 | DXY Primary Source | Broker/MetaAPI/FRED | Data Architecture |
| O2 | Yield Primary Source | Broker/FRED/Yahoo | Data Architecture |
| O3 | News Primary Source | MetaAPI/Investing.com/Custom | Data Architecture |
| O4 | GC Futures Access | MT5 GC/External/None | Implementation test |
| O5 | Platt vs Isotonic | Platt Scaling / Isotonic / Both | Phase 17 testing |
| O6 | Session Encoding | Ordinal / One-hot | Phase 17 testing |
| O7 | Regime Encoding | Ordinal / One-hot | Phase 17 testing |

---

# PART XVI — REMAINING ISSUES

---

## 22. REMAINING SIGNIFICANT ISSUES

| # | Issue | Phase | Status |
|---|-------|-------|--------|
| S1 | Macro data sources unresolved | 1, 7 | OPEN — defer to implementation |
| S2 | News data source unresolved | 1, 7 | OPEN — defer to implementation |
| S3 | GC futures access unknown | 1, 4 | OPEN — test during implementation |
| S4 | Whether broker provides real volume | 1, 4 | OPEN — test during implementation |
| S5 | Platt vs Isotonic calibration | 10 | OPEN — test both in Phase 17 |
| S6 | Optimal walk-forward window sizes | 16 | OPEN — test in Phase 17 |
| S7 | Session/Regime encoding method | 8 | OPEN — test both in Phase 17 |

## 23. REMAINING MODERATE ISSUES

| # | Issue | Phase | Status |
|---|-------|-------|--------|
| M1 | Position size formula narrative | 12 | MINOR — clean up in implementation |
| M2 | Price Action Score derivation | 6 | RESOLVED — removed from GSI (CE in Flow only) |
| M3 | GSI smoothing period optimal | 6 | INITIAL — test in Phase 17 |
| M4 | Calibration recalibration frequency | 10 | INITIAL — test in Phase 17 |
| M5 | Optimal K for KNN | 8 | INITIAL — test in Phase 17 |
| M6 | Covariance regularization λ | 8 | INITIAL — test in Phase 17 |

---

# PART XVII — IMPLEMENTATION BLOCKERS

---

## 24. IMPLEMENTATION BLOCKERS

| # | Blocker | Status | Resolution |
|---|---------|--------|------------|
| B1 | GSI naming conflict | ✅ RESOLVED | "Gold Smart Index" |
| B2 | GSI/Family double counting | ✅ RESOLVED | GSI excluded from Phase 10 |
| B3 | Institutional Flow Proxy | ✅ RESOLVED | Layered architecture defined |
| B4 | Historical feature vector | ✅ RESOLVED | GSI removed, redundancy documented |
| B5 | Performance acceptance | ✅ RESOLVED | 10-dimensional framework |
| B6 | No-Trade architecture | ✅ RESOLVED | Conditions only, not decisions |
| B7 | Temporal backtest protocol | ✅ RESOLVED | Information protocol defined |

**All 7 critical blockers RESOLVED.**

---

# PART XVIII — FINAL GATE

---

## 25. CRITICAL ISSUE RESOLUTION STATUS

| Issue | Status | Resolution | Remaining Risk |
|-------|--------|------------|----------------|
| C1 — GSI Naming | ✅ RESOLVED | "Gold Smart Index" throughout | None |
| C2 — Institutional Flow Proxy | ✅ RESOLVED | Layered architecture with confidence levels | Proxy accuracy depends on volume source quality |
| C3 — Double Counting | ✅ RESOLVED | GSI excluded from Probability Engine; Evidence Families are sole input | Minor overlap between families (managed through weights) |
| C4 — Historical Feature Vector | ✅ RESOLVED | GSI removed; 14 individual features | Minor redundancy between Trend/Momentum (managed) |
| C5 — Performance Acceptance | ✅ RESOLVED | 10-dimensional framework with statistical requirements | Thresholds need validation in Phase 17 |
| C6 — No-Trade Architecture | ✅ RESOLVED | Conditions only; Decision Engine is sole decision maker | Alignment between Phase 14 output and Phase 15 input needs testing |
| C7 — Temporal Backtest Protocol | ✅ RESOLVED | Information Protocol with availability timestamps | Enforcement requires careful implementation |

## 26. IMPLEMENTATION READINESS

```
╔══════════════════════════════════════════════════════════════╗
║              IMPLEMENTATION READINESS ASSESSMENT             ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Critical Issues Resolved:        7/7  ✅                   ║
║  Significant Issues Remaining:    7     (data sources)       ║
║  Moderate Issues Remaining:       6     (optimization)       ║
║                                                              ║
║  Architecture:                   CONSISTENT ✅               ║
║  Mathematical Definitions:       COMPLETE ✅                 ║
║  Temporal Protocol:              DEFINED ✅                  ║
║  Performance Framework:          DEFINED ✅                  ║
║  No Double Counting:             ENFORCED ✅                 ║
║                                                              ║
║  Data Sources:                   UNRESOLVED ⚠️              ║
║  (DXY, Yields, News — defer to implementation)              ║
║                                                              ║
║  ────────────────────────────────────────────────────────── ║
║                                                              ║
║  CLASSIFICATION:  READY FOR ARCHITECTURE                     ║
║                                                              ║
║  Rationale:                                                  ║
║  - All mathematical definitions are consistent               ║
║  - Architecture is clean and non-contradictory               ║
║  - Critical issues are resolved                              ║
║  - Data sources need resolution during implementation        ║
║  - System is ready for module design and code structure      ║
║                                                              ║
║  NOT YET:                                                    ║
║  - NOT READY FOR DATA IMPLEMENTATION (data sources unknown)  ║
║  - NOT READY FOR FULL IMPLEMENTATION (need architecture)     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*All critical issues C1–C7 have been resolved with mathematical reformulation.*
*No code has been written. All definitions are mathematical/engineering specifications.*
