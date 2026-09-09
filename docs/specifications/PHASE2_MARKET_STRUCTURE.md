# PHASE 2 — MARKET STRUCTURE ENGINE

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the mathematical framework for analyzing **Market Structure** — the sequence of swing highs, swing lows, and their relationships that reveal the underlying directional bias of price movement.

This engine produces:
1. Swing points (Highs and Lows) with confirmation timestamps
2. Structure classification (HH, HL, LH, LL)
3. Structure state (Bullish, Bearish, Transition, Compression, Neutral)
4. Break of Structure (BOS) detection with strength scoring
5. Market Structure Shift / Change of Character (MSS/CHoCH) detection
6. Multi-Timeframe structure aggregation

**Scope Boundary:**
- This engine operates on **price structure only**.
- Volume, momentum, and flow are handled by their respective engines (Phase 4, Phase 5).
- The engine does **not** generate trading signals — it provides structural context.

---

## B — INPUTS

### B.1 — Required Data

| Data | Source | Timeframes | Reference |
|------|--------|-----------|-----------|
| OHLCV | MT5 (Phase 1, Section C) | D1, H4, H1, M15, M5 | Phase 1 |
| Bar timestamps | MT5 | All | Phase 1 |
| Session boundaries | Phase 1 (timezone-aware) | All | Phase 1 |

### B.2 — Parameters

| Parameter | Initial Value | Description |
|-----------|--------------|-------------|
| `k` | 3 | Fractal lookback/lookahead for swing confirmation |
| `BOS_tolerance` | 0.05 ATR | Minimum break distance for BOS confirmation |
| `MSS_tolerance` | 0.10 ATR | Minimum break distance for MSS/CHoCH |
| `Structure_MA_period` | 50 | Moving average for structure smoothing (optional) |

---

## C — MATHEMATICAL DEFINITIONS

### C.1 — Swing Points (Fractal Logic)

#### Swing High

**Definition:** A bar $t$ is a **Swing High** if and only if:

$$\text{SwingHigh}(t) \iff H_{t-j} < H_t \quad \forall \, j \in \{1, 2, ..., k\}$$

$$\text{AND} \quad H_{t+j} < H_t \quad \forall \, j \in \{1, 2, ..., k\}$$

Where:
- $H_t$ = High price at bar $t$
- $k$ = Fractal parameter (initial value: 3)
- The bar must have $k$ lower highs on **both** sides

**In words:** Bar $t$ is a swing high if its high is higher than the $k$ bars before it AND higher than the $k$ bars after it.

#### Swing Low

**Definition:** A bar $t$ is a **Swing Low** if and only if:

$$\text{SwingLow}(t) \iff L_{t-j} > L_t \quad \forall \, j \in \{1, 2, ..., k\}$$

$$\text{AND} \quad L_{t+j} > L_t \quad \forall \, j \in \{1, 2, ..., k\}$$

Where:
- $L_t$ = Low price at bar $t$
- $k$ = Fractal parameter (initial value: 3)

**In words:** Bar $t$ is a swing low if its low is lower than the $k$ bars before it AND lower than the $k$ bars after it.

#### Swing Point Properties

Each swing point carries:

| Property | Symbol | Type | Description |
|----------|--------|------|-------------|
| Type | $\text{SP\_type}$ | Enum | `SWING_HIGH` or `SWING_LOW` |
| Timestamp | $\tau_{\text{SP}}$ | datetime | Bar timestamp of the swing |
| Price | $P_{\text{SP}}$ | float | $H_t$ for swing high, $L_t$ for swing low |
| Confirmation Time | $\tau_{\text{confirm}}$ | datetime | When the swing was confirmed ($\tau_{\text{SP}} + k$ bars) |
| Strength | $\text{SP\_strength}$ | float [0,1] | See Section C.2 |

### C.2 — Swing Strength

A swing's strength reflects how "clean" the pivot is:

$$\text{SP\_strength} = \frac{1}{k} \sum_{j=1}^{k} \left( \frac{|H_t - H_{t-j}|}{H_t} + \frac{|H_t - H_{t+j}|}{H_t} \right) \times \frac{1}{2}$$

**Interpretation:**
- Higher values = sharper reversal (more significant swing)
- Lower values = gradual reversal (less significant swing)
- Normalized to [0, 1] by clamping

