# PHASE 6 — GOLD SMART INDEX (GSI v1.0)

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the **Gold Smart Index (GSI)** — a composite score that aggregates all analytical engines into a single directional metric for XAUUSD.

$$\text{GSI} \in [-100, +100]$$

**Critical Clarification (Rule 5):**
- GSI is **NOT** a probability.
- GSI does **NOT** tell you "80% chance of going up."
- GSI is a **normalized composite score** that measures the strength and direction of evidence.
- Probability computation happens in Phase 10 (Probability Engine), using GSI as **one input among many**.

**Scope Boundary:**
- GSI aggregates outputs from Phase 2–5.
- GSI does not incorporate News/Macro (Phase 7), Historical (Phase 8), or Regime (Phase 9).
- Those are added in Phase 10 (Probability Engine).

---

## B — INPUTS

### B.1 — Component Scores (from Previous Phases)

| Component | Symbol | Source | Range |
|-----------|--------|--------|-------|
| Market Structure | $S_{\text{struct}}$ | Phase 2 | [-100, +100] |
| Trend | $S_{\text{trend}}$ | Phase 5 (Trend Engine) | [-100, +100] |
| Momentum | $S_{\text{momentum}}$ | Phase 5 (Momentum Engine) | [-100, +100] |
| Volatility | $S_{\text{volatility}}$ | Phase 5 (Volatility Engine) | [-100, +100] |
| Flow | $S_{\text{flow}}$ | Phase 4 | [-100, +100] |
| Price Action | $S_{\text{PA}}$ | Derived (see Section D) | [-100, +100] |

### B.2 — Parameters

| Parameter | Initial Value | Description |
|-----------|--------------|-------------|
| GSI Weights | See Section D | Component weights |
| GSI Smoothing | 3 bars | EMA smoothing of raw GSI |
| GSI Confidence Threshold | ±30 | Minimum |GSI| for directional signal |

---

## C — GSI FUNDAMENTAL PROPERTIES

### C.1 — What GSI Is

| Property | Description |
|----------|-------------|
| Directional Metric | Positive = bullish evidence, Negative = bearish evidence |
| Strength Metric | Magnitude = how strong the evidence is |
| Composite Score | Aggregates multiple independent(ish) engines |
| Normalized | All components on [-100, +100] scale |
| Causal | Uses only confirmed, past data |

### C.2 — What GSI Is NOT

| Property | Description |
|----------|-------------|
| NOT a Probability | Does not output "X% chance of success" |
| NOT a Signal | Does not directly generate entry/exit |
| NOT Static | Weights are initial; optimization in Phase 17 |
| NOT Independent | Components have documented overlaps |

### C.3 — GSI vs. Probability (Critical Distinction)

$$\text{GSI} \neq P(\text{Long}) \neq P(\text{Short})$$

GSI is an **evidence score**. Probability is a **calibrated likelihood** computed in Phase 10 using:

- GSI (as one evidence family)
- News/Macro evidence
- Historical similarity evidence
- Regime context

**Analogy:**
- GSI = "The symptoms suggest flu" (qualitative strength)
- Probability = "There is a 75% chance it is flu" (quantitative likelihood, calibrated against base rate)

---

## D — GSI FORMULA

### D.1 — Raw GSI

$$\text{GSI}_{\text{raw}} = \sum_{i=1}^{6} w_i \cdot S_i$$

Where $S_i$ are the component scores and $w_i$ are the weights:

$$\sum_{i=1}^{6} w_i = 1.0$$

### D.2 — Initial Weights

| Component $i$ | Symbol | Weight $w_i$ | Justification |
|---------------|--------|-------------|---------------|
| Market Structure | $S_{\text{struct}}$ | **0.25** | Primary directional context; defines the "playing field" |
| Flow | $S_{\text{flow}}$ | **0.20** | Volume confirms or denies structure; second most important |
| Trend | $S_{\text{trend}}$ | **0.15** | Smoothed directional bias; complements structure |
| Momentum | $S_{\text{momentum}}$ | **0.15** | Rate of change; confirms trend strength |
| Price Action | $S_{\text{PA}}$ | **0.15** | Bar-level quality; recent behavior |
| Volatility | $S_{\text{volatility}}$ | **0.10** | Context modifier, not directional; lower weight |

### D.3 — Weight Justification (Detailed)

#### Market Structure (25%)

