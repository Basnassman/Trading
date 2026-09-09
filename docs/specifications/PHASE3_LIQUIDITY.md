# PHASE 3 — LIQUIDITY ENGINE

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the mathematical framework for **Liquidity Analysis** — identifying where clusters of orders (stop losses, pending orders, institutional interest) are likely concentrated, and detecting when these levels are swept or absorbed.

This engine produces:
1. Liquidity Levels (static and dynamic)
2. Equal High/Low detection with ATR-based tolerance
3. Liquidity Clusters (aggregated nearby levels)
4. Liquidity Strength scoring
5. Liquidity Sweep detection (High/Low sweeps)
6. Sweep vs. Breakout vs. False Breakout classification
7. Sweep Strength scoring
8. Absorption detection

**Scope Boundary:**
- This engine operates on **price levels and order flow proxies**.
- Volume and flow analysis from Phase 4 provides inputs but is not duplicated here.
- The engine does **not** generate trading signals — it provides liquidity context.

---

## B — INPUTS

### B.1 — Required Data

| Data | Source | Reference |
|------|--------|-----------|
| OHLCV (all timeframes) | MT5 | Phase 1 |
| Swing Points | Phase 2 (Market Structure) | Phase 2 |
| Session boundaries | Phase 1 (timezone-aware) | Phase 1 |
| Tick data (bid/ask/volume) | MT5 | Phase 1 |
| ATR | Derived from OHLCV | Phase 5 input |

### B.2 — Parameters

| Parameter | Initial Value | Description |
|-----------|--------------|-------------|
| `EQHL_TOLERANCE_ATR` | 0.10 | ATR multiplier for Equal High/Low tolerance |
| `CLUSTER_DISTANCE_ATR` | 0.15 | ATR multiplier for cluster aggregation |
| `SWEEP_PENETRATION_MIN` | 0.02 | Minimum penetration beyond level (ATR fraction) |
| `SWEEP_RETURN_ATR` | 0.50 | Max ATR for sweep return speed |
| `ABSORPTION_VOLUME_THRESHOLD` | 1.5 | RVOL threshold for absorption |
| `LIQUIDITY_LOOKBACK_DAYS` | 5 | Days to look back for PDH/PDL/PWH/PWL |

---

## C — LIQUIDITY LEVELS

### C.1 — Level Types

| Level | Symbol | Definition | Update Frequency |
|-------|--------|-----------|-----------------|
| Previous Day High | $\text{PDH}$ | $H_{\text{yesterday}}$ | Daily |
| Previous Day Low | $\text{PDL}$ | $L_{\text{yesterday}}$ | Daily |
| Previous Week High | $\text{PWH}$ | $H_{\text{last\_week}}$ | Weekly |
| Previous Week Low | $\text{PWL}$ | $L_{\text{last\_week}}$ | Weekly |
| Asian High | $\text{AH}$ | $\max(H_t)$ during Asian session | Daily |
| Asian Low | $\text{AL}$ | $\min(L_t)$ during Asian session | Daily |
| London High | $\text{LH}$ | $\max(H_t)$ during London session | Daily |
| London Low | $\text{LL}$ | $\min(L_t)$ during London session | Daily |
| Swing High | $\text{SH}_i$ | From Phase 2 (confirmed) | Per swing |
| Swing Low | $\text{SL}_i$ | From Phase 2 (confirmed) | Per swing |
| Equal High | $\text{EQH}$ | See Section D | On detection |
| Equal Low | $\text{EQL}$ | See Section D | On detection |

### C.2 — Session Level Computation

For a given day and session $s$:

$$\text{SessionHigh}_s = \max_{t \in \text{Session}_s} H_t$$

$$\text{SessionLow}_s = \min_{t \in \text{Session}_s} L_t$$

**Session Definitions:** From Phase 1 (timezone-aware, DST-aware).

**Update Rule:** Session levels are finalized when the session closes.

### C.3 — Weekly Level Computation

$$\text{PWH} = \max_{t \in \text{LastWeek}} H_t$$

$$\text{PWL} = \min_{t \in \text{LastWeek}} L_t$$

