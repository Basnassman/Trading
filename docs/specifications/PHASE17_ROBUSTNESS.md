# PHASE 17 — ROBUSTNESS

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the **Robustness Testing** framework — ensuring the system performs reliably under adverse conditions, parameter variations, and real-world execution frictions.

This engine produces:
1. Parameter sensitivity analysis
2. Monte Carlo simulation (enhanced)
3. Trade sequence randomization
4. Slippage/Spread/Latency impact analysis
5. Execution failure testing
6. Comprehensive robustness metrics

**Critical Rule:** Don't rely on "Highest Profit" alone. A system with high profit but poor robustness is dangerous.

---

## B — TESTING FRAMEWORK

### B.1 — Test Categories

| Category | Purpose | Tests |
|----------|---------|-------|
| Parameter Sensitivity | How robust to parameter changes? | 6 parameters tested |
| Monte Carlo | How robust to random trade order? | 1000 permutations |
| Trade Randomization | How sensitive to trade sequence? | Shuffled sequences |
| Slippage Impact | How does slippage affect performance? | Variable slippage |
| Spread Impact | How does spread affect performance? | Variable spread |
| Latency Impact | How does execution delay affect? | Variable latency |
| Execution Failure | How does failed execution affect? | Random failures |

### B.2 — Testing Principle

$$\text{Robustness} = f(\text{Parameter Stability}, \text{Execution Resilience}, \text{Statistical Significance})$$

A robust system:
- Performs consistently across parameter variations
- Survives adverse execution conditions
- Has statistically significant results

---

## C — PARAMETER SENSITIVITY

### C.1 — Parameters to Test

| Parameter | Base Value | Test Range | Step |
|-----------|-----------|-----------|------|
| Risk per Trade | 1.0% | [0.5%, 1.5%] | 0.1% |
| SL Multiplier | 1.0 ATR | [0.7, 1.3] | 0.1 |
| TP Multiplier | 2.0 ATR | [1.5, 2.5] | 0.1 |
| GSI Threshold | ±30 | [±20, ±40] | 5 |
| Min RR | 1.5 | [1.2, 1.8] | 0.1 |
| BE Trigger | 1.0 ATR | [0.75, 1.25] | 0.1 |
| Trailing Distance | 1.0 ATR | [0.75, 1.25] | 0.1 |
| Setup Expiry | 10 bars | [5, 15] | 1 |

### C.2 — Sensitivity Computation

For each parameter $p$ with base value $p_0$:

$$\text{Sensitivity}_p = \frac{\Delta \text{Sharpe}}{\Delta p / p_0}$$

Where:
- $\Delta \text{Sharpe}$ = Change in Sharpe ratio
- $\Delta p / p_0$ = Percentage change in parameter

### C.3 — Sensitivity Classification

| Sensitivity | Classification | Action |
|-------------|---------------|--------|
| < 0.5 | Low (Robust) | Parameter is stable |
| 0.5 – 1.0 | Moderate | Parameter matters; test thoroughly |
| 1.0 – 2.0 | High | Parameter is critical; optimize carefully |
| > 2.0 | Very High | Parameter is fragile; investigate |

### C.4 — Stability Surface

For each parameter, plot Performance vs. Parameter Value:

```
Sharpe
  │
2.0│        ╭──────╮
  │       ╱        ╲
1.5│──────╱──────────╲────── (Min Threshold)
  │     ╱            ╲
1.0│    ╱              ╲
  │   ╱                ╲
0.5│  ╱                  ╲
  │ ╱                    ╲
0.0│╱──────────────────────╲──
  └──────────────────────────── Parameter
    0.7  0.8  0.9  1.0  1.1  1.2  1.3
                  ↑
              Base Value
```

**Goal:** Flat surface = robust. Steep surface = fragile.

### C.5 — Acceptance Criteria

| Criterion | Threshold |
|-----------|-----------|
| Max Sensitivity | < 2.0 for any parameter |
| Average Sensitivity | < 1.0 |
| Robust Parameters | > 50% of parameters with sensitivity < 1.0 |
| No Ruin at Any Value | System survives all tested parameter values |

---

## D — MONTE CARLO SIMULATION

### D.1 — Enhanced Monte Carlo (from Phase 16)