### C.3 — Look-Ahead Prevention (Critical — Rule 4)

**The Problem:**
If a swing high is at bar $t$ with $k=3$, the system needs bars $t+1, t+2, t+3$ to confirm it. During backtesting, these bars are in the "future" relative to $t$.

**The Rule:**

$$\text{SwingHigh}(t) \text{ is ONLY available for analysis at time } \tau_{t+k}$$

$$\text{SwingLow}(t) \text{ is ONLY available for analysis at time } \tau_{t+k}$$

**Formal Statement:**

$$\forall \, \text{bar } t: \quad \text{SwingPoint}(t) \notin \mathcal{F}_{\tau_{t+j}} \quad \forall \, j < k$$

Where $\mathcal{F}_{\tau}$ is the information set available at time $\tau$.

**Implementation Rules:**

| Rule | Description |
|------|-------------|
| R1 | Swing at bar $t$ confirmed at bar $t+k$ |
| R2 | No swing data is used before confirmation time |
| R3 | In backtesting, the confirmation delay is enforced exactly as in live |
| R4 | The confirmation timestamp $\tau_{\text{confirm}} = \tau_t + k \times \text{bar\_duration}$ is stored with each swing |
| R5 | If $k$ bars are missing (gap), the swing is marked as `confirmation_uncertain` |

**Example (M5, k=3):**

```
Bar 100: H=1850.00 (potential swing high)
Bar 101: H=1849.50 < 1850.00 ✓
Bar 102: H=1848.80 < 1850.00 ✓
Bar 103: H=1849.20 < 1850.00 ✓ (confirmation complete)

→ Swing High at bar 100 confirmed at bar 103
→ Available for analysis from bar 103 onward
→ NOT available at bar 100, 101, or 102
```

### C.4 — Swing Point Sequence

Let $\mathcal{S} = \{s_1, s_2, ..., s_n\}$ be the ordered sequence of confirmed swing points, where each $s_i$ has:
- Type: $s_i.\text{type} \in \{\text{HIGH}, \text{LOW}\}$
- Price: $s_i.\text{price}$
- Timestamp: $s_i.\tau$
- Confirmation: $s_i.\tau_{\text{confirm}}$

**Alternation Rule:**
In a well-formed structure, swing highs and lows alternate:

$$s_i.\text{type} \neq s_{i+1}.\text{type} \quad \forall \, i$$

If two consecutive swings have the same type, the system keeps only the more extreme one:
- Two consecutive Swing Highs → keep the higher one
- Two consecutive Swing Lows → keep the lower one

---

## D — STRUCTURE CLASSIFICATION

### D.1 — Swing High Comparison

Given two consecutive swing highs $s_i$ and $s_j$ (where $s_i$ precedes $s_j$):

$$\text{CompareHighs}(s_i, s_j) = \begin{cases}
\text{HH} & \text{if } s_j.\text{price} > s_i.\text{price} \\
\text{LH} & \text{if } s_j.\text{price} < s_i.\text{price} \\
\text{EH} & \text{if } s_j.\text{price} = s_i.\text{price}
\end{cases}$$

Where:
- **HH** = Higher High
- **LH** = Lower High
- **EH** = Equal High (see Phase 3 for Equal High/Low liquidity)

### D.2 — Swing Low Comparison

Given two consecutive swing lows $s_i$ and $s_j$:

$$\text{CompareLows}(s_i, s_j) = \begin{cases}
\text{HL} & \text{if } s_j.\text{price} > s_i.\text{price} \\
\text{LL} & \text{if } s_j.\text{price} < s_i.\text{price} \\
\text{EL} & \text{if } s_j.\text{price} = s_i.\text{price}
\end{cases}$$

Where:
- **HL** = Higher Low
- **LL** = Lower Low
- **EL** = Equal Low

### D.3 — Structure Label Sequence

The structure is described by the sequence of comparisons:

$$\mathcal{C} = \{c_1, c_2, ..., c_m\}$$

Where each $c_i \in \{\text{HH, HL, LH, LL, EH, EL}\}$.

**Example:**

```
Swing sequence: SH₁(1800) → SL₁(1780) → SH₂(1820) → SL₂(1790) → SH₃(1840)

Comparisons:
SH₁ → SH₂: HH (1820 > 1800)
SL₁ → SL₂: HL (1790 > 1780)
SH₂ → SH₃: HH (1840 > 1820)

Structure: HH → HL → HH → ... (Bullish Structure)
```