**Week Definition:** Monday 00:00 UTC to Sunday 23:59 UTC (Forex week).

### C.4 — Level Availability (Phase 1 Compliance)

| Level | Available When | Backtest Rule |
|-------|---------------|---------------|
| PDH/PDL | After yesterday's session close | Use yesterday's data only |
| PWH/PWL | After last week's close | Use last week's data only |
| AH/AL | After Asian session close | Use Asian session data only |
| LH/LL | After London session close | Use London session data only |
| SH/SL | After Phase 2 confirmation ($k$ bars) | Phase 2 rules apply |
| EQH/EQL | On detection (see Section D) | Same rules as swing points |

---

## D — EQUAL HIGH / EQUAL LOW

### D.1 — Definition

Two swing highs are **Equal Highs** if their price difference is within a tolerance:

$$\text{EqualHigh}(s_i, s_j) \iff |s_i.\text{price} - s_j.\text{price}| \leq \tau_{\text{EQHL}}$$

Similarly for swing lows:

$$\text{EqualLow}(s_i, s_j) \iff |s_i.\text{price} - s_j.\text{price}| \leq \tau_{\text{EQHL}}$$

### D.2 — Tolerance Calculation

$$\tau_{\text{EQHL}} = \alpha \times \text{ATR}_{14}$$

Where $\alpha = 0.10$ (initial parameter).

**Justification:**
- 10% of ATR accounts for normal price variation around a level
- Too small (e.g., 0.01 ATR): Misses near-equal levels
- Too large (e.g., 0.30 ATR): Merges distinct levels

**Discussion of $\alpha = 0.10$:**

| $\alpha$ | Interpretation | Risk |
|----------|---------------|------|
| 0.05 | Very strict — only near-exact matches | Misses most equal levels |
| 0.10 | Moderate — captures meaningful equality | Balanced (chosen) |
| 0.15 | Loose — captures approximate equality | May merge distinct levels |
| 0.20 | Very loose — captures general area | High false positive rate |

### D.3 — Equal High/Low Properties

Each EQH/EQL carries:

| Property | Symbol | Description |
|----------|--------|-------------|
| Price Level | $P_{\text{EQ}}$ | Average of the two swing prices |
| Swing 1 | $s_i$ | First swing point |
| Swing 2 | $s_j$ | Second swing point |
| Tolerance Used | $\tau_{\text{EQHL}}$ | ATR-based tolerance at detection |
| Time Gap | $\Delta t$ | Time between the two swings |
| Touch Count | $n_{\text{touches}}$ | Number of swings at this level |

**Price Level Formula:**

$$P_{\text{EQ}} = \frac{s_i.\text{price} + s_j.\text{price}}{2}$$

### D.4 — Liquidity Significance of Equal Levels

Equal Highs/Lows indicate **stop loss clusters**:
- Traders place stops just above equal highs (for longs) or below equal lows (for shorts)
- Market makers may push price to "sweep" these stops before reversing
- The more touches, the more liquidity is concentrated

---

## E — LIQUIDITY CLUSTERS

### E.1 — Definition

A **Liquidity Cluster** is a group of nearby liquidity levels that fall within a distance threshold:

$$\text{Cluster}(L_1, L_2, ..., L_m) \iff \max(L_i) - \min(L_i) \leq \tau_{\text{cluster}}$$

Where:
- $L_i$ are liquidity levels (any type from Section C)
- $\tau_{\text{cluster}} = \delta \times \text{ATR}_{14}$
- $\delta = 0.15$ (initial parameter)

### E.2 — Clustering Algorithm

```
INPUT: Sorted list of liquidity levels L = [l₁, l₂, ..., lₙ]
OUTPUT: List of clusters C = [c₁, c₂, ..., cₘ]

1. Sort L by price (ascending)
2. Initialize clusters: C = []
3. For each level lᵢ in L:
   a. Find all levels within τ_cluster of lᵢ
   b. If no existing cluster contains these levels:
      - Create new cluster with these levels
   c. Add lᵢ to the nearest cluster
4. Merge overlapping clusters
5. Return C
```