Phase 16 defined basic Monte Carlo. Phase 17 adds:

1. **Trade Sequence Randomization**
2. **Parameter Perturbation**
3. **Market Regime Permutation**
4. **Bootstrap Resampling**

### D.2 — Trade Sequence Randomization

**Purpose:** Test if performance depends on specific trade order.

**Procedure:**

```
1. Take all N historical trades
2. Randomly shuffle trade order
3. Simulate equity curve with new order
4. Record: Max DD, Sharpe, Final Return
5. Repeat M times (M = 1000)
6. Compute distribution
```

### D.3 — Parameter Perturbation

**Purpose:** Test if performance is sensitive to parameter values.

**Procedure:**

```
1. For each parameter p:
   a. Perturb p by ±10% randomly
   b. Re-run backtest
   c. Record performance
2. Repeat N times (N = 500)
3. Compute distribution of performance
```

### D.4 — Market Regime Permutation

**Purpose:** Test if performance holds across different regime sequences.

**Procedure:**

```
1. Identify all regime periods in history
2. Randomly shuffle regime sequence
3. Re-map prices to shuffled regimes
4. Re-run backtest
5. Record performance
6. Repeat M times (M = 200)
```

### D.5 — Bootstrap Resampling

**Purpose:** Generate confidence intervals for key metrics.

**Procedure:**

```
1. Sample N trades with replacement from historical trades
2. Compute metrics (Sharpe, Win Rate, etc.)
3. Repeat B times (B = 1000)
4. Compute 95% confidence intervals
```

### D.6 — Monte Carlo Outputs

| Output | Percentiles | Acceptance |
|--------|------------|-----------|
| Max Drawdown | 5th, 25th, 50th, 75th, 95th | 95th < 25% |
| Sharpe Ratio | Same | 5th > 0.5 |
| Final Return | Same | 5th > 0% |
| Win Rate | Same | 5th > 50% |
| Profit Factor | Same | 5th > 1.0 |
| Ruin Probability | P(Max DD > 20%) | < 1% |

---

## E — SLIPPAGE TESTING

### E.1 — Slippage Scenarios

| Scenario | Slippage | Frequency |
|----------|---------|-----------|
| Ideal | 0.0 pips | 0% (baseline) |
| Low | 0.5 pips | 80% of trades |
| Medium | 1.0 pips | 60% of trades |
| High | 2.0 pips | 40% of trades |
| Extreme | 3.0 pips | 20% of trades |
| Variable | 0.5–3.0 pips | Random |

### E.2 — Slippage Impact Formula

$$\text{SlippageImpact} = \frac{\text{Performance}_{\text{slippage}} - \text{Performance}_{\text{ideal}}}{\text{Performance}_{\text{ideal}}} \times 100$$

### E.3 — Acceptance Criteria

| Metric | Max Acceptable Degradation |
|--------|--------------------------|
| Sharpe Ratio | < 30% reduction |
| Win Rate | < 5% reduction |
| Profit Factor | < 20% reduction |
| Max Drawdown | < 20% increase |

---

## F — SPREAD TESTING

### F.1 — Spread Scenarios

| Scenario | Spread | Description |
|----------|--------|-------------|
| Tight | 0.5 pips | Best case |
| Normal | 1.0 pips | Typical |
| Wide | 2.0 pips | Adverse |
| Very Wide | 3.0 pips | Crisis conditions |
| Variable | 0.5–3.0 pips | Realistic |

### F.2 — Spread Impact

Similar to slippage testing, but with spread as the variable.

### F.3 — Spread-Slippage Combined

$$\text{TotalCost} = \text{Spread} + \text{Slippage}$$

Test combinations:
- Spread 1.0 + Slippage 0.5 = 1.5 pips total
- Spread 2.0 + Slippage 1.0 = 3.0 pips total
- Spread 3.0 + Slippage 2.0 = 5.0 pips total

---

## G — LATENCY TESTING

### G.1 — Latency Scenarios

| Scenario | Latency | Description |
|----------|---------|-------------|
| Ideal | 0 ms | Instant execution |
| Low | 100 ms | Good connection |
| Medium | 500 ms | Typical retail |
| High | 1000 ms | Poor connection |
| Extreme | 2000 ms | Very poor |
| Variable | 100–2000 ms | Realistic |

