# PHASE 14 — NO-TRADE ENGINE

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the **No-Trade** framework — conditions under which the system **actively decides** NOT to trade, rather than simply failing to generate a signal.

**Critical Rule:** NO TRADE is a **deliberate decision**, not a failure. The system must log:
- **Why** it decided not to trade
- **What** condition triggered the no-trade
- **When** the condition is expected to resolve

This engine produces:
1. No-Trade condition evaluation
2. Severity classification (Warning → Block)
3. Resolution tracking (when can trading resume?)
4. No-Trade logging and reporting

---

## B — INPUTS

### B.1 — Required Data

| Data | Source | Phase |
|------|--------|-------|
| Current Spread | MT5 | Phase 1 |
| Volatility Score | Phase 5 | 5 |
| ATR Ratio | Phase 5 | 5 |
| News Events | Phase 7 | 7 |
| Risk:Reward | Phase 11 | 11 |
| Liquidity Levels | Phase 3 | 3 |
| Evidence Families | Phase 10 | 10 |
| Daily P&L | Phase 12 | 12 |
| Execution Quality | MT5 | Phase 1 |
| Regime | Phase 9 | 9 |

### B.2 — Parameters

| Parameter | Initial Value | Description |
|-----------|--------------|-------------|
| `SPREAD_ALERT_PIPS` | 1.5 | Spread warning threshold |
| `SPREAD_HALT_PIPS` | 3.0 | Spread halt threshold |
| `VOL_ALERT_THRESHOLD` | 1.5 | ATR ratio warning |
| `VOL_HALT_THRESHOLD` | 2.5 | ATR ratio halt |
| `NEWS_BLOCK_MIN` | 60 | Minutes before high-impact event |
| `MIN_RR_RATIO` | 1.5 | Minimum risk:reward |
| `MIN_LIQUIDITY_SCORE` | 30 | Minimum liquidity score |
| `MAX_CONFLICTING_FAMILIES` | 3 | Max families with opposing evidence |
| `EXECUTION_LATENCY_THRESHOLD` | 2.0 | Max execution latency (seconds) |
| `UNCERTAIN_REGIME_THRESHOLD` | 0.50 | Regime confidence below which = uncertain |

---

## C — NO-TRADE CONDITIONS

### C.1 — Condition Summary

| # | Condition | Severity | Block Type |
|---|-----------|----------|-----------|
| 1 | Extreme Spread | Warning → Block | Hard Block |
| 2 | Extreme Volatility | Warning → Block | Hard Block |
| 3 | News Imminent | Warning → Block | Hard Block |
| 4 | Poor Risk:Reward | Block | Hard Block |
| 5 | Insufficient Liquidity | Warning → Block | Soft Block |
| 6 | Conflicting Evidence | Warning | Soft Block |
| 7 | Daily Risk Limit | Warning → Block | Hard Block |
| 8 | Execution Risk | Warning → Block | Hard Block |
| 9 | Uncertain Regime | Warning | Soft Block |

### C.2 — Block Types

| Type | Description | Effect |
|------|-------------|--------|
| **Hard Block** | Trading is strictly prohibited | No new entries |
| **Soft Block** | Trading is discouraged but allowed with caution | Reduced position size, tighter filters |

---

## D — CONDITION DETAILS

### D.1 — Extreme Spread

$$\text{Spread}_{\text{alert}} \iff S_t > \text{SPREAD\_ALERT\_PIPS} = 1.5$$

$$\text{Spread}_{\text{halt}} \iff S_t > \text{SPREAD\_HALT\_PIPS} = 3.0$$

| State | Spread | Action |
|-------|--------|--------|
| Normal | ≤ 1.5 pips | Trade normally |
| Warning | 1.5 – 3.0 pips | Alert; reduce position size by 50% |
| Block | > 3.0 pips | **No new entries** |

**Resolution:** Spread returns to ≤ 1.5 pips for 3 consecutive bars.

### D.2 — Extreme Volatility

$$\text{Vol}_{\text{alert}} \iff \text{ATR\_Ratio}_t > \text{VOL\_ALERT\_THRESHOLD} = 1.5$$

$$\text{Vol}_{\text{halt}} \iff \text{ATR\_Ratio}_t > \text{VOL\_HALT\_THRESHOLD} = 2.5$$