### E.3 — Cluster Properties

| Property | Symbol | Formula |
|----------|--------|---------|
| Cluster Price | $P_{\text{cluster}}$ | Weighted average of member levels |
| Cluster Width | $W_{\text{cluster}}$ | $\max(L_i) - \min(L_i)$ |
| Member Count | $m$ | Number of levels in cluster |
| Independent Levels | $n_{\text{ind}}$ | Levels from different sources (not same swing) |
| Cluster Age | $A_{\text{cluster}}$ | Time since first level was formed |
| Tests | $T_{\text{cluster}}$ | Number of times price approached the cluster |

**Cluster Price Formula:**

$$P_{\text{cluster}} = \frac{\sum_{i=1}^{m} w_i \cdot L_i}{\sum_{i=1}^{m} w_i}$$

Where $w_i = \text{strength}(L_i)$ (see Section F).

### E.4 — Cluster Significance

| Member Count | Independent Levels | Significance |
|-------------|-------------------|-------------|
| 1 | 1 | Single level — moderate |
| 2–3 | 2+ | Small cluster — significant |
| 4–6 | 3+ | Medium cluster — high |
| 7+ | 4+ | Large cluster — very high |

---

## F — LIQUIDITY STRENGTH SCORE

### F.1 — Score Design

$$\text{LS} \in [0, 100]$$

The score reflects the **significance** of a liquidity level or cluster.

### F.2 — Components

$$\text{LS} = w_1 \cdot N_{\text{norm}} + w_2 \cdot A_{\text{norm}} + w_3 \cdot T_{\text{norm}} + w_4 \cdot R_{\text{norm}} + w_5 \cdot S_{\text{norm}}$$

| Component | Symbol | Definition | Weight |
|-----------|--------|-----------|--------|
| Number of Levels | $N_{\text{norm}}$ | How many levels are at this area | $w_1 = 0.25$ |
| Age | $A_{\text{norm}}$ | How long the level has existed | $w_2 = 0.15$ |
| Touches/Tests | $T_{\text{norm}}$ | How many times price tested this level | $w_3 = 0.25$ |
| Source Diversity | $R_{\text{norm}}$ | How many different level types contribute | $w_4 = 0.15$ |
| Structure Alignment | $S_{\text{norm}}$ | Alignment with Phase 2 structure | $w_5 = 0.20$ |

### F.3 — Component Formulas

#### Number of Levels Score

$$N_{\text{norm}} = \min\left(1, \frac{m}{m_{\text{max}}}\right)$$

Where $m$ = member count, $m_{\text{max}} = 8$ (initial).

#### Age Score

$$A_{\text{norm}} = \min\left(1, \frac{A_{\text{cluster}}}{A_{\text{max}}}\right)$$

Where $A_{\text{cluster}}$ = age in bars, $A_{\text{max}} = 100$ bars on primary TF.

**Interpretation:** Older levels have more accumulated orders.

#### Touches/Tests Score

$$T_{\text{norm}} = \min\left(1, \frac{T_{\text{cluster}}}{T_{\text{max}}}\right)$$

Where $T_{\text{cluster}}$ = number of tests, $T_{\text{max}} = 5$.

**Interpretation:** Each test "refreshes" the level and adds more orders.

#### Source Diversity Score

$$R_{\text{norm}} = \frac{n_{\text{ind}}}{n_{\text{types}}}$$

Where:
- $n_{\text{ind}}$ = number of independent level types (e.g., Swing + PDH + EQH = 3)
- $n_{\text{types}} = 5$ (Swing, Session, Weekly, Daily, Equal)

#### Structure Alignment Score

$$S_{\text{norm}} = \begin{cases}
1.0 & \text{if level aligns with Phase 2 structure state} \\
0.5 & \text{if level is in Transition state} \\
0.0 & \text{if level contradicts structure}
\end{cases}$$

**Alignment Definition:**
- Bullish structure + support level (swing low, PDL, etc.) = aligned
- Bearish structure + resistance level (swing high, PDH, etc.) = aligned
- Bullish structure + resistance level = contradictory

### F.4 — Score Interpretation