**Why highest weight?**
- Structure defines the **framework** within which all other analysis operates
- Without structure context, momentum and flow signals are ambiguous
- Structure is the most **stable** signal (changes slowly)
- Phase 2 produces the most rigorous mathematical definitions

**Risk:** Structure can lag during rapid reversals. Mitigated by MSS/CHoCH detection.

#### Flow (20%)

**Why second highest?**
- Volume confirms or denies price action
- Flow captures **participation** — the "conviction" behind moves
- Flow and Structure together form the **core evidence pair**
- Flow can signal exhaustion before structure changes

**Risk:** Tick volume is a proxy (Rule 3). Mitigated by provenance tracking.

#### Trend (15%)

**Why moderate weight?**
- Trend (EMA-based) **complements** Structure (swing-based) — different mechanisms
- Trend provides **smoothed** directional bias
- Lower weight because it partially overlaps with Structure

**Double Counting Risk:** Trend and Structure both measure direction. Mitigated by:
- Structure uses **discrete swing points**; Trend uses **continuous EMA**
- They can diverge (structure transitioning, EMA still trending)
- Weight is moderate (15%) to reflect partial overlap

#### Momentum (15%)

**Why moderate weight?**
- Momentum confirms **rate of change** — is the move accelerating or decelerating?
- RSI provides **extreme detection** (overbought/oversold)
- MACD provides **trend-following momentum**

**Double Counting Risk:** Momentum overlaps with Trend (both measure "speed"). Mitigated by:
- Trend measures **direction** (where); Momentum measures **rate** (how fast)
- Different mathematical formulations (EMA crossover vs. RSI/MACD)
- Weight is moderate (15%) to reflect overlap

#### Price Action (15%)

**Why moderate weight?**
- Price Action captures **bar-level quality** (efficiency, rejection, acceptance)
- It's the most **immediate** signal (single-bar behavior)
- Complements longer-term Structure and Trend

**Derivation:** See Section D.4.

#### Volatility (10%)

**Why lowest weight?**
- Volatility is **not directional** — it measures dispersion, not direction
- Volatility **modifies** the interpretation of other signals
- High volatility = wider stops, lower position size (Phase 12)
- Low volatility = potential breakout setup
- Lowest weight because it's a **context modifier**, not a primary signal

**Special Case:** When Volatility is extreme (> +60 or < -60), it should trigger caution flags in the No-Trade Engine (Phase 14), not directly affect GSI direction.

### D.4 — Price Action Score Derivation

Price Action is not a separate engine — it's derived from existing components:

$$S_{\text{PA}} = w_{\text{PA},1} \cdot \text{CE}_{\text{score}} + w_{\text{PA},2} \cdot \text{Rejection}_{\text{score}} + w_{\text{PA},3} \cdot \text{CandlePattern}_{\text{score}}$$

| Sub-Component | Weight | Source |
|---------------|--------|--------|
| Candle Efficiency | 0.40 | Phase 4 (CE) |
| Rejection Strength | 0.30 | Phase 3 (Sweep rejection) |
| Candle Pattern | 0.30 | Derived (engulfing, pin bar, etc.) |

**Note:** CE is shared with Phase 4 (Flow). This is an **explicit overlap** — CE appears in both Flow Score and Price Action Score.

**Mitigation:** In the Probability Engine (Phase 10), CE is assigned to the **Flow Evidence Family** and counted once.

---

## E — NORMALIZATION

### E.1 — Component Normalization

All input scores are already normalized to [-100, +100] by their respective engines. GSI uses them directly.

### E.2 — GSI Clamping

$$\text{GSI} = \max(-100, \min(100, \text{GSI}_{\text{raw}}))$$

This ensures GSI stays within bounds even with extreme component values.

### E.3 — GSI Smoothing

To reduce noise:

$$\text{GSI}_{\text{smooth},t} = \alpha \cdot \text{GSI}_{\text{raw},t} + (1 - \alpha) \cdot \text{GSI}_{\text{smooth},t-1}$$

Where $\alpha = \frac{2}{n+1}$, $n = 3$ (smoothing period).

### E.4 — Zero-Centering

GSI is zero-centered by construction:
- All component scores are zero-centered (Phase 2–5)
- Weights sum to 1.0
- GSI = 0 means **no net directional evidence**

---

## F — DOUBLE COUNTING ANALYSIS

### F.1 — Overlap Matrix