---

## E — STRUCTURE STATE

### E.1 — State Definitions

The **Structure State** is a function of the recent swing comparison sequence:

$$\text{StructureState} = f(\mathcal{C}_{\text{recent}})$$

Where $\mathcal{C}_{\text{recent}}$ is the last $n$ comparisons (initial $n = 4$).

#### Bullish Structure

$$\text{Bullish} \iff \text{Last } n \text{ comparisons contain at least } \lceil n/2 \rceil \text{ HH or HL}$$

$$\text{AND} \quad \text{No LL in last 2 comparisons}$$

**Formal:**

$$\text{Bullish} \iff \sum_{i=m-n+1}^{m} \mathbb{1}[c_i \in \{\text{HH}, \text{HL}\}] \geq \lceil n/2 \rceil$$

$$\text{AND} \quad c_{m} \neq \text{LL} \quad \text{AND} \quad c_{m-1} \neq \text{LL}$$

#### Bearish Structure

$$\text{Bearish} \iff \text{Last } n \text{ comparisons contain at least } \lceil n/2 \rceil \text{ LH or LL}$$

$$\text{AND} \quad \text{No HH in last 2 comparisons}$$

**Formal:**

$$\text{Bearish} \iff \sum_{i=m-n+1}^{m} \mathbb{1}[c_i \in \{\text{LH}, \text{LL}\}] \geq \lceil n/2 \rceil$$

$$\text{AND} \quad c_{m} \neq \text{HH} \quad \text{AND} \quad c_{m-1} \neq \text{HH}$$

#### Transition State

$$\text{Transition} \iff \neg\text{Bullish} \quad \text{AND} \quad \neg\text{Bearish}$$

$$\text{AND} \quad \text{Last comparison is HL after LL (potential bullish)}$$

$$\text{OR} \quad \text{Last comparison is LH after HH (potential bearish)}$$

**Formal:**

$$\text{Transition} \iff (c_m = \text{HL} \wedge c_{m-1} = \text{LL}) \vee (c_m = \text{LH} \wedge c_{m-1} = \text{HH})$$

#### Compression State

$$\text{Compression} \iff \text{Last } n \text{ comparisons alternate frequently}$$

$$\text{AND} \quad \max(\mathcal{H}_{\text{recent}}) - \min(\mathcal{L}_{\text{recent}}) < \text{ATR} \times \text{compression\_threshold}$$

Where:
- $\mathcal{H}_{\text{recent}}$ = set of recent swing high prices
- $\mathcal{L}_{\text{recent}}$ = set of recent swing low prices
- `compression_threshold` = 1.5 (initial parameter)

**Interpretation:** Price is range-bound with contracting swings.

#### Neutral State

$$\text{Neutral} \iff \neg\text{Bullish} \wedge \neg\text{Bearish} \wedge \neg\text{Transition} \wedge \neg\text{Compression}$$

This occurs when there is insufficient data or mixed signals.

### E.2 — State Transition Diagram

```
                    ┌──────────────┐
                    │   Neutral    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Bullish  │ │Compressn │ │Bearish   │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │             │            │
             ▼             ▼            ▼
        ┌──────────────────────────────────┐
        │         Transition               │
        │  (Bullish→Bearish or vice versa) │
        └──────────────────────────────────┘
```

### E.3 — State Output

| State | Score Range | Description |
|-------|-----------|-------------|
| Bullish | +60 to +100 | Uptrend: HH + HL pattern |
| Bearish | -60 to -100 | Downtrend: LH + LL pattern |
| Transition | -30 to +30 | Direction change in progress |
| Compression | -20 to +20 | Range-bound, contracting |
| Neutral | -10 to +10 | Insufficient data |

---

## F — BREAK OF STRUCTURE (BOS)

### F.1 — Definition

A **Break of Structure** occurs when price closes beyond a significant swing point, confirming a continuation of the prevailing structure.

**Critical Rule:** BOS requires **Close-based confirmation**, not merely a wick penetration.

### F.2 — Bullish BOS

$$\text{BullishBOS} \iff C_t > s_{\text{last\_high}}.\text{price} + \text{BOS\_tolerance}$$