| Score | Significance | Description |
|-------|-------------|-------------|
| 80–100 | Very High | Major liquidity zone, high institutional interest |
| 60–79 | High | Significant level, multiple confirmations |
| 40–59 | Moderate | Notable level, some confirmation |
| 20–39 | Low | Minor level, limited significance |
| 0–19 | Negligible | Minimal liquidity interest |

---

## G — LIQUIDITY SWEEP

### G.1 — Definition

A **Liquidity Sweep** occurs when price temporarily breaks beyond a liquidity level, triggering stop losses, and then reverses back.

**Key Distinction:**
- Sweep = temporary break + reversal
- Breakout = sustained break + continuation
- False Breakout = failed breakout (similar to sweep but different context)

### G.2 — High Sweep (Sweep of Buy-Side Liquidity)

$$\text{HighSweep}(t) \iff H_t > L_{\text{level}} + \tau_{\text{penetration}}$$

$$\text{AND} \quad C_t < L_{\text{level}}$$

$$\text{AND} \quad \text{Return within } n \text{ bars}$$

Where:
- $L_{\text{level}}$ = Liquidity level (swing high, PDH, EQH, etc.)
- $\tau_{\text{penetration}} = \beta \times \text{ATR}_{14}$, $\beta = 0.02$ (minimum penetration)
- Return: Price closes back below the level within $n$ bars

**Interpretation:** Price poked above the level (triggering buy-side stops), then reversed.

### G.3 — Low Sweep (Sweep of Sell-Side Liquidity)

$$\text{LowSweep}(t) \iff L_t < L_{\text{level}} - \tau_{\text{penetration}}$$

$$\text{AND} \quad C_t > L_{\text{level}}$$

$$\text{AND} \quad \text{Return within } n \text{ bars}$$

**Interpretation:** Price poked below the level (triggering sell-side stops), then reversed.

### G.4 — Sweep Confirmation Window

The "return" must occur within a defined window:

$$\text{ReturnConfirmed} \iff \exists \, t' \in [t+1, t+n] : C_{t'} \text{ is on the opposite side of } L_{\text{level}}$$

Where $n = 5$ bars on primary timeframe (initial parameter).

**If no return within $n$ bars:** The event is reclassified as a **Breakout** (Section H).

### G.5 — Sweep Properties

| Property | Symbol | Description |
|----------|--------|-------------|
| Sweep Type | $\text{SweepType}$ | `HIGH_SWEEP` or `LOW_SWEEP` |
| Level Swept | $L_{\text{level}}$ | The liquidity level that was swept |
| Penetration Depth | $D_{\text{pen}}$ | How far beyond the level price went |
| Return Time | $\Delta t_{\text{return}}$ | Bars until price returned |
| Level Strength | $\text{LS}$ | Liquidity Strength of the swept level |

---

## H — SWEEP vs. BREAKOUT vs. FALSE BREAKOUT

### H.1 — Classification Matrix

| Event | Penetration | Close Beyond? | Return Within $n$ Bars? | Continuation? | Classification |
|-------|------------|--------------|------------------------|---------------|---------------|
| **Sweep** | ✅ Yes | ❌ No | ✅ Yes | N/A | Liquidity Sweep |
| **Breakout** | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes | Valid Breakout |
| **False Breakout** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No | Failed Breakout |
| **Wick Only** | ✅ Yes | ❌ No | ❌ No (stays beyond) | ❌ No | Incomplete — reclassify after window |

### H.2 — Formal Definitions

#### Sweep

$$\text{Sweep} \iff \text{Penetration} \wedge \neg\text{CloseBeyond} \wedge \text{ReturnWithin}_n$$

**Characteristics:**
- Wick beyond level, close back inside
- Reversal within $n$ bars
- Often followed by move in opposite direction

#### Breakout

$$\text{Breakout} \iff \text{Penetration} \wedge \text{CloseBeyond} \wedge \neg\text{ReturnWithin}_n$$

**Characteristics:**
- Close beyond the level
- No return within $n$ bars
- Price continues in breakout direction

#### False Breakout