| | Structure | Trend | Momentum | Volatility | Flow | PA |
|---|----------|-------|----------|-----------|------|-----|
| **Structure** | — | Partial | Low | Low | Low | Low |
| **Trend** | Partial | — | Moderate | Low | Low | Low |
| **Momentum** | Low | Moderate | — | Low | Low | Low |
| **Volatility** | Low | Low | Low | — | Low | Low |
| **Flow** | Low | Low | Low | Low | — | Moderate |
| **PA** | Low | Low | Low | Low | Moderate | — |

### F.2 — Identified Overlaps

#### Overlap 1: Structure vs. Trend (Partial)

| Aspect | Structure | Trend |
|--------|-----------|-------|
| Measures | Swing pattern direction | EMA crossover direction |
| Time Horizon | Discrete (swing points) | Continuous (EMA) |
| Mechanism | Fractal logic | Moving average |
| Change Rate | Slow (swing-based) | Moderate (EMA-based) |

**Status:** Partial overlap — both measure "direction" but through different lenses.
**Mitigation:** Different mechanisms; they can diverge; combined weight = 40% (25% + 15%).

#### Overlap 2: Trend vs. Momentum (Moderate)

| Aspect | Trend | Momentum |
|--------|-------|----------|
| Measures | Direction | Rate of change |
| Time Horizon | Medium-term (20/50 EMA) | Short-term (10–14 bars) |
| Mechanism | MA crossover | RSI/MACD/ROC |

**Status:** Moderate overlap — both measure "how fast price is moving."
**Mitigation:** Trend = **where** (direction); Momentum = **how fast** (rate). Combined weight = 30% (15% + 15%).

#### Overlap 3: Flow vs. Price Action (Moderate)

| Aspect | Flow | Price Action |
|--------|------|-------------|
| Measures | Volume-weighted direction | Bar-level quality |
| Key Shared Metric | Candle Efficiency (CE) | Candle Efficiency (CE) |

**Status:** Moderate overlap — CE appears in both.
**Mitigation:** CE is assigned to **Flow Evidence Family** in Phase 10; counted once.

#### Overlap 4: Volatility vs. Others (Low)

Volatility measures **dispersion**, not direction. It has low overlap with directional components.

**Status:** Low overlap — Volatility is a context modifier, not a directional signal.

### F.3 — Total Overlap Budget

$$\text{Overlap} = \underbrace{(w_{\text{struct}} + w_{\text{trend}})_{\text{partial}}}_{0.40} + \underbrace{(w_{\text{trend}} + w_{\text{mom}})_{\text{moderate}}}_{0.30} + \underbrace{(w_{\text{flow}} + w_{\text{PA}})_{\text{moderate}}}_{0.35}$$

**Assessment:** Overlap is present but managed through:
1. Different mathematical formulations
2. Different time horizons
3. Evidence Family grouping in Phase 10
4. Weights that account for overlap (lower individual weights where overlap exists)

---

## G — CALIBRATION METHODOLOGY

### G.1 — What Calibration Means

Calibration ensures that GSI values correspond to **empirically observed** directional tendencies:

$$\text{Calibration:} \quad \text{GSI} = +60 \implies \text{Historically, bullish moves were more frequent}$$

### G.2 — Calibration Procedure

**Step 1: Historical Computation**
- Compute GSI for all bars in the historical dataset
- Record GSI value and subsequent price direction

**Step 2: Binning**
- Bin GSI values into ranges: [-100,-80], [-80,-60], ..., [60,80], [80,100]
- For each bin, compute:
  - $n$ = number of bars in bin
  - $p_{\text{bull}}$ = proportion of bars where price went up in next $h$ bars
  - $p_{\text{bear}}$ = proportion of bars where price went down in next $h$ bars

**Step 3: Calibration Curve**
- Plot GSI vs. $p_{\text{bull}}$
- If well-calibrated: GSI = +60 should correspond to $p_{\text{bull}} \approx 60\%$
- If not well-calibrated: Adjust weights or apply post-hoc calibration function

**Step 4: Reliability Diagram**
- Plot predicted (GSI/100 + 0.5) vs. observed ($p_{\text{bull}}$)
- Perfect calibration = 45-degree line
-偏差 = distance from 45-degree line

### G.3 — Calibration Horizon

$$h = 15 \text{ bars on M5} = 75 \text{ minutes}$$

This is the **outcome horizon** for calibration — after 15 bars, was the move bullish or bearish?

