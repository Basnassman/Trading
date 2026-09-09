# PHASE 9 — MARKET REGIME ENGINE

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the mathematical framework for **Market Regime Classification** — identifying the current market environment and its implications for trading parameters.

The Regime Engine produces:
1. Primary Regime classification (9 regimes)
2. Regime confidence score
3. Regime duration tracking
4. Regime transition detection
5. Regime-specific parameter adjustments (SL, TP, Position Size, etc.)

**Scope Boundary:**
- This engine **consumes** outputs from Phase 2–8.
- It does **not** generate trading signals — it provides **context** for signal interpretation.
- Regime affects every downstream engine (Setup, Risk, Execution).

---

## B — INPUTS

### B.1 — Required Data

| Data | Source | Phase |
|------|--------|-------|
| Structure State | Phase 2 | 2 |
| Structure Score | Phase 2 | 2 |
| Liquidity Sweep Detected | Phase 3 | 3 |
| Liquidity Score | Phase 3 | 3 |
| Flow Score | Phase 4 | 4 |
| Trend Score | Phase 5 | 5 |
| Momentum Score | Phase 5 | 5 |
| Volatility Score | Phase 5 | 5 |
| ATR Ratio | Phase 5 | 5 |
| News Score | Phase 7 | 7 |
| News Blocking Status | Phase 7 | 7 |
| Session | Phase 1 | 1 |

### B.2 — Parameters

| Parameter | Initial Value | Description |
|-----------|--------------|-------------|
| `REGIME_LOOKBACK` | 20 bars | Bars for regime determination |
| `REGIME_STABILITY_THRESHOLD` | 0.70 | Min confidence for regime assignment |
| `REGIME_TRANSITION_BARS` | 5 | Bars to confirm regime change |
| `TREND_ADX_THRESHOLD` | 25 | ADX above which = trending |
| `RANGE_ATR_THRESHOLD` | 0.8 | ATR ratio below which = range |
| `BREAKOUT_ATR_THRESHOLD` | 1.5 | ATR ratio above which = breakout |
| `LOW_LIQUIDITY_RVOL` | 0.5 | RVOL below which = low liquidity |

---

## C — REGIME DEFINITIONS

### C.1 — Primary Regimes

| Regime | ID | Description |
|--------|-----|-------------|
| Normal Trend | 1 | Clear directional trend with normal volatility |
| Range | 2 | Price oscillating within a defined range |
| Breakout | 3 | Price breaking out of a range with expansion |
| High Volatility | 4 | Elevated volatility, unclear direction |
| Liquidity Sweep | 5 | Active sweep of liquidity levels |
| News | 6 | During or immediately after high-impact news |
| Post-News | 7 | Cooldown period after news event |
| Low Liquidity | 8 | Below-average volume and activity |
| Transition | 9 | Regime is changing; uncertain state |

### C.2 — Secondary Attributes

Each regime carries:

| Attribute | Description |
|-----------|-------------|
| Confidence | How certain the classification is [0, 1] |
| Duration | How long the regime has been active (bars) |
| Stability | How stable the regime has been (low transitions = stable) |
| Priority | Regimes that override others (e.g., News overrides all) |

---

## D — REGIME CLASSIFICATION ALGORITHM

### D.1 — Decision Tree

```
START
│
├── News Active?
│   └── YES → REGIME = News
│
├── Post-News Cooldown?
│   └── YES → REGIME = Post-News
│
├── Liquidity Sweep Detected?
│   └── YES → REGIME = Liquidity Sweep
│
├── Low Liquidity (RVOL < 0.5)?
│   └── YES → REGIME = Low Liquidity
│
├── Volatility Extreme?
│   ├── ATR Ratio > 1.5 AND Range Ratio > 1.5
│   │   └── REGIME = High Volatility
│   └── ATR Ratio > 2.0
│       └── REGIME = High Volatility
│
├── Breakout Detected?
│   ├── BOS Detected (Phase 2)
│   ├── ATR Ratio > 1.5
│   ├── Range Ratio > 1.5
│   └── REGIME = Breakout
│
├── Trending?
│   ├── ADX > 25
│   ├── Structure = Bullish or Bearish
│   ├── Trend Score > 30 or < -30
│   └── REGIME = Normal Trend
│
├── Range-Bound?
│   ├── ADX < 20
│   ├── ATR Ratio < 0.8
│   ├── Structure = Neutral or Compression
│   └── REGIME = Range
│
└── DEFAULT
    └── REGIME = Transition
```

