# PHASE 4 — FLOW ENGINE

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the mathematical framework for **Volume and Order Flow Analysis** — measuring the intensity, direction, and quality of trading activity to infer buying/selling pressure, absorption, exhaustion, and continuation signals.

This engine produces:
1. Relative Volume (RVOL) — volume relative to average
2. Buying Pressure / Selling Pressure — directional volume decomposition
3. Candle Efficiency — how effectively price moved through the range
4. Volume Acceleration — rate of change in volume
5. Momentum/Volume Relationship — divergence and confirmation
6. Flow Score — unified directional flow metric [-100, +100]
7. Flow State classification (Buying, Selling, Absorption, Exhaustion, Continuation)

**Scope Boundary:**
- This engine uses **volume and price action** only.
- Structure, liquidity, and momentum are inputs from Phase 2, 3, 5 — not duplicated.
- The engine does **not** generate trading signals — it provides flow context.

---

## B — INPUTS

### B.1 — Required Data

| Data | Source | Reference |
|------|--------|-----------|
| OHLCV | MT5 | Phase 1 |
| Tick Volume / Real Volume / Composite Volume | MT5 (see Phase 1, Section D.2) | Phase 1 |
| ATR | Derived from OHLCV | Phase 5 |
| Structure State | Phase 2 | Phase 2 |
| Liquidity Levels | Phase 3 | Phase 3 |

### B.2 — Parameters

| Parameter | Initial Value | Description |
|-----------|--------------|-------------|
| `RVOL_LOOKBACK` | 20 | EMA period for volume average |
| `PRESSURE_SMOOTHING` | 3 | Bar smoothing for pressure scores |
| `ACCELERATION_LOOKBACK` | 5 | Bars for volume acceleration |
| `FLOW_SCORE_WEIGHTS` | See Section H | Weights for Flow Score components |
| `EXHAUSTION_RVOL_THRESHOLD` | 2.5 | RVOL above which exhaustion is possible |
| `EXHAUSTION_RANGE_THRESHOLD` | 0.3 | Range/ATR below which exhaustion is confirmed |
| `ABSORPTION_RVOL_THRESHOLD` | 1.5 | RVOL for absorption detection |
| `ABSORPTION_RANGE_THRESHOLD` | 0.5 | Range/ATR for absorption detection |

---

## C — RELATIVE VOLUME (RVOL)

### C.1 — Definition

Relative Volume measures current volume against a rolling average:

$$\text{RVOL}_t = \frac{V_t}{\text{EMA}(V, \text{lookback})_t}$$

Where:
- $V_t$ = Volume at bar $t$ (tick, broker, or composite — see Phase 1, Section D.2)
- $\text{EMA}(V, \text{lookback})_t$ = Exponential Moving Average of volume with period = `RVOL_LOOKBACK`

### C.2 — EMA Formula

$$\text{EMA}(V, n)_t = \alpha \cdot V_t + (1 - \alpha) \cdot \text{EMA}(V, n)_{t-1}$$

Where:
$$\alpha = \frac{2}{n + 1}$$

With $n = 20$ (initial parameter):
$$\alpha = \frac{2}{21} \approx 0.0952$$

### C.3 — Interpretation

| RVOL | Interpretation | Significance |
|------|---------------|-------------|
| < 0.5 | Very low volume | Low participation, potential indecision |
| 0.5 – 0.8 | Below average | Weak activity |
| 0.8 – 1.2 | Average | Normal activity |
| 1.2 – 1.5 | Above average | Elevated interest |
| 1.5 – 2.0 | High volume | Strong participation |
| 2.0 – 3.0 | Very high volume | Significant event or accumulation |
| > 3.0 | Extreme volume | Potential capitulation or climax |

### C.4 — Volume Source Selection

From Phase 1, Section D.2, the volume source is selected hierarchically:

$$V_t = \begin{cases}
V_{\text{composite},t} & \text{if all sources available} \\
V_{\text{broker},t} & \text{if broker real volume available} \\
V_{\text{tick},t} & \text{if only tick volume (default)}
\end{cases}$$