$$\text{FalseBreakout} \iff \text{Penetration} \wedge \text{CloseBeyond} \wedge \text{ReturnWithin}_n \wedge \neg\text{Continuation}$$

**Characteristics:**
- Initially closes beyond the level
- But returns within $n$ bars
- Does not continue in breakout direction

### H.3 — Decision Tree

```
Price beyond level?
├── NO → No event
└── YES →
    ├── Close beyond level?
    │   ├── NO →
    │   │   └── Return within n bars?
    │   │       ├── YES → SWEEP
    │   │       └── NO → Wick Only (reclassify after window)
    │   └── YES →
    │       └── Return within n bars?
    │           ├── YES → FALSE BREAKOUT
    │           └── NO → BREAKOUT
```

### H.4 — Time Window for Classification

The classification requires waiting $n$ bars after the penetration event:

$$\text{ClassificationTime} = \tau_{\text{penetration}} + n \times \text{bar\_duration}$$

**Backtest Rule:** The system must wait $n$ bars before classifying the event. No premature classification.

---

## I — SWEEP STRENGTH SCORE

### I.1 — Score Design

$$\text{SweepStrength} \in [0, 100]$$

The score reflects the **quality and significance** of a liquidity sweep.

### I.2 — Components

$$\text{SweepStrength} = w_1 \cdot P_{\text{norm}} + w_2 \cdot R_{\text{norm}} + w_3 \cdot V_{\text{norm}} + w_4 \cdot S_{\text{norm}} + w_5 \cdot T_{\text{norm}}$$

| Component | Symbol | Definition | Weight |
|-----------|--------|-----------|--------|
| Penetration Depth | $P_{\text{norm}}$ | How far beyond the level | $w_1 = 0.20$ |
| Rejection Strength | $R_{\text{norm}}$ | How strongly price rejected the level | $w_2 = 0.25$ |
| Volume Confirmation | $V_{\text{norm}}$ | Volume during the sweep | $w_3 = 0.20$ |
| Structure Alignment | $S_{\text{norm}}$ | Alignment with Phase 2 structure | $w_4 = 0.20$ |
| Return Speed | $T_{\text{norm}}$ | How quickly price returned | $w_5 = 0.15$ |

### I.3 — Component Formulas

#### Penetration Depth Score

$$P_{\text{norm}} = \min\left(1, \frac{D_{\text{pen}}}{D_{\text{max}}}\right)$$

Where $D_{\text{pen}}$ = penetration distance, $D_{\text{max}} = 0.5 \times \text{ATR}_{14}$.

**Interpretation:** Moderate penetration is ideal — too shallow may be noise, too deep may indicate genuine breakout.

#### Rejection Strength Score

$$R_{\text{norm}} = \frac{|C_t - H_t|}{H_t - L_t} \quad \text{(for High Sweep)}$$

$$R_{\text{norm}} = \frac{|C_t - L_t|}{H_t - L_t} \quad \text{(for Low Sweep)}$$

This measures how far the close is from the extreme of the sweep bar:
- $R_{\text{norm}} = 1.0$: Close at opposite extreme (strong rejection)
- $R_{\text{norm}} = 0.0$: Close at the extreme (weak rejection)

#### Volume Confirmation Score

$$V_{\text{norm}} = \min\left(1, \frac{\text{RVOL}_{\text{sweep}}}{2.0}\right)$$

Where $\text{RVOL}_{\text{sweep}}$ = relative volume during the sweep bar.

**Interpretation:** High volume during the sweep indicates genuine stop hunting.

#### Structure Alignment Score

$$S_{\text{norm}} = \begin{cases}
1.0 & \text{if sweep aligns with Phase 2 structure direction} \\
0.5 & \text{if neutral alignment} \\
0.0 & \text{if sweep contradicts structure}
\end{cases}$$

**Alignment:**
- Bullish structure + Low Sweep (sweeping sell-side stops) = aligned
- Bearish structure + High Sweep (sweeping buy-side stops) = aligned

#### Return Speed Score

$$T_{\text{norm}} = \max\left(0, 1 - \frac{\Delta t_{\text{return}}}{n_{\text{max}}}\right)$$