### D.2 — Mathematical Conditions

#### News Regime

$$\text{Regime} = \text{News} \iff \text{NewsBlocking} = \text{True}$$

$$\text{OR} \quad \exists \, \text{event } i: |\text{time} - \text{release\_ts}_i| < \text{BLOCK\_WINDOW}$$

**Priority:** News overrides ALL other regimes.

#### Post-News Regime

$$\text{Regime} = \text{PostNews} \iff \text{RecentNews} = \text{True}$$

$$\text{AND} \quad \text{time} - \text{last\_news\_end} < \text{POST\_NEWS\_COOLDOWN}$$

Where `POST_NEWS_COOLDOWN` = 30 minutes (initial).

#### Liquidity Sweep Regime

$$\text{Regime} = \text{LiqSweep} \iff \text{SweepDetected} = \text{True}$$

From Phase 3 output.

#### Low Liquidity Regime

$$\text{Regime} = \text{LowLiq} \iff \text{RVOL}_t < \text{LOW\_LIQUIDITY\_RVOL}$$

$$\text{AND} \quad \text{Trend} < 15 \text{ (no clear trend)}$$

#### High Volatility Regime

$$\text{Regime} = \text{HighVol} \iff \text{ATR\_Ratio}_t > \text{BREAKOUT\_ATR\_THRESHOLD}$$

$$\text{OR} \quad \left(\text{ATR\_Ratio}_t > 1.2 \text{ AND } \text{Range\_Ratio}_t > 1.5\right)$$

#### Breakout Regime

$$\text{Regime} = \text{Breakout} \iff \text{BOSDetected} = \text{True}$$

$$\text{AND} \quad \text{ATR\_Ratio}_t > 1.2$$

$$\text{AND} \quad \text{FlowScore} \times \text{BOS\_direction} > 0$$

**Interpretation:** BOS confirmed by volume expansion and flow alignment.

#### Normal Trend Regime

$$\text{Regime} = \text{Trend} \iff \text{ADX}_t > \text{TREND\_ADX\_THRESHOLD}$$

$$\text{AND} \quad |\text{TrendScore}| > 30$$

$$\text{AND} \quad \text{Structure} \in \{\text{Bullish}, \text{Bearish}\}$$

$$\text{AND} \quad \text{ATR\_Ratio}_t \in [0.8, 1.5]$$

#### Range Regime

$$\text{Regime} = \text{Range} \iff \text{ADX}_t < 20$$

$$\text{AND} \quad \text{ATR\_Ratio}_t < 0.8$$

$$\text{AND} \quad \text{Structure} \in \{\text{Neutral}, \text{Compression}\}$$

$$\text{AND} \quad |\text{TrendScore}| < 20$$

#### Transition Regime

$$\text{Regime} = \text{Transition} \iff \text{None of the above conditions met}$$

$$\text{OR} \quad \text{Multiple regime conditions partially met}$$

### D.3 — Priority Order

When multiple conditions could apply:

| Priority | Regime | Reason |
|----------|--------|--------|
| 1 (Highest) | News | External event dominates |
| 2 | Post-News | Cooldown from news |
| 3 | Liquidity Sweep | Active stop hunting |
| 4 | Low Liquidity | Insufficient participation |
| 5 | High Volatility | Risk management critical |
| 6 | Breakout | Active breakout in progress |
| 7 | Normal Trend | Established trend |
| 8 | Range | No clear direction |
| 9 (Lowest) | Transition | Default/uncertain |