**Note:** $h$ is an initial parameter. Different horizons may require different calibrations.

### G.4 — Calibration Quality Metric

$$\text{ECE} = \sum_{b=1}^{B} \frac{n_b}{N} \cdot |\text{predicted}_b - \text{observed}_b|$$

Where:
- $B$ = number of bins
- $n_b$ = bars in bin $b$
- $N$ = total bars
- $\text{predicted}_b$ = average predicted probability in bin
- $\text{observed}_b$ = actual proportion in bin

**Target:** ECE < 0.10 (well-calibrated).

### G.5 — Calibration Limitations

| Limitation | Mitigation |
|-----------|-----------|
| GSI weights are initial | Phase 17 optimization |
| Market regime changes | Walk-forward recalibration |
| Overfitting to training data | Out-of-sample validation |
| GSI is not a probability | Phase 10 applies proper probability model |

---

## H — WEIGHT TESTING METHODOLOGY

### H.1 — Objective

Determine if the initial weights are reasonable and identify which components contribute most to predictive power.

### H.2 — Method 1: Feature Importance (Random Forest)

$$\text{Importance}(S_i) = \frac{\text{Reduction in Gini impurity from } S_i}{\text{Total reduction}}$$

**Procedure:**
1. Compute all component scores for historical data
2. Define target: price direction in next $h$ bars
3. Train Random Forest classifier
4. Extract feature importance for each component
5. Compare importance ranking with weight ranking

**Expected:** Structure and Flow should be top 2; Volatility should be lowest.

### H.3 — Method 2: Regression Analysis

$$\text{Direction}_{t+h} = \beta_0 + \beta_1 S_{\text{struct}} + \beta_2 S_{\text{trend}} + \beta_3 S_{\text{mom}} + \beta_4 S_{\text{vol}} + \beta_5 S_{\text{flow}} + \beta_6 S_{\text{PA}} + \epsilon$$

**Procedure:**
1. Run OLS regression
2. Examine $\beta_i$ coefficients (standardized)
3. Compare standardized coefficients with weights
4. If $\beta_i$ is insignificant → reduce weight for component $i$

### H.4 — Method 3: Walk-Forward Weight Optimization

**Procedure:**
1. Split data into walk-forward windows
2. For each window, optimize weights to maximize:
   $$\text{Objective} = \text{Sharpe}(\text{GSI-based signals})$$
3. Record optimal weights per window
4. Use **median** weights across windows as final weights

**Constraint:** Weights must sum to 1.0 and each $w_i \geq 0.05$ (minimum 5% per component).

### H.5 — Method 4: Sensitivity Analysis

**Procedure:**
1. Vary each weight by ±5% (keeping others fixed)
2. Measure impact on GSI predictive power
3. If small change → robust; if large change → sensitive

**Target:** No single weight should dominate (max weight ≤ 35%).

### H.6 — Expected Outcomes

| Test | Expected Result | Action if Not Met |
|------|----------------|-------------------|
| Feature Importance | Structure > Flow > Trend > Mom > PA > Vol | Re-examine weight allocation |
| Regression | All β significant (p < 0.05) | Remove insignificant components |
| Walk-Forward | Weights stable across windows | Investigate regime dependency |
| Sensitivity | No weight dominates | Redistribute if one dominates |

---

## I — GSI STATE CLASSIFICATION

### I.1 — Directional State

$$\text{GSI}_{\text{dir}} = \begin{cases}
\text{Strong Bullish} & \text{if } \text{GSI} > +60 \\
\text{Bullish} & \text{if } +30 < \text{GSI} \leq +60 \\
\text{Weak Bullish} & \text{if } +10 < \text{GSI} \leq +30 \\
\text{Neutral} & \text{if } -10 \leq \text{GSI} \leq +10 \\
\text{Weak Bearish} & \text{if } -30 \leq \text{GSI} < -10 \\
\text{Bearish} & \text{if } -60 \leq \text{GSI} < -30 \\
\text{Strong Bearish} & \text{if } \text{GSI} < -60
\end{cases}$$

### I.2 — Confidence Level

$$\text{GSI}_{\text{conf}} = \frac{|\text{GSI}|}{100}$$

$$\text{GSI}_{\text{conf}} \in [0, 1]$$