Where:
- $C_t$ = Close price at bar $t$
- $s_{\text{last\_high}}$ = Most recent swing high before bar $t$
- $\text{BOS\_tolerance} = 0.05 \times \text{ATR}_{14}$ (initial)

**Conditions:**
1. Close must exceed the swing high + tolerance
2. The swing high must be confirmed (not potential)
3. Structure state should be Bullish or Transition

### F.3 — Bearish BOS

$$\text{BearishBOS} \iff C_t < s_{\text{last\_low}}.\text{price} - \text{BOS\_tolerance}$$

Where:
- $s_{\text{last\_low}}$ = Most recent swing low before bar $t$
- $\text{BOS\_tolerance} = 0.05 \times \text{ATR}_{14}$ (initial)

### F.4 — BOS vs. Wick Penetration

| Scenario | Close > Swing High + Tol? | Wick > Swing High? | Result |
|----------|--------------------------|--------------------|----|
| Strong close above | ✅ Yes | ✅ Yes | **Valid BOS** |
| Wick above, close below | ❌ No | ✅ Yes | **NOT BOS** — Wick only |
| Close above, no wick | ✅ Yes | ✅ Yes | **Valid BOS** |
| Neither | ❌ No | ❌ No | **No BOS** |

**Why close-based?**
- Wick-only breaks are often fakeouts
- Close-based confirmation reduces false signals
- Institutional orders typically push price to close beyond levels

### F.5 — BOS Tolerance

$$\text{BOS\_tolerance} = \beta \times \text{ATR}_{14}$$

Where $\beta = 0.05$ (initial parameter).

**Justification:** 5% of ATR ensures the break is meaningful relative to current volatility, not just noise.

**Alternative:** Fixed pip tolerance (e.g., 0.50 pips for XAUUSD), but ATR-based is preferred for adaptiveness.

---

## G — MSS / CHoCH (Market Structure Shift / Change of Character)

### G.1 — Definitions

**MSS (Market Structure Shift):**
A shift in the internal structure that suggests the prevailing trend may be weakening, but hasn't necessarily reversed.

**CHoCH (Change of Character):**
A stronger signal — the first break against the prevailing structure, suggesting a potential direction change.

### G.2 — Bullish MSS / CHoCH

$$\text{BullishMSS} \iff C_t > s_{\text{last\_swing\_low}}.\text{price} + \text{MSS\_tolerance}$$

$$\text{AND} \quad \text{StructureState} \in \{\text{Bearish}, \text{Transition}\}$$

**Interpretation:** In a bearish structure, price closes above the last swing low + tolerance. This suggests sellers are losing control.

**Formal:**

$$\text{BullishCHoCH} \iff \text{BullishMSS} \wedge (c_m = \text{LL} \text{ or } c_m = \text{LH})$$

i.e., The MSS occurs while the structure was still making lower lows or lower highs.

### G.3 — Bearish MSS / CHoCH

$$\text{BearishMSS} \iff C_t < s_{\text{last\_swing\_high}}.\text{price} - \text{MSS\_tolerance}$$

$$\text{AND} \quad \text{StructureState} \in \{\text{Bullish}, \text{Transition}\}$$

$$\text{BearishCHoCH} \iff \text{BearishMSS} \wedge (c_m = \text{HH} \text{ or } c_m = \text{HL})$$

### G.4 — MSS vs. CHoCH vs. BOS

| Event | What It Means | Strength | Use Case |
|-------|--------------|----------|----------|
| **BOS** | Structure continuation confirmed | Medium | Trend following |
| **MSS** | Structure weakening | Medium | Caution / Prepare |
| **CHoCH** | Potential direction change | High | Reversal setup |

### G.5 — MSS Tolerance

$$\text{MSS\_tolerance} = \gamma \times \text{ATR}_{14}$$

Where $\gamma = 0.10$ (initial parameter).

**Why larger than BOS tolerance?**
- MSS/CHoCH represent a break against the prevailing structure
- Require stronger confirmation to avoid false signals
- 10% of ATR is a meaningful level break

### G.6 — Continuation vs. Direction Change