### G.2 — Latency Impact

Latency affects:
- Entry price (price may move during delay)
- SL/TP execution (may slip)
- Trailing updates (may be delayed)

**Simulation:**

$$\text{ActualEntry} = \text{IntendedEntry} + \text{PriceMoveDuringLatency}$$

Where $\text{PriceMoveDuringLatency}$ is estimated from historical volatility.

### G.3 — Acceptance Criteria

| Metric | Max Acceptable Degradation at 1s Latency |
|--------|----------------------------------------|
| Sharpe Ratio | < 20% reduction |
| Win Rate | < 3% reduction |

---

## H — EXECUTION FAILURE TESTING

### H.1 — Failure Scenarios

| Scenario | Failure Rate | Description |
|----------|-------------|-------------|
| None | 0% | Perfect execution |
| Low | 2% | Occasional failures |
| Medium | 5% | Regular failures |
| High | 10% | Frequent failures |
| Extreme | 15% | Severe failures |

### H.2 — Failure Types

| Type | Description | Impact |
|------|-------------|--------|
| Rejection | Order rejected | Missed trade |
| Partial Fill | Only partial execution | Reduced position |
| Timeout | Order timed out | Unknown fill |
| Requote | Price changed, must reconfirm | Delayed entry |

### H.3 — Failure Simulation

```
For each trade:
    1. Randomly determine if failure occurs (based on failure rate)
    2. If failure:
       a. Determine type (rejection, partial, timeout, requote)
       b. Simulate impact
    3. Record outcome
```

### H.4 — Acceptance Criteria

| Failure Rate | Max Acceptable Sharpe Degradation |
|-------------|----------------------------------|
| 2% | < 10% |
| 5% | < 20% |
| 10% | < 35% |
| 15% | < 50% |

---

## I — ROBUSTNESS METRICS

### I.1 — Comprehensive Metric Set

| Metric | Formula | Target | Purpose |
|--------|---------|--------|---------|
| **Expectancy** | $\text{WinRate} \times \text{AvgWin} - (1-\text{WinRate}) \times \text{AvgLoss}$ | > $20 | Positive edge |
| **Profit Factor** | $\frac{\text{Gross Profit}}{\text{Gross Loss}}$ | > 1.5 | Profitability |
| **Sharpe Ratio** | $\frac{R_p - R_f}{\sigma_p}$ | > 1.5 | Risk-adjusted return |
| **Sortino Ratio** | $\frac{R_p - R_f}{\sigma_{\text{downside}}}$ | > 2.0 | Downside risk |
| **Max Drawdown** | $\max(\text{Drawdown}_t)$ | < 15% | Worst case |
| **Win Rate** | $\frac{\text{Wins}}{\text{Total}}$ | > 55% | Accuracy |
| **Average R** | $\frac{\text{Avg Profit}}{\text{Avg Risk}}$ | > 1.0 | Risk-reward |
| **MFE** | $\max(\text{Favorable Excursion})$ | — | Profit potential |
| **MAE** | $\max(\text{Adverse Excursion})$ | — | Risk exposure |
| **Recovery Factor** | $\frac{\text{Net Profit}}{\text{Max Drawdown}}$ | > 2.0 | Recovery ability |

### I.2 — Metric Relationships

$$\text{Expectancy} = \text{WinRate} \times \text{AvgWin} - (1-\text{WinRate}) \times \text{AvgLoss}$$

$$\text{Profit Factor} = \frac{\text{WinRate} \times \text{AvgWin}}{(1-\text{WinRate}) \times \text{AvgLoss}}$$

$$\text{Average R} = \frac{\text{AvgWin}}{\text{AvgLoss}}$$

### I.3 — Metric Dashboard

| Category | Metrics |
|----------|---------|
| Profitability | Expectancy, Profit Factor, Net Profit |
| Risk-Adjusted | Sharpe, Sortino, Calmar |
| Risk | Max Drawdown, Max DD Duration, VaR |
| Accuracy | Win Rate, Consecutive Wins/Losses |
| Efficiency | Average R, MFE, MAE, Recovery Factor |
| Robustness | Parameter Sensitivity, MC Stability |

---

## J — ROBUSTNESS REPORT

### J.1 — Report Structure