| Confidence | Level | Interpretation |
|-----------|-------|---------------|
| > 0.60 | High | Strong directional evidence |
| 0.30 – 0.60 | Moderate | Decent directional evidence |
| 0.10 – 0.30 | Low | Weak directional evidence |
| < 0.10 | Negligible | Insufficient evidence |

### I.3 — GSI State

$$\text{GSI}_{\text{state}} = \text{GSI}_{\text{dir}} \times \text{GSI}_{\text{conf}}$$

This combines direction and confidence into a single state descriptor.

---

## J — EDGE CASES

### J.1 — Missing Components

| Scenario | Handling |
|----------|----------|
| One component unavailable | Redistribute weight proportionally to available components |
| Two+ components unavailable | GSI = 0 (insufficient data); flag `gsi_disabled` |
| All components available | Normal computation |

**Redistribution Formula:**

$$w_i^{\text{adj}} = \frac{w_i}{\sum_{j \in \text{available}} w_j}$$

### J.2 — Conflicting Signals

| Scenario | Handling |
|----------|----------|
| All components aligned | Highest confidence GSI |
| 50/50 split | GSI near 0; Neutral state |
| One component strongly opposes others | Flag as `conflicting_evidence`; reduce confidence |

### J.3 — Extreme GSI Values

| Scenario | Handling |
|----------|----------|
| GSI > +90 | Flag as `extreme_bullish`; may indicate overextension |
| GSI < -90 | Flag as `extreme_bearish`; may indicate overextension |
| GSI = ±100 | Cap at ±100; log as `max_gsi_reached` |

---

## K — BIAS PREVENTION

### K.1 — Look-Ahead Bias

**Prevention:**
1. All component scores are computed from confirmed bars only
2. GSI at bar $t$ uses only components available at bar $t$
3. Calibration uses only historical data (walk-forward)

### K.2 — Overfitting

**Prevention:**
1. Weights are initial; optimization in Phase 17 with walk-forward
2. Calibration is validated on out-of-sample data
3. No single weight exceeds 35% (diversification)

### K.3 — Double Counting

**Prevention:**
1. Overlap matrix documented (Section F)
2. Evidence Family grouping in Phase 10
3. Weights account for overlap (lower where overlap exists)

---

## L — BACKTESTABILITY

### L.1 — Backtest Requirements

| Requirement | Implementation |
|-------------|---------------|
| Component availability | Each component must be confirmed before use |
| Weight stability | Weights fixed during a walk-forward window |
| Calibration per window | Recalibrate weights per walk-forward period |
| No future data | GSI at $t$ uses only data through $t$ |

### L.2 — Backtest Data Flow

```
Phase 2 Output → Structure Score [-100, +100]
Phase 5 Output → Trend Score [-100, +100]
Phase 5 Output → Momentum Score [-100, +100]
Phase 5 Output → Volatility Score [-100, +100]
Phase 4 Output → Flow Score [-100, +100]
Derived        → Price Action Score [-100, +100]
    ↓
GSI Weighted Sum
    ↓
GSI Smoothing (EMA, n=3)
    ↓
GSI Clamping [-100, +100]
    ↓
GSI State Classification
    ↓
Final GSI Output
```

---

## M — WHAT IS FIXED

### M.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| GSI Range | [-100, +100] | Symmetric, bounded |
| Component Count | 6 | Comprehensive coverage |
| Initial Weights | [0.25, 0.15, 0.15, 0.10, 0.20, 0.15] | Structure + Flow primary |
| Smoothing Period | 3 bars | Reduces noise without lag |
| Calibration Horizon | 15 bars (M5) | ~75 minutes |
| Calibration Metric | ECE < 0.10 | Well-calibrated target |
| Min Component Weight | 5% | Ensures diversification |
| Max Component Weight | 35% | Prevents dominance |

### M.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal weights | Phase 17 (Optimization) |
| Calibration function | Phase 17 (with walk-forward) |
| Smoothing period | Phase 17 |
| Calibration horizon | Phase 17 |
| Price Action sub-weights | Phase 17 |
| GSI → Probability mapping | Phase 10 |

---

## N — WHAT REQUIRES TESTING

### N.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | Initial weights produce well-calibrated GSI | Reliability diagram | ECE < 0.15 |
| H2 | Structure has highest feature importance | Random Forest | Importance > 0.20 |
| H3 | Flow has second-highest importance | Random Forest | Importance > 0.15 |
| H4 | Volatility has lowest importance | Random Forest | Importance < 0.10 |
| H5 | GSI is independent of News/Macro | Correlation check | ρ < 0.3 |
| H6 | GSI smoothing reduces noise | Compare raw vs. smoothed | Smoothing improves Sharpe |
| H7 | Walk-forward weights are stable | Std dev of weights across windows | Std < 0.10 |