| Condition | Interpretation | Action |
|-----------|---------------|--------|
| BOS in trend direction | Continuation confirmed | Follow trend |
| MSS against trend | Trend weakening | Reduce confidence |
| CHoCH against trend | Direction change likely | Prepare for reversal |
| MSS then BOS back in trend | False CHoCH | Resume trend |

---

## H — BOS STRENGTH SCORE

### H.1 — Score Design

$$\text{BOS\_Score} \in [0, 100]$$

The score reflects the **quality and conviction** of the break.

### H.2 — Components

$$\text{BOS\_Score} = w_1 \cdot D_{\text{norm}} + w_2 \cdot C_{\text{norm}} + w_3 \cdot V_{\text{norm}} + w_4 \cdot M_{\text{norm}}$$

Where:

| Component | Symbol | Definition | Weight |
|-----------|--------|-----------|--------|
| Break Distance | $D_{\text{norm}}$ | How far price broke beyond the level | $w_1 = 0.30$ |
| Close Strength | $C_{\text{norm}}$ | How strong the close was relative to the bar | $w_2 = 0.30$ |
| Volume Confirmation | $V_{\text{norm}}$ | Volume relative to average (RVOL) | $w_3 = 0.20$ |
| Momentum Alignment | $M_{\text{norm}}$ | Momentum direction matches BOS direction | $w_4 = 0.20$ |

**Note on Double Counting (Rule 6):**
Volume and Momentum are inputs from Phase 4 and Phase 5 respectively. The BOS Score uses them as **confirmation signals**, not as primary drivers. The primary driver is price structure (Distance + Close Strength = 60% weight).

### H.3 — Component Formulas

#### Break Distance Score

$$D_{\text{norm}} = \min\left(1, \frac{|C_t - s_{\text{level}}|}{\text{ATR}_{14}} \times \frac{1}{\text{distance\_factor}}\right)$$

Where `distance_factor` = 0.5 (initial). This normalizes the break distance as a fraction of ATR.

#### Close Strength Score

$$C_{\text{norm}} = \frac{|C_t - O_t|}{H_t - L_t}$$

This measures how much of the bar's range was captured by the close:
- $C_{\text{norm}} = 1.0$: Close at the extreme (full-range bar)
- $C_{\text{norm}} = 0.5$: Close at midpoint
- $C_{\text{norm}} = 0.0$: Close at open (doji — weak confirmation)

**Direction adjustment:**
- For Bullish BOS: Use $(C_t - O_t) / (H_t - L_t)$ (positive = bullish)
- For Bearish BOS: Use $(O_t - C_t) / (H_t - L_t)$ (positive = bearish)

#### Volume Confirmation Score

$$V_{\text{norm}} = \min\left(1, \frac{\text{RVOL}_t}{2.0}\right)$$

Where $\text{RVOL}_t = V_t / \text{EMA}(V, 20)_t$ (Phase 1 formula).

- RVOL = 2.0 → $V_{\text{norm}} = 1.0$ (full score)
- RVOL = 1.0 → $V_{\text{norm}} = 0.5$
- RVOL = 0.5 → $V_{\text{norm}} = 0.25$

**Note:** Uses tick volume or composite volume as available (Phase 1, Section D.2).

#### Momentum Alignment Score

$$M_{\text{norm}} = \begin{cases}
\min(1, \frac{\text{RSI}_t - 50}{50}) & \text{for Bullish BOS} \\
\min(1, \frac{50 - \text{RSI}_t}{50}) & \text{for Bearish BOS}
\end{cases}$$

Where $\text{RSI}_t$ is the 14-period RSI (Phase 5 input).

- RSI = 70 → Bullish BOS gets $M_{\text{norm}} = 0.4$
- RSI = 50 → $M_{\text{norm}} = 0$ (no alignment)
- RSI = 30 → Bearish BOS gets $M_{\text{norm}} = 0.4$

### H.4 — Score Interpretation

| Score Range | Quality | Description |
|-------------|---------|-------------|
| 80–100 | Strong | High-conviction BOS with multiple confirmations |
| 60–79 | Moderate | Decent BOS, some confirmation |
| 40–59 | Weak | Marginal BOS, limited confirmation |
| 20–39 | Very Weak | Likely noise, low confidence |
| 0–19 | Invalid | Does not meet minimum BOS criteria |

### H.5 — Minimum BOS Score Threshold

$$\text{BOS}_{\text{valid}} \iff \text{BOS\_Score} \geq \text{BOS\_min\_score}$$