| State | ATR Ratio | Action |
|-------|-----------|--------|
| Normal | ≤ 1.5 | Trade normally |
| Warning | 1.5 – 2.5 | Alert; reduce position size by 50% |
| Block | > 2.5 | **No new entries** |

**Resolution:** ATR Ratio returns to ≤ 1.5 for 5 consecutive bars.

### D.3 — News Imminent

$$\text{News}_{\text{block}} \iff \exists \, \text{event } i: 0 < \text{release\_ts}_i - \text{now} < \text{NEWS\_BLOCK\_MIN} \text{ minutes}$$

$$\wedge \quad \text{event}.importance \geq \text{HIGH}$$

| State | Time to Event | Action |
|-------|--------------|--------|
| Normal | > 60 min or no event | Trade normally |
| Warning | 60–30 min before | Alert; prepare to halt |
| Block | < 30 min before | **No new entries** |
| Extended Block | During event + 30 min post | **No new entries** |

**Resolution:** Event passes + 30-minute cooldown.

### D.4 — Poor Risk:Reward

$$\text{RR}_{\text{block}} \iff \text{RR}_{\text{setup}} < \text{MIN\_RR\_RATIO} = 1.5$$

| State | RR | Action |
|-------|-----|--------|
| Acceptable | ≥ 1.5 | Trade normally |
| Block | < 1.5 | **No trade** — setup rejected |

**Resolution:** RR recalculated with updated TP/SL. If still < 1.5, setup remains blocked.

### D.5 — Insufficient Liquidity

$$\text{Liquidity}_{\text{alert}} \iff \text{LiquidityScore}_t < \text{MIN\_LIQUIDITY\_SCORE} = 30$$

$$\text{Liquidity}_{\text{halt}} \iff \text{LiquidityScore}_t < 15$$

| State | Liquidity Score | Action |
|-------|----------------|--------|
| Normal | ≥ 30 | Trade normally |
| Warning | 15 – 30 | Alert; reduce position size by 50% |
| Block | < 15 | **No new entries** |

**Resolution:** Liquidity Score returns to ≥ 30 for 5 consecutive bars.

### D.6 — Conflicting Evidence

$$\text{Conflict}_{\text{warning}} \iff \text{Families}_{\text{conflicting}} \geq \text{MAX\_CONFLICTING\_FAMILIES} = 3$$

Where $\text{Families}_{\text{conflicting}}$ = count of families with score sign opposite to dominant direction.

| State | Conflicting Families | Action |
|-------|---------------------|--------|
| Aligned | 0–1 | Trade normally |
| Mild Conflict | 2 | Alert; reduce confidence |
| Significant Conflict | ≥ 3 | **Reduce position size by 50%** |
| Severe Conflict | ≥ 5 | **No new entries** |

**Resolution:** Evidence alignment improves (conflicting families < 3).

### D.7 — Daily Risk Limit

$$\text{DailyLoss}_{\text{warning}} \iff \frac{|\text{DailyP\&L}|}{\text{Equity}_{\text{start}}} > \text{daily\_loss\_lvl1} = 0.02$$

$$\text{DailyLoss}_{\text{block}} \iff \frac{|\text{DailyP\&L}|}{\text{Equity}_{\text{start}}} > \text{MAX\_DAILY\_LOSS} = 0.05$$

From Phase 12 cascading alerts:

| Level | Threshold | Action |
|-------|-----------|--------|
| Level 1 (Yellow) | 2% | Alert; reduce size by 50% |
| Level 2 (Orange) | 3% | Alert; reduce size by 75% |
| Level 3 (Red) | 4% | **No new entries** |
| Level 4 (Kill) | 5% | **Halt all trading** |
| Hard Stop | 6% | **Force close all** |

**Resolution:** Next trading day (daily reset).

### D.8 — Execution Risk

$$\text{Execution}_{\text{alert}} \iff \text{Latency}_t > \text{EXECUTION\_LATENCY\_THRESHOLD} = 2.0 \text{ seconds}$$

$$\text{Execution}_{\text{halt}} \iff \text{ConnectionLost} = \text{True}$$

| State | Condition | Action |
|-------|-----------|--------|
| Normal | Latency < 2.0s, connected | Trade normally |
| Warning | Latency 2.0–5.0s | Alert; reduce position size |
| Block | Latency > 5.0s or disconnected | **No new entries** |