Where $\Delta t_{\text{return}}$ = bars to return, $n_{\text{max}} = 5$.

**Interpretation:** Faster return = stronger sweep signal.

### I.4 — Score Interpretation

| Score | Quality | Description |
|-------|---------|-------------|
| 80–100 | Strong | High-quality sweep with multiple confirmations |
| 60–79 | Moderate | Decent sweep, some confirmation |
| 40–59 | Weak | Marginal sweep, limited confirmation |
| 20–39 | Very Weak | Likely noise |
| 0–19 | Invalid | Does not meet minimum sweep criteria |

---

## J — ABSORPTION

### J.1 — Definition

**Absorption** occurs when large orders absorb selling/buying pressure without significant price movement. This is a proxy for institutional activity.

**Critical Note (Rule 3 Compliance):**
Absorption detected via tick volume is a **proxy** for institutional order flow, not confirmed institutional flow. True absorption detection requires order book data.

### J.2 — Potential Absorption Detection

$$\text{PotentialAbsorption}(t) \iff \text{HighVolume}(t) \wedge \text{SmallRange}(t) \wedge \text{NearLevel}(t)$$

Where:

$$\text{HighVolume}(t) \iff \text{RVOL}_t > \text{ABS\_THRESHOLD}$$

$$\text{SmallRange}(t) \iff \frac{H_t - L_t}{\text{ATR}_{14}} < \text{range\_threshold}$$

$$\text{NearLevel}(t) \iff \min_{l \in \mathcal{L}} |C_t - l| < \tau_{\text{proximity}}$$

Where:
- $\text{ABS\_THRESHOLD} = 1.5$ (initial)
- $\text{range\_threshold} = 0.5$ (initial)
- $\tau_{\text{proximity}} = 0.10 \times \text{ATR}_{14}$
- $\mathcal{L}$ = set of active liquidity levels

### J.3 — Absorption Properties

| Property | Symbol | Description |
|----------|--------|-------------|
| Absorption Type | $\text{AbsType}$ | `BID_ABSORPTION` or `ASK_ABSORPTION` |
| Level | $L_{\text{abs}}$ | Liquidity level where absorption occurred |
| Volume | $\text{RVOL}$ | Relative volume during absorption |
| Range Ratio | $\text{RangeRatio}$ | Bar range / ATR |
| Direction | $\text{AbsDir}$ | Buying or Selling pressure being absorbed |

### J.4 — Absorption vs. Sweep

| Feature | Absorption | Sweep |
|---------|-----------|-------|
| Volume | High | High |
| Range | Small (contained) | Large (penetration) |
| Close | Near level | Opposite side of level |
| Interpretation | Orders being filled | Stops being triggered |

---

## K — EDGE CASES

### K.1 — Missing Levels

| Scenario | Handling |
|----------|----------|
| No swing points yet | Use only static levels (PDH/PDL etc.) |
| Session not yet closed | Use current session's developing levels |
| Weekly data unavailable | Skip PWH/PWL; flag quality |

### K.2 — Level Conflicts

| Scenario | Handling |
|----------|----------|
| Two levels very close | Merge into cluster |
| Level at exact same price as another | Treat as single level with higher strength |

### K.3 — Sweep Ambiguity

| Scenario | Handling |
|----------|----------|
| Multiple levels swept simultaneously | Record all swept levels |
| Sweep of cluster | Record cluster-level sweep |
| Price returns to level multiple times | Each return counts as separate test |

### K.4 — Rapid Sweeps

| Scenario | Handling |
|----------|----------|
| Sweep, return, sweep again within $n$ bars | Record both sweeps; increase level strength |

---

## L — BIAS PREVENTION

### L.1 — Look-Ahead Bias

**Prevention:**
1. Session levels finalized only after session closes
2. Swing points confirmed per Phase 2 rules ($k$-bar delay)
3. Sweep classification requires waiting $n$ bars for return confirmation
4. In backtesting, all level availability rules enforced strictly

### L.2 — Repainting

**Prevention:**
1. Once a liquidity level is identified, it is frozen
2. Sweep classification is final after the $n$-bar window
3. Cluster composition does not change after formation