---

## E — REGIME CONFIDENCE

### E.1 — Confidence Score

$$\text{Confidence} = \frac{\text{Number of conditions met}}{\text{Total conditions for regime}} \times \text{StabilityFactor}$$

Where:
- Conditions met: How many sub-conditions the current bar satisfies
- Total conditions: Total sub-conditions defined for the regime
- StabilityFactor: Based on regime duration (longer = more stable)

### E.2 — Stability Factor

$$\text{StabilityFactor} = \min\left(1, \frac{\text{Duration}_{\text{bars}}}{\text{REGIME\_STABILITY\_THRESHOLD}_{\text{bars}}}\right)$$

Where `REGIME_STABILITY_THRESHOLD` = 20 bars.

**Interpretation:**
- Duration < 5 bars: Low confidence (regime just started)
- Duration 5–20 bars: Increasing confidence
- Duration > 20 bars: Full confidence

### E.3 — Confidence Threshold

$$\text{Regime}_{\text{assigned}} \iff \text{Confidence} \geq \text{REGIME\_STABILITY\_THRESHOLD} = 0.70$$

If confidence < 0.70: Regime = Transition (insufficient certainty).

---

## F — REGIME DURATION AND TRANSITIONS

### F.1 — Duration Tracking

$$\text{Duration}_{\text{current}} = \text{CurrentBar} - \text{RegimeStartBar}$$

### F.2 — Transition Detection

$$\text{TransitionDetected} \iff \text{Regime}_{\text{current}} \neq \text{Regime}_{\text{previous}}$$

**Confirmation Rule:**

$$\text{TransitionConfirmed} \iff \text{NewRegime sustained for } \text{REGIME\_TRANSITION\_BARS} \text{ bars}$$

Where `REGIME_TRANSITION_BARS` = 5.

**Prevention:** A single bar of different regime does NOT trigger transition. The new regime must persist for 5 bars.

### F.3 — Transition Log

| Field | Description |
|-------|-------------|
| From Regime | Previous regime |
| To Regime | New regime |
| Timestamp | When transition was confirmed |
| Duration | How long previous regime lasted |
| Trigger | What caused the transition |

---

## G — REGIME INFLUENCE ON TRADING

### G.1 — Parameter Adjustments per Regime

| Regime | Signal Threshold | Entry Logic | SL | TP | Position Size | No-Trade? |
|--------|-----------------|-------------|----|----|--------------|-----------|
| **Normal Trend** | Standard | Trend-following | Standard (1.0 ATR) | Standard (2.0 ATR) | Standard (100%) | No |
| **Range** | Higher (+20%) | Mean-reversion | Tighter (0.7 ATR) | Conservative (1.5 ATR) | Reduced (70%) | Consider |
| **Breakout** | Standard | Breakout-confirmed | Wider (1.5 ATR) | Extended (3.0 ATR) | Standard (100%) | No |
| **High Volatility** | Higher (+30%) | Conservative | Wider (1.5 ATR) | Extended (2.5 ATR) | Reduced (50%) | Consider |
| **Liquidity Sweep** | Higher (+25%) | Post-sweep reversal | Standard (1.0 ATR) | Standard (2.0 ATR) | Reduced (60%) | Wait for confirmation |
| **News** | N/A | N/A | N/A | N/A | N/A | **YES — BLOCK** |
| **Post-News** | Higher (+40%) | Cautious | Wider (1.3 ATR) | Conservative (1.8 ATR) | Reduced (40%) | Often |
| **Low Liquidity** | Higher (+35%) | Conservative | Standard (1.0 ATR) | Conservative (1.5 ATR) | Reduced (50%) | Consider |
| **Transition** | Higher (+25%) | Wait | Standard (1.0 ATR) | Standard (2.0 ATR) | Reduced (60%) | Often |