Where `BOS_min_score` = 40 (initial parameter).

BOS events with scores below this threshold are logged but not used for structure classification.

---

## I — MULTI-TIMEFRAME STRUCTURE

### I.1 — Rationale

Market structure operates on multiple timeframes simultaneously. A bullish structure on M5 may coexist with a bearish structure on H4. The system must combine these views.

### I.2 — Timeframe Hierarchy

| Timeframe | Role | Weight |
|-----------|------|--------|
| D1 | Primary trend direction | 30% |
| H4 | Intermediate structure | 30% |
| H1 | Short-term structure | 20% |
| M15 | Micro structure | 15% |
| M5 | Execution timing | 5% |

**Initial Weights:**

$$W = [0.30, 0.30, 0.20, 0.15, 0.05]$$

**Note (Rule 7):** These weights are initial parameters. Optimization happens in Phase 17.

### I.3 — Per-Timeframe Structure Score

For each timeframe $tf$, compute a structure score:

$$\text{StructScore}_{tf} = \begin{cases}
+100 & \text{if Bullish state} \\
-100 & \text{if Bearish state} \\
\text{linear interpolation} & \text{if Transition} \\
0 & \text{if Neutral or Compression}
\end{cases}$$

### I.4 — Aggregated Structure Score

$$\text{AggStructScore} = \sum_{i=1}^{5} W_i \times \text{StructScore}_{tf_i}$$

$$\text{AggStructScore} \in [-100, +100]$$

### I.5 — Multi-Timeframe BOS

BOS events on different timeframes carry different significance:

| Timeframe BOS | Significance | Holding Time Impact |
|---------------|-------------|-------------------|
| D1 BOS | Very High | Weeks to months |
| H4 BOS | High | Days to weeks |
| H1 BOS | Medium | Hours to days |
| M15 BOS | Low-Medium | Minutes to hours |
| M5 BOS | Low | Minutes |

**Rule:** A BOS on a higher timeframe overrides lower timeframes for structure state.

### I.6 — Timeframe Conflict Resolution

When timeframes disagree:

| Scenario | Resolution |
|----------|-----------|
| D1 Bullish + H4 Bearish | D1 dominates for direction; H4 for entry timing |
| D1 Bearish + H4 Bullish | D1 dominates for direction; look for short entries |
| H1 Bullish + M15 Bearish | H1 for direction; M15 for entry refinement |
| All timeframes agree | Highest conviction signal |

**Formal Rule:**

$$\text{DominantStructure} = \text{argmax}_{tf}(\text{weight}_{tf}) \text{ where } \text{StructScore}_{tf} \neq 0$$

If no timeframe has a clear structure → state = Neutral.

---

## J — EDGE CASES

### J.1 — Insufficient Swing Data

| Scenario | Handling |
|----------|----------|
| Fewer than 3 swing points | State = Neutral, insufficient data |
| Fewer than 5 swing points | Structure classification is `provisional` |
| Gap in swing data | Flag, use available swings |

### J.2 — Equal Swings

| Scenario | Handling |
|----------|----------|
| Two consecutive swing highs at same price | Keep the later one (more recent) |
| $|H_{s_i} - H_{s_j}| < \text{point}/2$ | Treat as Equal High (Phase 3 handles this) |

### J.3 — Rapid State Changes

| Scenario | Handling |
|----------|----------|
| State changes every bar | Flag as Choppy; consider Compression state |
| More than 3 state changes in 20 bars | Reduce confidence in structure signals |

### J.4 — Session Transitions

| Scenario | Handling |
|----------|----------|
| Swing confirmed during session transition | Use the bar's session classification |
| BOS across session boundary | Valid if close confirms |

---

## K — BIAS PREVENTION

### K.1 — Look-Ahead Bias

**Prevention:**
1. Swing confirmation requires $k$ future bars
2. BOS requires close confirmation (same bar, no future data)
3. MSS/CHoCH uses only confirmed swing points
4. In backtesting, all structure data is available only after confirmation time

### K.2 — Repainting

**Prevention:**
1. Once a swing is confirmed, its price and timestamp are frozen
2. Structure state at time $t$ depends only on swings confirmed by time $t$
3. No retroactive reclassification of past states

### K.3 — Double Counting