```
╔══════════════════════════════════════════════════════════════╗
║                  ROBUSTNESS REPORT v1.0                      ║
╠══════════════════════════════════════════════════════════════╣
║ OVERALL ROBUSTNESS SCORE: 78/100 (GOOD)                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║ PARAMETER SENSITIVITY                                        ║
║ Risk per Trade:    0.8 (Moderate) ✅                         ║
║ SL Multiplier:     1.2 (High) ⚠️                            ║
║ TP Multiplier:     0.6 (Low) ✅                             ║
║ GSI Threshold:     1.5 (High) ⚠️                            ║
║ Min RR:            0.9 (Moderate) ✅                         ║
║ BE Trigger:        0.7 (Moderate) ✅                         ║
║ Trailing Distance: 0.5 (Low) ✅                             ║
║ Setup Expiry:      0.3 (Low) ✅                             ║
║                                                              ║
║ Average Sensitivity: 0.82 (Moderate)                         ║
║ Max Sensitivity: 1.5 (GSI Threshold)                        ║
║ Robust Parameters: 6/8 (75%) ✅                             ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║ MONTE CARLO (1000 runs)                                      ║
║ P(Ruin): 0.3% ✅                                             ║
║ Sharpe 5th: 0.85 | Median: 1.83 | 95th: 2.65               ║
║ Max DD 5th: 5.2% | Median: 11.2% | 95th: 18.5%             ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║ EXECUTION IMPACT                                             ║
║ Slippage 1.0 pip: Sharpe -12% ✅                            ║
║ Spread 2.0 pips: Sharpe -18% ✅                             ║
║ Latency 1.0 sec: Sharpe -8% ✅                              ║
║ Failure 5%: Sharpe -15% ✅                                  ║
║ Combined (1.0+2.0+1.0s+5%): Sharpe -35% ⚠️                 ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║ ROBUSTNESS METRICS                                           ║
║ Expectancy: $32.15 ✅                                        ║
║ Profit Factor: 1.82 ✅                                       ║
║ Sharpe: 1.87 ✅                                              ║
║ Sortino: 2.34 ✅                                             ║
║ Max Drawdown: 11.2% ✅                                       ║
║ Win Rate: 58.3% ✅                                           ║
║ Average R: 1.60 ✅                                           ║
║ Recovery Factor: 2.85 ✅                                     ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║ VALIDATION                                                   ║
║ All criteria met: YES ✅                                     ║
║ Red flags: NONE                                              ║
║ Recommendation: PROCEED TO PAPER TRADING                     ║
╚══════════════════════════════════════════════════════════════╝
```

---

## K — EDGE CASES

### K.1 — Degenerate Cases

| Scenario | Handling |
|----------|----------|
| Zero trades in backtest | Report as "insufficient data" |
| All trades profitable | Flag as likely overfitting |
| All trades losing | Investigate system logic |
| Infinite Sharpe | Data error; flag |

### K.2 — Extreme Parameter Values

| Scenario | Handling |
|----------|----------|
| Risk = 0% | No trades; skip |
| Risk > 5% | Test but flag as aggressive |
| SL = 0 | Invalid; skip |
| TP = 0 | Invalid; skip |

---

## L — WHAT IS FIXED

### L.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Parameters to Test | 8 | Key system parameters |
| Parameter Range | ±30% base | Meaningful variation |
| Monte Carlo Runs | 1000 | Statistical significance |
| Bootstrap Samples | 1000 | Confidence intervals |
| Slippage Scenarios | 6 | Cover range |
| Spread Scenarios | 5 | Cover range |
| Latency Scenarios | 5 | Cover range |
| Failure Rates | 5 | Cover range |
| Max Sensitivity | < 2.0 | Robustness threshold |
| P(Ruin) | < 1% | Survival threshold |

### L.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal parameter values | From Phase 17 testing |
| Acceptable sensitivity levels | From Phase 17 results |
| Execution assumptions | From real trading experience |
| Robustness score weights | From validation |

---

## M — WHAT REQUIRES TESTING

### M.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | System is robust to ±10% parameter changes | Sensitivity analysis | < 20% Sharpe degradation |
| H2 | Monte Carlo confirms stability | P(Ruin) < 1% | Yes |
| H3 | Slippage < 1 pip has minimal impact | Slippage testing | < 15% Sharpe degradation |
| H4 | System survives 5% execution failures | Failure testing | < 25% Sharpe degradation |
| H5 | Combined adverse conditions are survivable | Combined testing | Sharpe > 0.5 |