### G.2 — SL/TP Adjustment Formulas

$$\text{SL}_{\text{regime}} = \text{SL}_{\text{base}} \times \text{SL}_{\text{multiplier}}(\text{Regime})$$

$$\text{TP}_{\text{regime}} = \text{TP}_{\text{base}} \times \text{TP}_{\text{multiplier}}(\text{Regime})$$

| Regime | SL Multiplier | TP Multiplier |
|--------|--------------|---------------|
| Normal Trend | 1.0 | 1.0 |
| Range | 0.7 | 0.75 |
| Breakout | 1.5 | 1.5 |
| High Volatility | 1.5 | 1.25 |
| Liquidity Sweep | 1.0 | 1.0 |
| News | N/A | N/A |
| Post-News | 1.3 | 0.9 |
| Low Liquidity | 1.0 | 0.75 |
| Transition | 1.0 | 1.0 |

### G.3 — Position Size Adjustment

$$\text{Size}_{\text{regime}} = \text{Size}_{\text{base}} \times \text{Size}_{\text{factor}}(\text{Regime})$$

| Regime | Size Factor |
|--------|------------|
| Normal Trend | 1.00 |
| Range | 0.70 |
| Breakout | 1.00 |
| High Volatility | 0.50 |
| Liquidity Sweep | 0.60 |
| News | 0.00 (blocked) |
| Post-News | 0.40 |
| Low Liquidity | 0.50 |
| Transition | 0.60 |

### G.4 — Signal Threshold Adjustment

$$\text{Threshold}_{\text{regime}} = \text{Threshold}_{\text{base}} + \text{Threshold}_{\text{adjustment}}(\text{Regime})$$

| Regime | Threshold Adjustment |
|--------|---------------------|
| Normal Trend | +0% |
| Range | +20% |
| Breakout | +0% |
| High Volatility | +30% |
| Liquidity Sweep | +25% |
| News | N/A (blocked) |
| Post-News | +40% |
| Low Liquidity | +35% |
| Transition | +25% |

**Interpretation:** Higher threshold = more selective signal required.

---

## H — REGIME TRANSITION DIAGRAM

```
                    ┌──────────────┐
                    │  Transition  │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  ┌──────────┐      ┌──────────┐      ┌──────────┐
  │  Trend   │      │  Range   │      │ High Vol │
  └────┬─────┘      └────┬─────┘      └────┬─────┘
       │                  │                  │
       ▼                  ▼                  ▼
  ┌──────────┐      ┌──────────┐      ┌──────────┐
  │ Breakout │      │   Low    │      │   Liq    │
  │          │      │  Liq     │      │  Sweep   │
  └──────────┘      └──────────┘      └──────────┘

News → Post-News → (back to any regime)
```

### H.1 — Common Transitions

| From | To | Trigger |
|------|-----|---------|
| Trend → Range | ADX drops below 20, structure compresses |
| Range → Breakout | BOS detected, ATR expands |
| Breakout → Trend | BOS confirmed, trend establishes |
| Any → News | High-impact event released |
| News → Post-News | Event ends, cooldown begins |
| Post-News → (any) | Cooldown expires, regime re-evaluated |
| Any → High Vol | ATR ratio spikes |
| High Vol → Trend/Range | Volatility normalizes |
| Any → Low Liquidity | RVOL drops below threshold |
| Low Liquidity → (any) | Volume returns |

---

## I — EDGE CASES

### I.1 — Ambiguous Regimes

| Scenario | Handling |
|----------|----------|
| Multiple conditions partially met | Use priority order; assign highest-priority regime |
| No conditions met | Assign Transition |
| Conditions flip-flopping | Apply stability factor; require 5-bar confirmation |

### I.2 — Rapid Transitions

| Scenario | Handling |
|----------|----------|
| Regime changes every bar | Log as Choppy; consider Range or Transition |
| More than 3 transitions in 20 bars | Flag `unstable_regime`; increase thresholds |