**Prevention:**
1. Volume and Momentum in BOS Score are **confirmation** inputs, not primary drivers
2. Structure Score is price-only; it does not include volume or momentum
3. Evidence Families (Phase 10) will explicitly separate Structure from Flow/Momentum

---

## L — BACKTESTABILITY

### L.1 — Backtest Requirements

| Requirement | Implementation |
|-------------|---------------|
| Swing confirmation delay | Enforce $k$-bar delay exactly as live |
| BOS close confirmation | Use only bar close, not future bars |
| MSS/CHoCH timing | Only after swing confirmation |
| State computation | Only from confirmed swings |
| Multi-TF alignment | Each TF computed independently with its own delay |

### L.2 — Backtest Data Flow

```
OHLCV (per timeframe)
    ↓
Swing Detection (with k-bar delay)
    ↓
Swing Confirmation (at τ + k bars)
    ↓
Structure Classification (HH/HL/LH/LL)
    ↓
Structure State (Bullish/Bearish/Transition/Compression/Neutral)
    ↓
BOS Detection (Close-based)
    ↓
BOS Strength Scoring
    ↓
MSS/CHoCH Detection
    ↓
Multi-TF Aggregation
    ↓
Final Structure Output
```

---

## M — WHAT IS FIXED

### M.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Fractal parameter $k$ | 3 | Industry standard for swing detection |
| BOS confirmation method | Close-based | Prevents fakeouts from wick-only breaks |
| BOS tolerance | 0.05 ATR | Meaningful break relative to volatility |
| MSS tolerance | 0.10 ATR | Stronger confirmation for direction change |
| BOS minimum score | 40 | Filter weak/marginal BOS events |
| Timeframe set | D1, H4, H1, M15, M5 | Multi-timeframe coverage |
| MTF weights | [0.30, 0.30, 0.20, 0.15, 0.05] | Initial, subject to optimization |
| BOS Score weights | [0.30, 0.30, 0.20, 0.20] | Price-primary, no double counting |
| State lookback | Last $n=4$ comparisons | Balances responsiveness vs. noise |

### M.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal $k$ value | Phase 17 (Optimization) |
| BOS/MSS tolerance optimization | Phase 17 |
| MTF weight optimization | Phase 17 |
| BOS Score weight optimization | Phase 17 |
| Compression threshold | Phase 17 |
| Volume source for BOS Score | Phase 4 (Flow Engine) |
| Momentum source for BOS Score | Phase 5 (Momentum Engine) |

---

## N — WHAT REQUIRES TESTING

### N.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | k=3 captures meaningful swings on M5 | Visual inspection + statistical analysis | > 80% of identified swings are "significant" |
| H2 | Close-based BOS reduces fakeouts vs. wick-based | Backtest both methods | Close-based has higher hit rate |
| H3 | BOS tolerance of 0.05 ATR is appropriate | Test range [0.01–0.10] ATR | Optimal in [0.03–0.07] range |
| H4 | MSS tolerance of 0.10 ATR is appropriate | Test range [0.05–0.20] ATR | Optimal in [0.07–0.15] range |
| H5 | MTF weights reflect actual predictive power | Feature importance analysis | D1/H4 most important |
| H6 | BOS Score correlates with continuation probability | Compute correlation | ρ > 0.3 |
| H7 | Structure state transitions are informative | Analyze state duration and transitions | Average state duration > 10 bars |

### N.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Is k=3 optimal for all timeframes, or should k vary by TF? | Test k=2,3,4 per timeframe |
| Q2 | Should BOS tolerance be fixed or adaptive? | Test both approaches |
| Q3 | How many state transitions are too many (choppy filter)? | Analyze historical data |
| Q4 | Should Equal Highs/Lows be handled differently in structure? | Defer to Phase 3 |

---

## O — OUTPUT SCHEMA

### O.1 — Structure Output per Bar