**Resolution:** Latency returns to < 2.0s for 3 consecutive checks, or connection restored.

### D.9 — Uncertain Regime

$$\text{Regime}_{\text{uncertain}} \iff \text{RegimeConfidence}_t < \text{UNCERTAIN\_REGIME\_THRESHOLD} = 0.50$$

| State | Regime Confidence | Action |
|-------|------------------|--------|
| Clear | ≥ 0.70 | Trade normally |
| Uncertain | 0.50 – 0.70 | Alert; increase signal threshold by 25% |
| Unknown | < 0.50 | **Reduce position size by 50%** |

**Resolution:** Regime confidence returns to ≥ 0.70 for 5 consecutive bars.

---

## E — SEVERITY CLASSIFICATION

### E.1 — Severity Levels

| Level | Code | Description | Effect |
|-------|------|-------------|--------|
| 0 | GREEN | All conditions normal | Trade normally |
| 1 | YELLOW | Warning condition active | Alert; reduce caution |
| 2 | ORANGE | Significant risk | Reduce position size |
| 3 | RED | High risk | No new entries |
| 4 | CRITICAL | Extreme risk | Halt all trading |

### E.2 — Overall Severity

$$\text{OverallSeverity} = \max(\text{Severity}_{\text{spread}}, \text{Severity}_{\text{vol}}, \text{Severity}_{\text{news}}, ..., \text{Severity}_{\text{regime}})$$

The **worst** condition determines the overall severity.

### E.3 — Severity → Action Matrix

| Severity | Position Size | New Entries | Existing Positions |
|----------|-------------|-------------|-------------------|
| GREEN (0) | 100% | Allowed | Manage normally |
| YELLOW (1) | 75% | Allowed | Manage normally |
| ORANGE (2) | 50% | Allowed with caution | Tighten SL |
| RED (3) | 0% | **Blocked** | Manage (trail/BE) |
| CRITICAL (4) | 0% | **Blocked** | **Close all** |

---

## F — NO-TRADE DECISION

### F.1 — Decision Process

```
For each potential setup:
    1. Evaluate all 9 No-Trade conditions
    2. Assign severity per condition
    3. Determine overall severity
    4. Apply action matrix
    5. Log decision with reasons
```

### F.2 — Decision Output

$$\text{Decision} = \begin{cases}
\text{TRADE} & \text{if OverallSeverity} \leq 1 \wedge \text{Setup valid} \\
\text{TRADE\_REDUCED} & \text{if OverallSeverity} = 2 \\
\text{NO\_TRADE} & \text{if OverallSeverity} \geq 3 \\
\text{HALT} & \text{if OverallSeverity} = 4
\end{cases}$$

### F.3 — No-Trade is a Real Decision

The system must output:

```
Decision: NO TRADE
Reason: Extreme Spread (3.5 pips > 3.0 threshold)
Severity: RED (3)
Expected Resolution: When spread returns to ≤ 1.5 pips for 3 bars
Time Since Onset: 12 minutes
Conditions Active: [Spread: RED, Volatility: GREEN, News: GREEN, ...]
```

**Not:**

```
Decision: HOLD (no signal generated)
```

**The difference:** NO TRADE is an **active decision** with a reason. HOLD is ambiguous.

---

## G — CONDITION TRACKING

### G.1 — Active Conditions

The system maintains a list of active No-Trade conditions:

$$\text{ActiveConditions}_t = \{c \in \mathcal{C} : c.\text{severity} \geq \text{YELLOW}\}$$

### G.2 — Condition Duration

For each active condition:

$$\text{Duration}_c = \text{now} - c.\text{onset\_time}$$

### G.3 — Resolution Prediction

For each active condition, estimate when it will resolve:

| Condition | Estimated Resolution |
|-----------|---------------------|
| Spread | When spread normalizes (unknown) |
| Volatility | When ATR ratio drops (unknown) |
| News | At event time + cooldown (known) |
| RR | When setup updated (unknown) |
| Liquidity | When liquidity returns (unknown) |
| Conflict | When evidence aligns (unknown) |
| Daily Limit | Next trading day (known) |
| Execution | When connection恢复 (unknown) |
| Regime | When regime stabilizes (unknown) |