### I.3 — Session Transitions

| Scenario | Handling |
|----------|----------|
| Regime changes at session open | Normal; re-evaluate at session start |
| Low Liquidity during off-hours | Expected; do not flag as anomaly |

### I.4 — News Override

| Scenario | Handling |
|----------|----------|
| News during Trend | News overrides; Trend resumes after cooldown |
| News during Range | News overrides; Range may become Breakout |
| Multiple news events | Cooldown extends to latest event + POST window |

---

## J — BIAS PREVENTION

### J.1 — Look-Ahead Bias

**Prevention:**
1. Regime at bar $t$ uses only data from bars $\{1, ..., t\}$
2. News blocking uses release_timestamp strictly
3. 5-bar confirmation prevents premature transitions

### J.2 — Repainting

**Prevention:**
1. Once a regime is confirmed, it is frozen for that bar
2. Transitions are final after confirmation window
3. No retroactive regime changes

### J.3 — Overfitting

**Prevention:**
1. Regime parameters are initial; optimization in Phase 17
2. Walk-forward regime classification
3. Stability factor prevents over-reacting to noise

---

## K — BACKTESTABILITY

### K.1 — Backtest Requirements

| Requirement | Implementation |
|-------------|---------------|
| Regime computation | Bar-by-bar, no future data |
| News blocking | Use release_timestamp strictly |
| Transition confirmation | 5-bar delay enforced |
| Regime-dependent parameters | Applied retroactively in backtest |

### K.2 — Backtest Data Flow

```
All Engine Outputs (Phase 2–7)
    ↓
Regime Classification (per bar)
    ↓
Confidence Scoring
    ↓
Duration Tracking
    ↓
Transition Detection (5-bar confirmation)
    ↓
Parameter Adjustments
    ↓
Final Regime Output
```

---

## L — WHAT IS FIXED

### L.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Regime Count | 9 | Comprehensive coverage |
| Decision Tree Priority | News > Sweep > Vol > Breakout > Trend > Range > Transition | Safety-first |
| Transition Confirmation | 5 bars | Prevents noise-driven transitions |
| Stability Threshold | 20 bars | Regime needs time to establish |
| News Override | Always | External events dominate |
| SL/TP Multipliers | Per regime table | Adaptive risk management |
| Size Factors | Per regime table | Position sizing adjustment |

### L.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal regime thresholds | Phase 17 (Optimization) |
| SL/TP multiplier optimization | Phase 17 |
| Size factor optimization | Phase 17 |
| Transition confirmation period | Phase 17 |
| Stability threshold | Phase 17 |

---

## M — WHAT REQUIRES TESTING

### M.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | Regime classification is stable | Measure regime duration | Average > 20 bars |
| H2 | Regime transitions are informative | Compare post-transition performance | Regime change → performance change |
| H3 | News override is appropriate | Backtest with/without news blocking | News blocking improves risk-adjusted returns |
| H4 | Regime-dependent SL/TP outperforms fixed | Backtest both | Regime-dependent has better Sharpe |
| H5 | 5-bar confirmation prevents noise | Compare 1/3/5/10 bar confirmation | 5 bars balances sensitivity vs. stability |
| H6 | Regime improves GSI calibration | Compare GSI with/without regime | Regime-adjusted GSI is better calibrated |

### M.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Should regime affect GSI computation directly? | Test regime-weighted GSI |
| Q2 | How many regimes are optimal? | Test 5/7/9 regime sets |
| Q3 | Should regime confidence be continuous or discrete? | Test both approaches |
| Q4 | Can regime transitions predict reversals? | Statistical analysis |

---

## N — OUTPUT SCHEMA

### N.1 — Regime Output per Bar