**Metadata:** Each RVOL value is tagged with its source for provenance.

### C.5 — Look-Ahead Prevention

RVOL at bar $t$ uses only volume data from bars $\{1, ..., t\}$. The EMA is computed sequentially with no future data.

---

## D — BUYING / SELLING PRESSURE

### D.1 — Raw Pressure (per bar)

#### Buying Pressure

$$\text{BP}_t = \frac{C_t - L_t}{H_t - L_t} \times V_t$$

This measures the proportion of the bar's range captured by buyers (close near high), weighted by volume.

**Interpretation:**
- $BP_t = V_t$: Close at High (maximum buying pressure)
- $BP_t = 0$: Close at Low (no buying pressure)
- $BP_t = 0.5 \times V_t$: Close at midpoint

#### Selling Pressure

$$\text{SP}_t = \frac{H_t - C_t}{H_t - L_t} \times V_t$$

This measures the proportion of the bar's range captured by sellers (close near low), weighted by volume.

**Interpretation:**
- $SP_t = V_t$: Close at Low (maximum selling pressure)
- $SP_t = 0$: Close at High (no selling pressure)
- $SP_t = 0.5 \times V_t$: Close at midpoint

### D.2 — Properties

$$\text{BP}_t + \text{SP}_t = V_t \quad \forall \, t$$

The total pressure equals the total volume. This is a **decomposition**, not independent measures.

### D.3 — Normalized Pressure

$$\text{BP}_{\text{norm},t} = \frac{C_t - L_t}{H_t - L_t}$$

$$\text{SP}_{\text{norm},t} = \frac{H_t - C_t}{H_t - L_t}$$

These are volume-independent measures of directional pressure.

**Edge Case:** If $H_t = L_t$ (doji), both $\text{BP}_{\text{norm}} = \text{SP}_{\text{norm}} = 0.5$.

### D.4 — Smoothed Pressure

To reduce noise, apply smoothing over $m$ bars:

$$\text{BP}_{\text{smooth},t} = \frac{1}{m} \sum_{i=0}^{m-1} \text{BP}_{t-i}$$

$$\text{SP}_{\text{smooth},t} = \frac{1}{m} \sum_{i=0}^{m-1} \text{SP}_{t-i}$$

Where $m = 3$ (initial parameter — `PRESSURE_SMOOTHING`).

### D.5 — Net Pressure

$$\text{NetPressure}_t = \text{BP}_{\text{smooth},t} - \text{SP}_{\text{smooth},t}$$

$$\text{NetPressure}_t \in [-V_{\text{total}}, +V_{\text{total}}]$$

Where $V_{\text{total}} = \sum_{i=0}^{m-1} V_{t-i}$.

---

## E — CANDLE EFFICIENCY

### E.1 — Definition

Candle Efficiency measures how effectively price moved through the bar's range:

$$\text{CE}_t = \frac{|C_t - O_t|}{H_t - L_t}$$

**Interpretation:**
- $\text{CE}_t = 1.0$: Full-range bar (close at extreme) — maximum efficiency
- $\text{CE}_t = 0.5$: Close at midpoint — moderate efficiency
- $\text{CE}_t = 0.0$: Close at open (doji) — zero efficiency

### E.2 — Directional Efficiency

For directional analysis:

$$\text{CE}_{\text{bull},t} = \frac{C_t - O_t}{H_t - L_t} \quad \text{(positive = bullish)}$$

$$\text{CE}_{\text{bear},t} = \frac{O_t - C_t}{H_t - L_t} \quad \text{(positive = bearish)}$$

### E.3 — Efficiency Classification

| CE | Classification | Interpretation |
|----|---------------|---------------|
| > 0.7 | High Efficiency | Strong directional move |
| 0.4 – 0.7 | Moderate Efficiency | Normal price action |
| 0.2 – 0.4 | Low Efficiency | Choppy / contested |
| < 0.2 | Very Low Efficiency | Doji / indecision |