### L.3 — Double Counting

**Prevention:**
1. Volume in Absorption is a **proxy**, not institutional flow (Rule 3)
2. Structure alignment uses Phase 2 output, not duplicated structure analysis
3. Level strength uses independent metrics (count, age, touches, diversity, alignment)

---

## M — BACKTESTABILITY

### M.1 — Backtest Requirements

| Requirement | Implementation |
|-------------|---------------|
| Session level timing | Only use levels after session closes |
| Swing point confirmation | Phase 2 $k$-bar delay applies |
| Sweep classification delay | Wait $n$ bars before classifying |
| Absorption detection | Real-time only; no future data |
| Cluster formation | Only from confirmed levels |

### M.2 — Backtest Data Flow

```
OHLCV + Session Data
    ↓
Static Levels (PDH/PDL/PWH/PWL/AH/AL/LH/LL)
    ↓
Swing Points (from Phase 2)
    ↓
Equal High/Low Detection
    ↓
Level Aggregation → Clusters
    ↓
Liquidity Strength Scoring
    ↓
Sweep Detection
    ↓
Sweep Classification (wait n bars)
    ↓
Sweep Strength Scoring
    ↓
Absorption Detection
    ↓
Final Liquidity Output
```

---

## N — WHAT IS FIXED

### N.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| EQHL Tolerance | 0.10 ATR | Balances precision vs. coverage |
| Cluster Distance | 0.15 ATR | Groups meaningful nearby levels |
| Sweep Penetration Min | 0.02 ATR | Minimum meaningful break |
| Sweep Return Window | 5 bars | Balances confirmation vs. timeliness |
| Absorption Volume Threshold | 1.5 RVOL | Above-average volume required |
| LS Score Weights | [0.25, 0.15, 0.25, 0.15, 0.20] | Touches + Count most important |
| Sweep Strength Weights | [0.20, 0.25, 0.20, 0.20, 0.15] | Rejection most important |

### N.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal EQHL tolerance | Phase 17 (Optimization) |
| Optimal cluster distance | Phase 17 |
| Sweep return window | Phase 17 |
| Absorption thresholds | Phase 17 |
| LS/Sweep Score weights | Phase 17 |
| Absorption direction detection | Phase 4 (Flow Engine) |

---

## O — WHAT REQUIRES TESTING

### O.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | EQHL tolerance of 0.10 ATR captures meaningful equal levels | Visual inspection + backtest | > 70% of identified EQHL are significant |
| H2 | Cluster distance of 0.15 ATR groups related levels | Statistical analysis | Clusters have higher LS than individual levels |
| H3 | Sweep detection has lower false positive than breakout | Backtest both | Sweep win rate > breakout win rate |
| H4 | Sweep Strength correlates with reversal probability | Compute correlation | ρ > 0.3 |
| H5 | Absorption near levels precedes price moves | Statistical test | Absorption events have directional predictive value |
| H6 | 5-bar return window is appropriate | Test range [3–10] | Optimal in [4–7] range |

### O.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Should absorption detection use tick volume or OHLCV? | Test both approaches |
| Q2 | Can we detect absorption direction (bid vs. ask)? | Requires tick-level data analysis |
| Q3 | How to handle sweeps of clusters vs. individual levels? | Implement both; test which is more predictive |
| Q4 | Should sweep strength include time-of-day component? | Test session-specific calibration |

---

## P — OUTPUT SCHEMA

### P.1 — Liquidity Output per Bar