### N.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Should Volatility affect GSI direction at all? | Test removing Volatility from GSI |
| Q2 | Is 6 components optimal? | Test adding/removing components |
| Q3 | Should GSI use equal weights as baseline? | Test equal-weight vs. initial weights |
| Q4 | How often should calibration be refreshed? | Test recalibration frequency |

---

## O — OUTPUT SCHEMA

### O.1 — GSI Output per Bar

```python
@dataclass(frozen=True)
class GSIOutput:
    """Gold Smart Index output for a single bar."""
    timestamp: datetime
    
    # Component Scores
    structure_score: float              # [-100, +100]
    trend_score: float                  # [-100, +100]
    momentum_score: float               # [-100, +100]
    volatility_score: float             # [-100, +100]
    flow_score: float                   # [-100, +100]
    price_action_score: float           # [-100, +100]
    
    # Weights Used
    weights: dict[str, float]           # Current weight per component
    
    # Raw and Smoothed
    gsi_raw: float                      # Before smoothing
    gsi_smooth: float                   # After smoothing, clamped [-100, +100]
    
    # State
    gsi_direction: str                  # "strong_bullish", "bullish", ..., "strong_bearish"
    gsi_confidence: float               # [0, 1]
    gsi_state: str                      # Combined direction + confidence
    
    # Diagnostics
    components_available: int           # Number of components used
    components_missing: list[str]       # Missing component names
    overlap_flags: dict[str, bool]      # Documented overlaps
    
    # Calibration
    calibrated: bool                    # Whether calibration is active
    ece_score: float | None             # Current ECE if calibrated
    
    # Provenance
    provenance: DataProvenance
```

---

## P — DECISION OUTPUT

### P.1 — Per-Bar Decision

```
=== GSI v1.0 ===
Raw: +62.3
Smoothed: +58.7
Direction: Bullish
Confidence: 0.59 (Moderate)

=== Component Breakdown ===
Structure:  +78  (w=0.25) → +19.5
Flow:       +65  (w=0.20) → +13.0
Trend:      +45  (w=0.15) → +6.75
Momentum:   +52  (w=0.15) → +7.8
Price Act:  +40  (w=0.15) → +6.0
Volatility: -15  (w=0.10) → -1.5
─────────────────────────────
Total:              → +51.55 → clamped to +58.7 (after smoothing)

=== Overlap Notes ===
Structure ↔ Trend: Partial (direction overlap)
Trend ↔ Momentum: Moderate (rate overlap)
Flow ↔ PA: Moderate (CE shared)
```

---

## Q — APPROVAL GATE

### The Phase 6 — GSI v1.0 specification is now complete.

**Summary of what is defined:**

1. ✅ GSI formula with 6 components and initial weights
2. ✅ Detailed weight justification for each component
3. ✅ GSI ≠ Probability distinction (critical)
4. ✅ Complete overlap matrix and double counting mitigation
5. ✅ Normalization methodology (clamping, smoothing)
6. ✅ Calibration methodology (binning, ECE, walk-forward)
7. ✅ Weight testing methodology (4 methods)
8. ✅ GSI state classification (direction + confidence)
9. ✅ Edge cases and handling
10. ✅ Bias prevention measures
11. ✅ Backtest requirements
12. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **GSI ≠ Probability:** Is the distinction clear and acceptable?

2. **Initial Weights:** Structure 25%, Flow 20%, Trend 15%, Momentum 15%, PA 15%, Volatility 10% — acceptable as starting point?

3. **Weight Justification:** Are the justifications for each weight convincing?

4. **Overlap Management:** Is the documented overlap analysis sufficient?

5. **Calibration Methodology:** Is the binning + ECE approach acceptable?

6. **Weight Testing:** Are the 4 testing methods (Feature Importance, Regression, Walk-Forward, Sensitivity) comprehensive enough?

7. **Smoothing Period (3 bars):** Appropriate for GSI?

8. **Component Redistribution:** When a component is missing, redistribute weight proportionally — acceptable?

---

**Please review and approve (or request modifications) before I proceed to Phase 7 — News / Macro Engine.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