### E.4 — Efficiency with Volume

The product of efficiency and volume gives a **conviction-weighted** measure:

$$\text{Conviction}_t = \text{CE}_t \times \text{RVOL}_t$$

High conviction = high efficiency + high volume = strong directional flow.

---

## F — VOLUME ACCELERATION

### F.1 — Definition

Volume Acceleration measures the rate of change in volume:

$$\text{VA}_t = \frac{V_t - V_{t-1}}{V_{t-1}}$$

Or equivalently:

$$\text{VA}_t = \frac{V_t}{V_{t-1}} - 1$$

### F.2 — Smoothed Acceleration

To reduce noise:

$$\text{VA}_{\text{smooth},t} = \frac{1}{n} \sum_{i=0}^{n-1} \text{VA}_{t-i}$$

Where $n = 5$ (initial parameter — `ACCELERATION_LOOKBACK`).

### F.3 — Acceleration Classification

| VA | Classification | Interpretation |
|----|---------------|---------------|
| > 0.5 | Rapid Acceleration | Volume surging (+50%+) |
| 0.2 – 0.5 | Moderate Acceleration | Volume increasing |
| -0.2 – 0.2 | Stable | Volume flat |
| -0.5 – -0.2 | Moderate Deceleration | Volume declining |
| < -0.5 | Rapid Deceleration | Volume collapsing |

### F.4 — Acceleration + Direction

Volume acceleration combined with price direction:

$$\text{VA}_{\text{bull},t} = \text{VA}_t \times \mathbb{1}[C_t > O_t]$$

$$\text{VA}_{\text{bear},t} = \text{VA}_t \times \mathbb{1}[C_t < O_t]$$

- $\text{VA}_{\text{bull},t} > 0$: Bullish volume accelerating (accumulation)
- $\text{VA}_{\text{bear},t} > 0$: Bearish volume accelerating (distribution)

---

## G — MOMENTUM/VOLUME RELATIONSHIP

### G.1 — Definition

The relationship between price momentum and volume reveals the quality of the move:

$$\text{MV\_Relationship}_t = \text{sign}(\Delta P_t) \times \text{sign}(\Delta V_t)$$

Where:
- $\Delta P_t = C_t - C_{t-1}$ (price change)
- $\Delta V_t = V_t - V_{t-1}$ (volume change)

### G.2 — Classification

| $\Delta P$ | $\Delta V$ | Relationship | Interpretation |
|------------|------------|-------------|---------------|
| + | + | **Confirmation** | Price up + Volume up = Strong bullish |
| + | - | **Divergence** | Price up + Volume down = Weak bullish |
| - | + | **Confirmation** | Price down + Volume down = Strong bearish |
| - | - | **Divergence** | Price down + Volume down = Weak bearish |

### G.3 — Quantitative Relationship

$$\text{MV\_Score}_t = \frac{\Delta P_t / P_{t-1}}{\text{ATR}_{14} / P_{t-1}} \times \frac{\Delta V_t / V_{t-1}}{\text{VA}_{\text{avg}}}$$

Where $\text{VA}_{\text{avg}}$ = average volume acceleration over lookback.

**Interpretation:**
- $|\text{MV\_Score}| > 1.0$: Strong relationship (momentum confirmed by volume)
- $|\text{MV\_Score}| < 0.5$: Weak relationship (momentum not confirmed)

---

## H — FLOW SCORE

### H.1 — Score Design

$$\text{FlowScore} \in [-100, +100]$$

Positive = Bullish Flow, Negative = Bearish Flow, Zero = Neutral.

### H.2 — Components

$$\text{FlowScore} = w_1 \cdot \text{Pressure}_{\text{score}} + w_2 \cdot \text{Efficiency}_{\text{score}} + w_3 \cdot \text{RVOL}_{\text{score}} + w_4 \cdot \text{Acceleration}_{\text{score}} + w_5 \cdot \text{MV}_{\text{score}}$$