```python
@dataclass(frozen=True)
class LiquidityOutput:
    """Liquidity analysis output for a single bar."""
    timestamp: datetime
    confirmation_timestamp: datetime
    
    # Active Levels
    active_levels: list[LiquidityLevel]
    active_clusters: list[LiquidityCluster]
    
    # Sweep Detection
    sweep_detected: bool
    sweep_type: str | None          # "high_sweep" or "low_sweep" or None
    sweep_level: LiquidityLevel | None
    sweep_strength: float | None    # [0, 100]
    sweep_penetration: float | None
    sweep_return_bars: int | None
    
    # Breakout Detection
    breakout_detected: bool
    breakout_type: str | None       # "bullish_breakout" or "bearish_breakout"
    breakout_level: LiquidityLevel | None
    
    # False Breakout Detection
    false_breakout_detected: bool
    
    # Absorption
    absorption_detected: bool
    absorption_type: str | None     # "bid_absorption" or "ask_absorption"
    absorption_level: LiquidityLevel | None
    
    # Aggregate
    nearest_support: float | None
    nearest_resistance: float | None
    liquidity_score: float          # Aggregate [-100, +100]
    
    # Provenance
    provenance: DataProvenance
```

### P.2 — Liquidity Level Schema

```python
@dataclass(frozen=True)
class LiquidityLevel:
    """A single liquidity level."""
    level_type: str                 # "pdh", "pdl", "swing_high", "eqh", etc.
    price: float
    strength: float                 # [0, 100]
    timestamp: datetime             # When level was formed
    source: str                     # "session", "swing", "equal", "weekly"
    touch_count: int
    last_test: datetime | None
```

### P.3 — Liquidity Cluster Schema

```python
@dataclass(frozen=True)
class LiquidityCluster:
    """A cluster of nearby liquidity levels."""
    price: float                    # Weighted average
    width: float                    # Price range
    member_count: int
    independent_levels: int
    strength: float                 # [0, 100]
    age_bars: int
    levels: tuple[LiquidityLevel, ...]  # Member levels
```

---

## Q — DECISION OUTPUT

### Q.1 — Per-Bar Decision

```
Liquidity: Bullish Bias (+45)
Nearest Support: 1842.50 (Swing Low, LS=72)
Nearest Resistance: 1858.30 (EQH Cluster, LS=85)
Active Clusters: 3
Sweep: None
Absorption: Potential Bid Absorption @ 1843.20 (RVOL=1.8)
```

### Q.2 — Sweep Event

```
[14:35] HIGH SWEEP detected @ 1858.50
  Level: EQH @ 1858.30 (LS=85)
  Penetration: 0.20 pips (0.02 ATR)
  Return: 3 bars
  Sweep Strength: 78
  Structure Alignment: Yes (Bearish structure + buy-side sweep)
```

---

## R — APPROVAL GATE

### The Phase 3 — Liquidity Engine specification is now complete.

**Summary of what is defined:**

1. ✅ All Liquidity Levels (PDH, PDL, PWH, PWL, AH, AL, LH, LL, SH, SL, EQH, EQL)
2. ✅ Equal High/Low with ATR-based tolerance (0.10 ATR)
3. ✅ Liquidity Clusters with aggregation algorithm
4. ✅ Liquidity Strength Score (0–100) with 5 components
5. ✅ Liquidity Sweep detection (High/Low) with mathematical conditions
6. ✅ Sweep vs. Breakout vs. False Breakout classification with decision tree
7. ✅ Sweep Strength Score (0–100) with 5 components
8. ✅ Absorption detection with proxy limitations
9. ✅ Edge cases and handling
10. ✅ Bias prevention measures
11. ✅ Backtest requirements
12. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **EQHL Tolerance (0.10 ATR):** Does this capture meaningful equal levels for XAUUSD?

2. **Cluster Distance (0.15 ATR):** Is this appropriate for grouping nearby levels?

3. **Sweep Return Window (5 bars):** Is this enough time for confirmation?

4. **Sweep Minimum Penetration (0.02 ATR):** Too small, too large, or just right?

5. **LS Score Weights:** Touches 25%, Count 25%, Structure 20%, Age 15%, Diversity 15% — acceptable?

6. **Sweep Strength Weights:** Rejection 25%, Penetration 20%, Volume 20%, Structure 20%, Speed 15% — acceptable?

7. **Absorption Proxy Limitation:** Is it acceptable to label tick-volume absorption as "potential" only?

8. **Sweep Classification Delay:** Waiting 5 bars before classifying — acceptable for backtest integrity?

---

**Please review and approve (or request modifications) before I proceed to Phase 4 — Flow Engine.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