```python
@dataclass(frozen=True)
class StructureOutput:
    """Market Structure analysis output for a single bar."""
    timestamp: datetime                    # Bar timestamp
    confirmation_timestamp: datetime       # When this output became available
    
    # Swing Points
    last_swing_high: SwingPoint | None     # Most recent confirmed swing high
    last_swing_low: SwingPoint | None      # Most recent confirmed swing low
    swing_count: int                       # Total confirmed swings
    
    # Structure Classification
    last_comparison: str                   # HH, HL, LH, LL, EH, EL
    comparison_sequence: list[str]         # Last n comparisons
    
    # Structure State
    state: str                             # Bullish, Bearish, Transition, Compression, Neutral
    state_score: float                     # [-100, +100]
    
    # BOS
    bos_detected: bool                     # True if BOS occurred at this bar
    bos_type: str | None                   # "bullish_bos" or "bearish_bos" or None
    bos_score: float | None                # [0, 100] or None
    bos_level: float | None                # Price level that was broken
    
    # MSS/CHoCH
    mss_detected: bool                     # True if MSS occurred
    choch_detected: bool                   # True if CHoCH occurred
    mss_type: str | None                   # "bullish_mss" or "bearish_mss" or None
    
    # Multi-Timeframe
    mtf_score: float                       # Aggregated structure score [-100, +100]
    mtf_state: str                         # Dominant timeframe state
    per_tf_scores: dict[str, float]        # Score per timeframe
    
    # Provenance
    provenance: DataProvenance             # From Phase 1
```

### O.2 — Swing Point Schema

```python
@dataclass(frozen=True)
class SwingPoint:
    """A confirmed swing point."""
    type: str                              # "swing_high" or "swing_low"
    price: float                           # H_t or L_t
    timestamp: datetime                    # Bar timestamp
    confirmation_timestamp: datetime       # τ + k bars
    strength: float                        # [0, 1]
    bar_index: int                         # Index in the data array
```

---

## P — DECISION OUTPUT

### P.1 — Per-Bar Decision

For each bar, the engine outputs:

```
Structure: Bullish (+78)
Last Swing: High @ 1852.30 (confirmed at 10:15 UTC)
Last Comparison: HH (1852.30 > 1848.50)
BOS: None
MSS: None
MTF Score: +65 (D1: +90, H4: +80, H1: +50, M15: +30, M5: +20)
```

### P.2 — Key Events

```
[10:15] Swing High confirmed @ 1852.30 (strength: 0.82)
[10:35] BOS Bullish @ 1853.10 (score: 72, break: 0.80, close: 0.85, vol: 0.60, mom: 0.55)
[11:00] MSS Bullish detected (price closed above last swing low + tolerance)
```

---

## Q — APPROVAL GATE

### The Phase 2 — Market Structure Engine specification is now complete.

**Summary of what is defined:**

1. ✅ Swing High/Low mathematical definition (fractal logic, k=3)
2. ✅ Swing Strength calculation
3. ✅ Look-Ahead Prevention (k-bar confirmation delay)
4. ✅ Structure Classification (HH, HL, LH, LL, EH, EL)
5. ✅ Structure State equations (Bullish, Bearish, Transition, Compression, Neutral)
6. ✅ BOS definition with Close-based confirmation
7. ✅ BOS Tolerance (0.05 ATR)
8. ✅ MSS/CHoCH definitions with tolerance (0.10 ATR)
9. ✅ Continuation vs. Direction Change logic
10. ✅ BOS Strength Score (0–100) with 4 components
11. ✅ Multi-Timeframe Structure with weighted aggregation
12. ✅ Timeframe conflict resolution
13. ✅ Edge cases and handling
14. ✅ Bias prevention measures
15. ✅ Backtest requirements
16. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **Fractal k=3:** Is this the right starting value for XAUUSD M5? Should it vary by timeframe?

2. **Close-Based BOS:** Is the close-only confirmation acceptable, or do you want wick-based as an option?

3. **BOS Tolerance (0.05 ATR):** Does this seem appropriate for meaningful structure breaks?

4. **MSS Tolerance (0.10 ATR):** Is 2x the BOS tolerance appropriate for direction changes?

5. **BOS Score Weights:** Price structure at 60% (Distance + Close), Volume 20%, Momentum 20% — acceptable?

6. **MTF Weights:** D1=30%, H4=30%, H1=20%, M15=15%, M5=5% — acceptable as starting point?

7. **Structure State Lookback:** Last 4 comparisons — too few, too many, or just right?

8. **BOS Minimum Score:** 40/100 — appropriate threshold for valid BOS?

---

**Please review and approve (or request modifications) before I proceed to Phase 3 — Liquidity Engine.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