| Component | Symbol | Definition | Weight |
|-----------|--------|-----------|--------|
| Net Pressure | $\text{Pressure}_{\text{score}}$ | Directional volume balance | $w_1 = 0.30$ |
| Candle Efficiency | $\text{Efficiency}_{\text{score}}$ | How effectively price moved | $w_2 = 0.25$ |
| Relative Volume | $\text{RVOL}_{\text{score}}$ | Volume intensity | $w_3 = 0.20$ |
| Volume Acceleration | $\text{Acceleration}_{\text{score}}$ | Volume trend | $w_4 = 0.10$ |
| Momentum/Volume | $\text{MV}_{\text{score}}$ | Relationship quality | $w_5 = 0.15$ |

### H.3 — Component Score Formulas

#### Net Pressure Score

$$\text{Pressure}_{\text{score}} = \frac{\text{BP}_{\text{smooth},t} - \text{SP}_{\text{smooth},t}}{V_{\text{total}}} \times 100$$

$$\text{Pressure}_{\text{score}} \in [-100, +100]$$

#### Candle Efficiency Score

$$\text{Efficiency}_{\text{score}} = \text{CE}_{\text{bull},t} \times \text{sign}(C_t - O_t) \times 100$$

$$\text{Efficiency}_{\text{score}} \in [-100, +100]$$

#### RVOL Score

$$\text{RVOL}_{\text{score}} = \begin{cases}
\min(100, (\text{RVOL}_t - 1) \times 50) & \text{if } \text{RVOL}_t > 1 \\
\max(-100, (1 - \text{RVOL}_t) \times (-50)) & \text{if } \text{RVOL}_t < 1
\end{cases}$$

**Note:** RVOL alone is not directional. The sign is determined by the candle direction:

$$\text{RVOL}_{\text{score}} = \text{sign}(C_t - O_t) \times \min(100, |\text{RVOL}_t - 1| \times 50)$$

#### Acceleration Score

$$\text{Acceleration}_{\text{score}} = \text{sign}(\Delta V_t) \times \text{sign}(C_t - O_t) \times \min(100, |\text{VA}_t| \times 100)$$

#### Momentum/Volume Score

$$\text{MV}_{\text{score}} = \text{sign}(\Delta P_t) \times \text{sign}(\Delta V_t) \times \min(100, |\text{MV\_Score}_t| \times 50)$$

### H.4 — Score Interpretation

| Score | Flow State | Description |
|-------|-----------|-------------|
| +80 to +100 | Strong Bullish Flow | Intense buying pressure with volume confirmation |
| +50 to +79 | Bullish Flow | Moderate buying pressure |
| +20 to +49 | Weak Bullish Flow | Slight bullish bias |
| -20 to +20 | Neutral Flow | Balanced or low-activity |
| -49 to -20 | Weak Bearish Flow | Slight bearish bias |
| -79 to -50 | Bearish Flow | Moderate selling pressure |
| -100 to -80 | Strong Bearish Flow | Intense selling pressure with volume confirmation |

---

## I — FLOW STATE CLASSIFICATION

### I.1 — States

| State | Definition | Indicators |
|-------|-----------|-----------|
| **Buying** | Net buying pressure with volume support | BP > SP, RVOL > 1.2, CE > 0.5 |
| **Selling** | Net selling pressure with volume support | SP > BP, RVOL > 1.2, CE > 0.5 |
| **Absorption** | High volume, small range, near level | RVOL > 1.5, Range/ATR < 0.5, NearLevel |
| **Exhaustion** | Extreme volume with diminishing returns | RVOL > 2.5, Range/ATR < 0.3, At extreme |
| **Continuation** | Flow consistent with prevailing direction | FlowScore aligned with structure |

### I.2 — State Detection Rules

#### Buying State

$$\text{Buying} \iff \text{BP}_{\text{smooth}} > \text{SP}_{\text{smooth}}$$

$$\wedge \quad \text{RVOL}_t > 1.2$$

$$\wedge \quad \text{CE}_t > 0.5$$