```python
@dataclass(frozen=True)
class RegimeOutput:
    """Market Regime output for a single bar."""
    timestamp: datetime
    
    # Classification
    regime: str                          # "trend", "range", "breakout", etc.
    regime_id: int                       # 1–9
    confidence: float                    # [0, 1]
    
    # Duration
    duration_bars: int                   # How long current regime has lasted
    regime_start: datetime               # When current regime started
    
    # Transition
    transition_pending: bool             # Whether a transition is being confirmed
    transition_from: str | None          # Previous regime (if transitioning)
    transition_bars_confirmed: int       # Bars since potential transition
    
    # Stability
    stability: float                     # [0, 1]
    recent_transitions: int              # Transitions in last 20 bars
    
    # Parameter Adjustments
    sl_multiplier: float                 # SL adjustment factor
    tp_multiplier: float                 # TP adjustment factor
    size_factor: float                   # Position size adjustment factor
    threshold_adjustment: float          # Signal threshold adjustment
    
    # No-Trade
    is_no_trade: bool                    # Whether regime blocks trading
    no_trade_reason: str | None          # Reason for blocking
    
    # Diagnostics
    conditions_met: dict[str, bool]      # Which conditions were evaluated
    regime_score: float                  # Raw regime score before classification
    
    # Provenance
    provenance: DataProvenance
```

---

## O — DECISION OUTPUT

### O.1 — Per-Bar Decision

```
=== REGIME CLASSIFICATION ===
Regime: Normal Trend (ID=1)
Confidence: 0.85 (High)
Duration: 34 bars (2h 50min)
Stability: 0.90

=== CONDITIONS MET ===
ADX > 25: ✓ (38.2)
Structure Bullish: ✓
Trend Score > 30: ✓ (+52)
ATR Ratio in [0.8, 1.5]: ✓ (1.05)

=== PARAMETER ADJUSTMENTS ===
SL Multiplier: 1.0 (standard)
TP Multiplier: 1.0 (standard)
Size Factor: 1.0 (standard)
Threshold Adjustment: +0%
No-Trade: No

=== TRANSITION STATUS ===
No pending transitions
Recent transitions: 1 (in last 20 bars)
```

### O.2 — Regime Change Event

```
[14:30] REGIME TRANSITION CONFIRMED
  From: Range (duration: 45 bars)
  To: Normal Trend (ID=1)
  Confidence: 0.78
  Trigger: ADX crossed above 25, Structure became Bullish
  Duration of previous regime: 45 bars (3h 45min)
  
  Parameter Changes:
    SL: 0.7 ATR → 1.0 ATR
    TP: 1.5 ATR → 2.0 ATR
    Size: 70% → 100%
    Threshold: +20% → +0%
```

---

## P — APPROVAL GATE

### The Phase 9 — Market Regime Engine specification is now complete.

**Summary of what is defined:**

1. ✅ 9 regime types with mathematical conditions
2. ✅ Decision tree classification algorithm
3. ✅ Priority ordering for overlapping conditions
4. ✅ Confidence scoring with stability factor
5. ✅ Transition detection with 5-bar confirmation
6. ✅ Regime influence on all trading parameters
7. ✅ SL/TP multipliers per regime
8. ✅ Position size factors per regime
9. ✅ Signal threshold adjustments per regime
10. ✅ No-Trade conditions per regime
11. ✅ Edge cases and handling
12. ✅ Bias prevention measures
13. ✅ Backtest requirements
14. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **Regime Count (9):** Is this comprehensive enough? Too many?

2. **Priority Order:** News > Sweep > Vol > Breakout > Trend > Range > Transition — correct?

3. **Transition Confirmation (5 bars):** Appropriate for noise filtering?

4. **SL/TP Multipliers:** Are the per-regime values reasonable?

5. **Position Size Factors:** Are the reductions appropriate for each regime?

6. **News Override:** Always block during news — correct?

7. **Stability Threshold (20 bars):** How long before regime is "established"?

8. **Regime → GSI:** Should regime directly affect GSI, or just downstream parameters?

---

**Please review and approve (or request modifications) before I proceed to Phase 10 — Probability Engine.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