### G.4 — Condition Log

Every No-Trade decision is logged with:

| Field | Description |
|-------|-------------|
| Timestamp | When decision was made |
| Conditions | List of active conditions |
| Severity per condition | Severity level |
| Overall severity | Worst severity |
| Decision | TRADE / TRADE_REDUCED / NO_TRADE / HALT |
| Setup details | What setup was evaluated |
| Resolution estimate | When conditions expected to resolve |

---

## H — EDGE CASES

### H.1 — Multiple Conditions

| Scenario | Handling |
|----------|----------|
| Multiple conditions active | Use worst severity |
| Conditions conflict (one says trade, other says don't) | Don't wins (conservative) |
| Conditions resolve at different times | Wait for all to resolve |

### H.2 — Rapid Condition Changes

| Scenario | Handling |
|----------|----------|
| Condition flickers (on/off/on) | Apply stability filter (3-bar confirmation) |
| Condition resolves then immediately returns | Log as `unstable_condition` |

### H.3 — Session Transitions

| Scenario | Handling |
|----------|----------|
| No-Trade during session close | Evaluate at next session open |
| Condition active across sessions | Carry forward; re-evaluate |

---

## I — BIAS PREVENTION

### I.1 — Look-Ahead Bias

**Prevention:**
1. All conditions evaluated using current bar data only
2. News blocking uses release_timestamp strictly
3. No future knowledge of spread/volatility

### I.2 — Overfitting

**Prevention:**
1. No-Trade parameters are conservative
2. Walk-forward validation
3. Conditions are based on market fundamentals, not backtest optimization

---

## J — BACKTESTABILITY

### J.1 — Backtest Requirements

| Requirement | Implementation |
|-------------|---------------|
| Spread data | Use historical spread if available |
| News blocking | Use release_timestamp strictly |
| Daily limits | Track per-day P&L |
| Execution risk | Simulate latency if data available |

### J.2 — Backtest Impact

No-Trade conditions **reduce** the number of trades in backtest. This is realistic — the system should not trade in adverse conditions.

---

## K — WHAT IS FIXED

### K.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Spread Alert | 1.5 pips | Above normal |
| Spread Halt | 3.0 pips | Abnormally wide |
| Vol Alert | 1.5 ATR ratio | Above normal |
| Vol Halt | 2.5 ATR ratio | Extreme |
| News Block | 60 min pre / 30 min post | Safety buffer |
| Min RR | 1.5 | Positive expectancy |
| Min Liquidity | 30 | Meaningful liquidity |
| Max Conflicts | 3 families | Significant disagreement |
| Execution Latency | 2.0s | Normal execution |
| Regime Confidence | 0.50 | Minimum certainty |

### K.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal spread thresholds | Phase 17 (Optimization) |
| Optimal volatility thresholds | Phase 17 |
| News blocking windows | Phase 17 |
| Conflict threshold | Phase 17 |
| Stability filter period | Phase 17 |

---

## L — WHAT REQUIRES TESTING

### L.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | No-Trade conditions reduce drawdown | Backtest with/without | Drawdown reduced by > 20% |
| H2 | Spread blocking prevents slippage losses | Analyze blocked periods | Avoided high-spread periods |
| H3 | News blocking prevents adverse moves | Analyze post-news moves | Avoided volatile periods |
| H4 | Conflict blocking reduces false signals | Compare win rates | Higher win rate when not blocked |
| H5 | No-Trade is a real decision (not noise) | Analyze blocked vs. traded performance | Blocked periods have worse expected outcomes |

### L.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Should No-Trade be more aggressive? | Test tighter thresholds |
| Q2 | How to handle conditions that rarely resolve? | Test maximum duration |
| Q3 | Should No-Trade affect existing positions? | Test position management during blocks |
| Q4 | Can we predict when conditions will resolve? | Feature importance analysis |

---

## M — OUTPUT SCHEMA

### M.1 — No-Trade Output per Bar

```python
@dataclass(frozen=True)
class NoTradeOutput:
    """No-Trade Engine output for a single bar."""
    timestamp: datetime
    
    # Conditions
    conditions: dict[str, NoTradeCondition]  # Per-condition status
    active_conditions: list[str]        # Names of active conditions
    
    # Severity
    severity_per_condition: dict[str, int]  # Severity per condition
    overall_severity: int               # 0–4
    
    # Decision
    decision: str                       # "trade", "trade_reduced", "no_trade", "halt"
    decision_reasons: list[str]         # Why this decision
    
    # Position Adjustment
    position_size_factor: float         # [0, 1] — multiplier for position size
    signal_threshold_adjustment: float  # Additional threshold
    
    # Resolution
    estimated_resolution: dict[str, str | None]  # Per condition
    conditions_duration: dict[str, int]  # Bars since onset
    
    # Provenance
    provenance: DataProvenance
```

### M.2 — No-Trade Condition Schema

```python
@dataclass(frozen=True)
class NoTradeCondition:
    """A single No-Trade condition."""
    name: str                           # "spread", "volatility", etc.
    is_active: bool
    severity: int                       # 0–4
    value: float                        # Current value
    threshold: float                    # Threshold that triggered
    onset_bar: datetime                 # When condition became active
    duration_bars: int                  # How long active
    resolution_estimate: str | None     # Expected resolution
```

---

## N — DECISION OUTPUT

### N.1 — No-Trade Decision

```
=== NO-TRADE ENGINE ===
Overall Severity: RED (3)
Decision: NO TRADE

=== ACTIVE CONDITIONS ===
Spread:        RED (3.5 pips > 3.0) — Active 12 min
Volatility:    GREEN (ATR Ratio = 0.95)
News:          GREEN (No upcoming events)
RR:            GREEN (RR = 1.8)
Liquidity:     GREEN (Score = 65)
Conflict:      GREEN (1/8 families conflicting)
Daily Limit:   GREEN (1.2% / 5.0%)
Execution:     GREEN (Latency = 0.3s)
Regime:        GREEN (Confidence = 0.85)

=== DECISION DETAILS ===
Setup Evaluated: LONG @ 1848.50
Reason: Spread exceeds halt threshold (3.5 > 3.0)
Expected Resolution: When spread returns to ≤ 1.5 pips for 3 bars
Time Since Onset: 12 minutes

=== POSITION ADJUSTMENT ===
Position Size Factor: 0% (blocked)
Signal Threshold: +0% (not applicable)

=== LOG ===
Decision logged as NO_TRADE with reason "extreme_spread"
```

### N.2 — Warning State

```
=== NO-TRADE ENGINE ===
Overall Severity: ORANGE (2)
Decision: TRADE_REDUCED

=== ACTIVE CONDITIONS ===
Spread:        ORANGE (1.8 pips > 1.5) — Active 5 min
Volatility:    GREEN (ATR Ratio = 1.1)
News:          GREEN (No upcoming events)
Conflict:      YELLOW (2/8 families conflicting)
...

=== DECISION DETAILS ===
Position Size Factor: 50% (reduced due to spread)
Signal Threshold: +25% (increased due to conflict)
```

---

## O — APPROVAL GATE

### The Phase 14 — No-Trade Engine specification is now complete.

**Summary of what is defined:**

1. ✅ 9 No-Trade conditions with mathematical thresholds
2. ✅ Severity classification (GREEN → CRITICAL)
3. ✅ Block types (Hard Block vs. Soft Block)
4. ✅ Position size adjustment per severity
5. ✅ Signal threshold adjustment
6. ✅ Resolution tracking and estimation
7. ✅ No-Trade as real decision (not failure)
8. ✅ Condition logging and reporting
9. ✅ Edge cases and handling
10. ✅ Bias prevention measures
11. ✅ Backtest requirements
12. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **9 Conditions:** Is this comprehensive? Missing any?

2. **Spread Thresholds (1.5 / 3.0 pips):** Appropriate for XAUUSD?

3. **Volatility Thresholds (1.5 / 2.5 ATR ratio):** Appropriate?

4. **News Blocking (60 min pre / 30 min post):** Sufficient buffer?

5. **Min RR (1.5):** Ensures positive expectancy?

6. **Max Conflicting Families (3):** Significant disagreement threshold?

7. **No-Trade as Real Decision:** Is the logging format appropriate?

8. **Severity → Action Matrix:** Position size reductions appropriate?

---

**Please review and approve (or request modifications) before I proceed to Phase 15 — Decision Engine.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