$$\wedge \quad \text{FlowScore} > +20$$

#### Selling State

$$\text{Selling} \iff \text{SP}_{\text{smooth}} > \text{BP}_{\text{smooth}}$$

$$\wedge \quad \text{RVOL}_t > 1.2$$

$$\wedge \quad \text{CE}_t > 0.5$$

$$\wedge \quad \text{FlowScore} < -20$$

#### Absorption State

$$\text{Absorption} \iff \text{RVOL}_t > \text{ABSORPTION\_RVOL\_THRESHOLD}$$

$$\wedge \quad \frac{H_t - L_t}{\text{ATR}_{14}} < \text{ABSORPTION\_RANGE\_THRESHOLD}$$

$$\wedge \quad \text{NearLevel}(C_t, \mathcal{L})$$

Where $\mathcal{L}$ = set of active liquidity levels from Phase 3.

**Absorption Direction:**

$$\text{AbsDir}_t = \begin{cases}
\text{BID\_ABSORPTION} & \text{if } C_t > O_t \text{ (sellers absorbed)} \\
\text{ASK\_ABSORPTION} & \text{if } C_t < O_t \text{ (buyers absorbed)}
\end{cases}$$

#### Exhaustion State

$$\text{Exhaustion} \iff \text{RVOL}_t > \text{EXHAUSTION\_RVOL\_THRESHOLD}$$

$$\wedge \quad \frac{H_t - L_t}{\text{ATR}_{14}} < \text{EXHAUSTION\_RANGE\_THRESHOLD}$$

$$\wedge \quad \text{AtPriceExtreme}(C_t)$$

Where `AtPriceExtreme` checks if the close is near a recent high/low.

**Exhaustion Type:**

$$\text{ExhType}_t = \begin{cases}
\text{BUYING\_EXHAUSTION} & \text{if } C_t \approx \text{recent high} + \text{high RVOL} + \text{small range} \\
\text{SELLING\_EXHAUSTION} & \text{if } C_t \approx \text{recent low} + \text{high RVOL} + \text{small range}
\end{cases}$$

#### Continuation State

$$\text{Continuation} \iff \text{FlowScore} \times \text{StructureState} > 0$$

$$\wedge \quad |\text{FlowScore}| > 30$$

$$\wedge \quad \text{RVOL}_t > 1.0$$

**Interpretation:** Flow direction matches structure direction with sufficient intensity.

### I.3 — State Priority

If multiple states could apply:

$$\text{Priority: Exhaustion} > \text{Absorption} > \text{Buying/Selling} > \text{Continuation}$$

Exhaustion and Absorption are **exceptional** states that override normal flow classification.

---

## J — EDGE CASES

### J.1 — Missing Volume Data

| Scenario | Handling | Risk |
|----------|----------|------|
| Volume = 0 for bar | Set RVOL = 0; flag `volume_missing` | Flow Score degraded |
| Volume data unavailable for > 3 bars | Skip Flow Score; flag `flow_disabled` | No flow context |
| Only tick volume available | Use tick volume; label `volume_type: "tick_proxy"` | Proxy limitations apply |

### J.2 — Price Anomalies

| Scenario | Handling |
|----------|----------|
| $H_t = L_t$ (doji) | CE = 0; Pressure = 50/50 split |
| $H_t = L_t = C_t$ (zero range) | All pressure/efficiency = 0; flag `zero_range` |
| Gap up/down | Use gap bar's range normally |

### J.3 — Extreme Values

| Scenario | Handling |
|----------|----------|
| RVOL > 10 | Cap at 10 for scoring; log as `extreme_volume` |
| CE > 1.0 (data error) | Cap at 1.0; flag `ce_error` |
| VA > 500% | Cap at 500% for scoring |

---

## K — BIAS PREVENTION

### K.1 — Look-Ahead Bias

**Prevention:**
1. EMA computation is sequential — no future data
2. Pressure, Efficiency, Acceleration computed per-bar only
3. Flow Score uses only current and past bar data