### M.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Which parameters are most critical? | From sensitivity results |
| Q2 | What is the maximum survivable slippage? | From slippage testing |
| Q3 | Should some parameters be fixed (not optimized)? | From sensitivity results |
| Q4 | Is the system robust enough for live trading? | From overall robustness score |

---

## N — OUTPUT SCHEMA

### N.1 — Robustness Report

```python
@dataclass(frozen=True)
class RobustnessReport:
    """Complete robustness analysis report."""
    
    # Overall
    robustness_score: float              # [0, 100]
    robustness_rating: str               # "excellent", "good", "adequate", "poor"
    
    # Parameter Sensitivity
    parameter_sensitivity: dict[str, float]  # Sensitivity per parameter
    avg_sensitivity: float
    max_sensitivity: float
    max_sensitivity_param: str
    robust_params_count: int
    robust_params_pct: float
    
    # Monte Carlo
    mc_runs: int
    mc_ruin_probability: float
    mc_sharpe_percentiles: dict[str, float]  # "5th", "25th", "50th", "75th", "95th"
    mc_dd_percentiles: dict[str, float]
    
    # Execution Impact
    slippage_impact: dict[str, float]    # Slippage scenario → Sharpe change
    spread_impact: dict[str, float]
    latency_impact: dict[str, float]
    failure_impact: dict[str, float]
    combined_impact: float
    
    # Robustness Metrics
    expectancy: float
    profit_factor: float
    sharpe: float
    sortino: float
    max_drawdown: float
    win_rate: float
    avg_r: float
    recovery_factor: float
    
    # Validation
    criteria_met: dict[str, bool]
    all_criteria_met: bool
    red_flags: list[str]
    
    # Recommendation
    recommendation: str                  # "proceed", "investigate", "do_not_proceed"
```

---

## O — DECISION OUTPUT

### O.1 — Robustness Decision

```
=== ROBUSTNESS ASSESSMENT ===
Overall Score: 78/100 (GOOD)

=== CRITERIA CHECKLIST ===
Parameter Sensitivity < 2.0:    ✅ (Max: 1.5)
Monte Carlo P(Ruin) < 1%:       ✅ (0.3%)
Slippage Impact < 30%:          ✅ (12%)
Spread Impact < 30%:            ✅ (18%)
Latency Impact < 20%:           ✅ (8%)
Failure Impact < 25%:           ✅ (15%)
Combined Impact Survivable:     ✅ (Sharpe > 0.5)

=== RECOMMENDATION ===
PROCEED TO PAPER TRADING ✅

=== CAUTIONS ===
⚠️ GSI Threshold has high sensitivity (1.5)
⚠️ SL Multiplier has high sensitivity (1.2)
→ Monitor these parameters closely during paper trading
```

---

## P — APPROVAL GATE

### The Phase 17 — Robustness specification is now complete.

**Summary of what is defined:**

1. ✅ 8 parameters tested for sensitivity
2. ✅ Enhanced Monte Carlo (trade randomization, parameter perturbation, regime permutation, bootstrap)
3. ✅ Slippage testing (6 scenarios)
4. ✅ Spread testing (5 scenarios)
5. ✅ Latency testing (5 scenarios)
6. ✅ Execution failure testing (5 scenarios)
7. ✅ Combined impact testing
8. ✅ 10 robustness metrics
9. ✅ Robustness report format
10. ✅ Acceptance criteria

---

### 📋 Points Requiring Your Approval:

1. **Parameters to Test (8):** Comprehensive enough?

2. **Parameter Range (±30%):** Meaningful variation?

3. **Monte Carlo Runs (1000):** Sufficient?

4. **Slippage Scenarios (6):** Cover the range?

5. **Combined Impact Test:** Include all adverse conditions together?

6. **Robustness Metrics (10):** Comprehensive enough?

7. **Acceptance Criteria:** Thresholds appropriate?

8. **Recommendation System:** Proceed/Investigate/Do-not-proceed — sufficient?

---

**Please review and approve (or request modifications) before I proceed to Phase 18 — Paper Trading.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