### K.2 — Double Counting (Rule 6)

**Prevention:**
1. Pressure and Efficiency are **independent** measures (volume-weighted vs. range-based)
2. RVOL is **directionally neutral** — it requires price direction for sign
3. Acceleration is the **rate of change** of RVOL, not a duplicate
4. MV Relationship is a **cross-check**, not a new signal

**Evidence Family:** All Flow components belong to the **Flow Evidence Family** and will be grouped in Phase 10 (Probability Engine).

### K.3 — Volume Type Contamination

**Prevention:**
1. Tick volume is labeled as proxy (Phase 1, Rule 3)
2. RVOL source is tracked in provenance
3. Flow Score carries a `volume_quality` flag

---

## L — BACKTESTABILITY

### L.1 — Backtest Requirements

| Requirement | Implementation |
|-------------|---------------|
| EMA sequential | Compute bar-by-bar, no batch |
| Pressure per bar | Use only bar's OHLCV + volume |
| Acceleration uses only past | $V_t / V_{t-1}$ — no future data |
| Absorption near level | Use only confirmed levels from Phase 3 |
| Exhaustion at extreme | Use only confirmed swing points from Phase 2 |

### L.2 — Backtest Data Flow

```
OHLCV + Volume
    ↓
RVOL (EMA-based)
    ↓
Buying/Selling Pressure
    ↓
Candle Efficiency
    ↓
Volume Acceleration
    ↓
MV Relationship
    ↓
Flow Score Computation
    ↓
Flow State Classification
    ↓
Final Flow Output
```

---

## M — WHAT IS FIXED

### M.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| RVOL Lookback | 20 bars | ~1 trading day on M5 |
| Pressure Smoothing | 3 bars | Reduces noise without lag |
| Acceleration Lookback | 5 bars | Captures short-term volume trend |
| Flow Score Weights | [0.30, 0.25, 0.20, 0.10, 0.15] | Pressure + Efficiency primary |
| Exhaustion RVOL Threshold | 2.5 | Extreme volume required |
| Exhaustion Range Threshold | 0.3 | Small range required |
| Absorption RVOL Threshold | 1.5 | Above-average volume |
| Absorption Range Threshold | 0.5 | Contained range |

### M.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal RVOL lookback | Phase 17 (Optimization) |
| Flow Score weight optimization | Phase 17 |
| Exhaustion/Absorption thresholds | Phase 17 |
| Pressure smoothing period | Phase 17 |
| Volume source selection weights | Phase 1 (storage analysis) |

---

## N — WHAT REQUIRES TESTING

### N.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | RVOL of 20 captures meaningful volume regime | Statistical analysis | Volume mean-reverts within 20 bars |
| H2 | Pressure scores correlate with short-term price direction | Compute correlation | ρ > 0.25 |
| H3 | Exhaustion events precede reversals | Statistical test | Reversal within 10 bars > 50% |
| H4 | Absorption near levels predicts directional moves | Backtest | Positive expectancy |
| H5 | Flow Score is independent of Structure Score | Correlation check | ρ < 0.3 |
| H6 | Candle Efficiency + RVOL (Conviction) is predictive | Feature importance | Top 5 feature |

### N.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Does tick volume RVOL correlate with real volume RVOL? | Test when both available |
| Q2 | Should exhaustion detection use session-specific thresholds? | Test per-session calibration |
| Q3 | Is 3-bar pressure smoothing optimal? | Test range [1–7] |
| Q4 | Can we detect absorption direction from tick data? | Research tick analysis |

---

## O — OUTPUT SCHEMA

### O.1 — Flow Output per Bar

```python
@dataclass(frozen=True)
class FlowOutput:
    """Flow analysis output for a single bar."""
    timestamp: datetime
    confirmation_timestamp: datetime
    
    # Volume
    rvol: float                        # Relative Volume
    volume_type: str                   # "tick_proxy", "broker_real", "exchange", "composite"
    
    # Pressure
    buying_pressure: float             # Raw BP
    selling_pressure: float            # Raw SP
    net_pressure: float                # Smoothed BP - SP
    pressure_score: float              # [-100, +100]
    
    # Efficiency
    candle_efficiency: float           # [0, 1]
    directional_efficiency: float      # [-1, +1]
    
    # Acceleration
    volume_acceleration: float         # Rate of change
    acceleration_score: float          # [-100, +100]
    
    # MV Relationship
    mv_relationship: str               # "confirmation", "divergence"
    mv_score: float                    # [-100, +100]
    
    # Aggregate
    flow_score: float                  # [-100, +100]
    flow_state: str                    # "buying", "selling", "absorption", "exhaustion", "continuation", "neutral"
    flow_direction: str                # "bullish", "bearish", "neutral"
    
    # Absorption/Exhaustion details
    absorption_type: str | None        # "bid_absorption", "ask_absorption"
    exhaustion_type: str | None        # "buying_exhaustion", "selling_exhaustion"
    
    # Quality
    volume_quality: str                # "verified", "tick_proxy", "degraded"
    
    # Provenance
    provenance: DataProvenance
```

---

## P — DECISION OUTPUT

### P.1 — Per-Bar Decision

```
Flow: Bullish (+62)
RVOL: 1.8 (Above Average, source: tick_proxy)
Pressure: BP=0.72, SP=0.28 (Net: +0.44)
Efficiency: 0.68 (High)
Acceleration: +0.15 (Moderate Increase)
MV: Confirmation (+0.85)
Flow State: Buying
Volume Quality: Tick Proxy
```

### P.2 — Absorption Event

```
[14:20] ABSORPTION detected @ 1843.20
  Type: BID_ABSORPTION
  RVOL: 2.1
  Range/ATR: 0.35
  Near Level: Swing Low @ 1842.50 (LS=72)
  Interpretation: Sellers absorbed by buyers near support
```

### P.3 — Exhaustion Event

```
[15:45] EXHAUSTION detected @ 1862.80
  Type: BUYING_EXHAUSTION
  RVOL: 3.2
  Range/ATR: 0.25
  At Extreme: Near Swing High @ 1863.00
  Interpretation: Buying climax, potential reversal
```

---

## Q — APPROVAL GATE

### The Phase 4 — Flow Engine specification is now complete.

**Summary of what is defined:**

1. ✅ Relative Volume (RVOL) with EMA formula
2. ✅ Buying/Selling Pressure (volume-weighted, smoothed)
3. ✅ Candle Efficiency (range-based)
4. ✅ Volume Acceleration (rate of change)
5. ✅ Momentum/Volume Relationship (confirmation/divergence)
6. ✅ Flow Score [-100, +100] with 5 weighted components
7. ✅ Flow State classification (Buying, Selling, Absorption, Exhaustion, Continuation)
8. ✅ Absorption detection with direction
9. ✅ Exhaustion detection with type
10. ✅ Edge cases and handling
11. ✅ Bias prevention (no double counting)
12. ✅ Backtest requirements
13. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **RVOL Lookback (20 bars):** Is this appropriate for M5 volume averaging?

2. **Pressure Smoothing (3 bars):** Too few, too many, or just right?

3. **Flow Score Weights:** Pressure 30%, Efficiency 25%, RVOL 20%, Acceleration 10%, MV 15% — acceptable?

4. **Exhaustion Thresholds:** RVOL > 2.5 + Range/ATR < 0.3 — appropriate for XAUUSD?

5. **Absorption Thresholds:** RVOL > 1.5 + Range/ATR < 0.5 — appropriate?

6. **State Priority:** Exhaustion > Absorption > Buying/Selling > Continuation — correct?

7. **Volume Proxy Labeling:** Is labeling tick volume as "tick_proxy" throughout acceptable?

8. **Double Counting Prevention:** Are the independence guarantees sufficient?

---

**Please review and approve (or request modifications) before I proceed to Phase 5 — Trend/Momentum/Volatility.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
