# PHASE 16 — BACKTEST ARCHITECTURE

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the **Backtest Architecture** — a rigorous historical simulation framework that prevents common biases and validates the system across multiple market conditions.

This engine produces:
1. Backtesting engine with bias prevention
2. In-Sample / Out-of-Sample / Walk-Forward validation
3. Multi-scenario testing
4. Performance metrics
5. Robustness analysis

**Critical Rule:** No Live Trading until backtest passes all validation criteria.

---

## B — BIAS PREVENTION

### B.1 — Bias Registry

| Bias | Description | Prevention Method |
|------|-------------|-------------------|
| Look-Ahead | Using future data | Temporal ordering enforcement |
| Data Leakage | Test data in training | Strict temporal splits |
| Repainting | Historical data changes | Snapshot logging, append-only |
| Survivorship | Only successful cases | Include all historical periods |
| Overfitting | Optimized for training | Walk-forward, out-of-sample |
| Selection Bias | Cherry-picking scenarios | Test ALL scenarios |
| Installation Bias | favorable start/end dates | Multiple start/end points |

### B.2 — Look-Ahead Prevention

**Rule:** At bar $t$, the system can only access data from bars $\{1, ..., t\}$.

**Implementation:**

$$\forall \, t: \quad \mathcal{F}_t = \{b_1, b_2, ..., b_t\}$$

Where $\mathcal{F}_t$ is the information set at time $t$.

**Enforcement:**
- Every engine computation is timestamped
- Data access is strictly monotonic
- No future bar data is available to any function
- Swing confirmation requires $k$ future bars (Phase 2)
- Entry at next bar open (Phase 11)

### B.3 — Data Leakage Prevention

**Rule:** Test data is never used in training or parameter estimation.

**Implementation:**
- Temporal split: Train < Validation < Test
- Parameters estimated from training set only
- Calibration from separate calibration set
- Walk-forward: retrain per window

### B.4 — Repainting Prevention

**Rule:** Once a bar is confirmed, its data is frozen.

**Implementation:**
- Bar data is logged at confirmation time
- No retroactive modification
- Indicators computed sequentially
- Scores frozen once computed

### B.5 — Survivorship Bias Prevention

**Rule:** Include ALL historical periods, including losing streaks and crises.

**Implementation:**
- Backtest covers full historical period
- No exclusion of "bad" periods
- Include: COVID-2020, Inflation-2022, Banking-2023, etc.

### B.6 — Overfitting Prevention

**Rule:** System must perform well on unseen data.

**Implementation:**
- Walk-forward validation
- Out-of-sample testing
- Parameter stability analysis
- Monte Carlo simulation

---

## C — DATA SPLITS

### C.1 — Temporal Split

```
|←──── Training ────→|←── Validation ──→|←──── Test ────→|
|                     |                   |                  |
2016                  2021                2023               2026
```

| Split | Years | Purpose |
|-------|-------|---------|
| Training | 2016–2020 (5 years) | Parameter estimation, model training |
| Validation | 2021–2022 (2 years) | Hyperparameter tuning, calibration |
| Test | 2023–2026 (3 years) | Final performance evaluation |

### C.2 — Walk-Forward Windows

```
Window 1: [2016–2018] train → [2019] test
Window 2: [2017–2019] train → [2020] test
Window 3: [2018–2020] train → [2021] test
Window 4: [2019–2021] train → [2022] test
Window 5: [2020–2022] train → [2023] test
...
```

| Parameter | Value |
|-----------|-------|
| Training window | 3 years |
| Test window | 1 year |
| Step size | 1 year |
| Minimum windows | 5 |

### C.3 — Walk-Forward Procedure

```
For each window w:
    1. Train/estimate parameters on training period
    2. Apply to test period (no modification)
    3. Record performance
    4. Move window forward
    ↓
Aggregate: Median performance across windows
```

### C.4 — Purged Walk-Forward

To prevent leakage at window boundaries:

$$\text{PurgeGap} = \text{Lookback}_{\max} + \text{OutcomeHorizon}$$

Where:
- $\text{Lookback}_{\max}$ = maximum lookback of any indicator (e.g., 50 bars for EMA)
- $\text{OutcomeHorizon}$ = 15 bars (Phase 8)

**Implementation:** Remove `PurgeGap` bars between training and test periods.

---

## D — BACKTESTING ENGINE

### D.1 — Engine Architecture

```
Historical Data
    ↓
Data Quality Check
    ↓
Feature Computation (Phase 2–9)
    ↓
Decision Engine (Phase 15)
    ↓
Trade Simulation
    ├── Entry: Next bar open
    ├── SL/TP: Set at entry
    ├── Partial Close: At TP levels
    ├── Trailing: Every bar
    ├── Emergency: Every bar
    └── Exit: At SL/TP/Trailing/Emergency
    ↓
Performance Recording
    ↓
Metrics Computation
```

### D.2 — Trade Simulation Rules

| Rule | Implementation |
|------|---------------|
| Entry Price | Next bar open (not trigger bar close) |
| Exit Price | At SL/TP level (or next available price if gap) |
| Slippage | Configurable (default: 0.5 pips) |
| Spread | Use historical spread if available |
| Commission | Configurable (default: $7 per lot round-trip) |
| Partial Close | Execute at exact TP level |
| Trailing | Check every bar |
| Emergency | Check every bar |

### D.3 — Realistic Assumptions

| Factor | Assumption | Rationale |
|--------|-----------|-----------|
| Slippage | 0.5 pips per trade | Conservative estimate |
| Spread | Variable (historical) | Realistic |
| Commission | $7 per lot round-trip | Typical broker |
| Execution Delay | 1 bar | Realistic for M5 |
| Partial Fills | Not modeled | Assume full fill |
| Gap Handling | Execute at next available price | Realistic |

### D.4 — Position Management in Backtest

The backtester simulates the full trade lifecycle:

```
Entry → BE Check → Trailing Check → Partial Close → TP₁ → TP₂ → TP₃
   ↓         ↓            ↓              ↓
   SL Check → Emergency Check → Exit
```

---

## E — TEST SCENARIOS

### E.1 — Scenario Matrix

| Scenario | Period | Purpose |
|----------|--------|---------|
| Full History | 2016–2026 | Overall performance |
| Trend (Bull) | 2020–2021 | Bull market validation |
| Trend (Bear) | 2022–2023 | Bear market validation |
| Range | 2019 Q2 | Range-bound validation |
| High Volatility | 2020 Q1 (COVID) | Crisis validation |
| High Volatility | 2022 Q2 (Inflation) | Inflation validation |
| Low Volatility | 2019 Q1 | Low vol validation |
| News-Heavy | 2022 FOMC cycle | News engine validation |
| Session: Asian | All periods | Session-specific |
| Session: London | All periods | Session-specific |
| Session: NY | All periods | Session-specific |
| Different Years | 2016, 2018, 2020, 2022, 2024 | Year-specific |

### E.2 — Scenario Definition

#### Trend (Bull)

$$\text{Trend}_{\text{bull}} \iff \text{Price rose > 15\% over period}$$

$$\wedge \quad \text{ADX average > 25$$

#### Trend (Bear)

$$\text{Trend}_{\text{bear}} \iff \text{Price fell > 15\% over period}$$

$$\wedge \quad \text{ADX average > 25$$

#### Range

$$\text{Range} \iff \text{Price stayed within 10\% band for > 3 months}$$

$$\wedge \quad \text{ADX average < 20$$

#### High Volatility

$$\text{HighVol} \iff \text{ATR ratio average > 1.5 for period}$$

#### Low Volatility

$$\text{LowVol} \iff \text{ATR ratio average < 0.8 for period}$$

#### News-Heavy

$$\text{NewsHeavy} \iff > 10 \text{ high-impact events in period}$$

### E.3 — Scenario Expectations

| Scenario | Expected Win Rate | Expected Sharpe | Expected Max DD |
|----------|------------------|-----------------|-----------------|
| Full History | > 55% | > 1.5 | < 15% |
| Trend (Bull) | > 60% | > 2.0 | < 10% |
| Trend (Bear) | > 55% | > 1.5 | < 12% |
| Range | > 50% | > 1.0 | < 10% |
| High Volatility | > 50% | > 1.0 | < 20% |
| Low Volatility | > 55% | > 1.5 | < 8% |
| News-Heavy | > 55% | > 1.5 | < 15% |

---

## F — PERFORMANCE METRICS

### F.1 — Primary Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Sharpe Ratio** | $\frac{R_p - R_f}{\sigma_p}$ | > 1.5 |
| **Sortino Ratio** | $\frac{R_p - R_f}{\sigma_{\text{downside}}}$ | > 2.0 |
| **Max Drawdown** | $\max(\text{Drawdown}_t)$ | < 15% |
| **Win Rate** | $\frac{\text{Winning Trades}}{\text{Total Trades}}$ | > 55% |
| **Profit Factor** | $\frac{\text{Gross Profit}}{\text{Gross Loss}}$ | > 1.5 |
| **Expectancy** | $\text{WinRate} \times \text{AvgWin} - (1-\text{WinRate}) \times \text{AvgLoss}$ | > 0 |

### F.2 — Secondary Metrics

| Metric | Formula | Purpose |
|--------|---------|---------|
| **Recovery Factor** | $\frac{\text{Net Profit}}{\text{Max Drawdown}}$ | Risk-adjusted return |
| **Calmar Ratio** | $\frac{\text{Annual Return}}{\text{Max Drawdown}}$ | Return per unit risk |
| **Average R** | $\frac{\text{Avg Profit}}{\text{Avg Risk}}$ | Risk-reward quality |
| **MFE** | $\text{Max Favorable Excursion}$ | How far trades went in profit |
| **MAE** | $\text{Max Adverse Excursion}$ | How far trades went in loss |
| **Trade Count** | Number of trades | Statistical significance |
| **Avg Trade Duration** | Mean holding period | Time efficiency |

### F.3 — Risk Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| **Daily VaR (95%)** | 5th percentile of daily returns | < 2% |
| **Daily CVaR (95%)** | Average of returns below VaR | < 3% |
| **Max Losing Streak** | Longest consecutive losses | < 5 |
| **Max Drawdown Duration** | Time to recover from max DD | < 3 months |

### F.4 — Robustness Metrics

| Metric | Formula | Purpose |
|--------|---------|---------|
| **Parameter Sensitivity** | Change in performance per ±10% parameter change | Stability |
| **Walk-Forward Consistency** | Std dev of Sharpe across windows | Robustness |
| **Out-of-Sample Degradation** | (In-Sample Sharpe - OOS Sharpe) / In-Sample Sharpe | Overfitting check |

---

## G — VALIDATION CRITERIA

### G.1 — Must-Pass Criteria

| Criterion | Threshold | Consequence if Failed |
|-----------|-----------|----------------------|
| Sharpe Ratio (Full History) | > 1.5 | Do not proceed to paper trading |
| Max Drawdown (Full History) | < 15% | Do not proceed |
| Win Rate (Full History) | > 55% | Investigate |
| Profit Factor (Full History) | > 1.5 | Do not proceed |
| Walk-Forward Sharpe (Median) | > 1.0 | Do not proceed |
| Walk-Forward Consistency (Std) | < 0.5 | Investigate |
| Out-of-Sample Degradation | < 30% | Investigate |
| Minimum Trade Count | > 100 per window | Investigate |

### G.2 — Nice-to-Have Criteria

| Criterion | Threshold | Benefit |
|-----------|-----------|---------|
| Sharpe Ratio (Walk-Forward) | > 2.0 | High confidence |
| Max Drawdown (Walk-Forward) | < 12% | Strong risk control |
| Win Rate (Walk-Forward) | > 60% | High accuracy |
| Profit Factor (Walk-Forward) | > 2.0 | Strong profitability |

### G.3 — Red Flags

| Red Flag | Action |
|----------|--------|
| Sharpe > 4.0 | Likely overfitting — investigate |
| Win Rate > 70% | May be too selective — check trade count |
| Max DD < 5% | May be too conservative — check returns |
| All scenarios profitable | May be overfitting — check robustness |
| Walk-Forward std > 1.0 | Unstable — investigate parameters |

---

## H — MONTE CARLO SIMULATION

### H.1 — Purpose

Monte Carlo simulation tests the robustness of the system by randomly permuting trade sequences.

### H.2 — Procedure

```
1. Take all historical trades
2. Randomly shuffle trade order
3. Compute equity curve
4. Record: Max DD, Sharpe, Final Return
5. Repeat N times (N = 1000)
6. Compute distribution of metrics
```

### H.3 — Monte Carlo Outputs

| Output | Description |
|--------|-------------|
| Max DD Distribution | 5th, 25th, 50th, 75th, 95th percentiles |
| Sharpe Distribution | Same percentiles |
| Ruin Probability | P(Max DD > 20%) |
| Confidence Intervals | 95% CI for key metrics |

### H.4 — Acceptance Criteria

| Criterion | Threshold |
|-----------|-----------|
| P(Ruin) | < 1% (P(Max DD > 20%)) |
| 5th Percentile Sharpe | > 0.5 |
| 95th Percentile Max DD | < 25% |

---

## I — SENSITIVITY ANALYSIS

### I.1 — Purpose

Test how sensitive the system is to parameter changes.

### I.2 — Parameters to Test

| Parameter | Base Value | Test Range |
|-----------|-----------|-----------|
| Risk per trade | 1% | [0.5%, 1.5%] |
| SL multiplier | 1.0 ATR | [0.7, 1.3] |
| TP multiplier | 2.0 ATR | [1.5, 2.5] |
| GSI threshold | ±30 | [±20, ±40] |
| Min RR | 1.5 | [1.2, 1.8] |
| BE trigger | 1.0 ATR | [0.75, 1.25] |

### I.3 — Sensitivity Metric

$$\text{Sensitivity}_p = \frac{\Delta \text{Performance}}{\Delta p / p_{\text{base}}}$$

Where:
- $\Delta \text{Performance}$ = Change in Sharpe
- $\Delta p / p_{\text{base}}$ = Percentage change in parameter

**Interpretation:**
- High sensitivity (> 1.0): Parameter is critical — optimize carefully
- Moderate sensitivity (0.5–1.0): Parameter matters — test thoroughly
- Low sensitivity (< 0.5): Parameter is robust — less optimization needed

### I.4 — Acceptance Criteria

| Criterion | Threshold |
|-----------|-----------|
| Max sensitivity | < 2.0 for any parameter |
| Average sensitivity | < 1.0 |
| No parameter causes ruin | Sensitivity < ∞ at any tested value |

---

## J — EDGE CASES

### J.1 — Data Quality Issues

| Scenario | Handling |
|----------|----------|
| Missing bars | Skip that bar; log gap |
| Data errors | Flag and skip |
| Weekend gaps | Handle naturally (no weekend data) |
| Holiday gaps | Handle naturally |

### J.2 — Execution Issues

| Scenario | Handling |
|----------|----------|
| Slippage exceeds assumption | Use actual slippage if available |
| Spread spike during trade | Use actual spread |
| Gap through SL/TP | Execute at next available price |

### J.3 — Statistical Issues

| Scenario | Handling |
|----------|----------|
| Few trades in scenario | Flag as insufficient sample |
| All trades in same direction | Flag as directional bias |
| Clustered trades | Check autocorrelation |

---

## K — BIAS PREVENTION

### K.1 — Implementation Checklist

| Check | Implementation | Status |
|-------|---------------|--------|
| No future data | Temporal ordering enforced | ☐ |
| No test data in training | Strict splits | ☐ |
| No repainting | Snapshot logging | ☐ |
| Include bad periods | Full history tested | ☐ |
| Walk-forward | Multiple windows | ☐ |
| Out-of-sample | Separate test set | ☐ |
| Monte Carlo | Trade permutation | ☐ |
| Sensitivity analysis | Parameter variation | ☐ |

---

## L — BACKTEST REPORT

### L.1 — Report Structure

```
=== BACKTEST REPORT ===
Period: 2016-01-01 to 2026-08-31
Timeframe: M5
Total Bars: 2,500,000+

=== TRADE STATISTICS ===
Total Trades: 1,247
Win Rate: 58.3%
Avg Win: $142.50
Avg Loss: -$89.20
Profit Factor: 1.82
Expectancy: $32.15 per trade

=== RISK METRICS ===
Max Drawdown: 11.2%
Max Drawdown Duration: 45 days
Sharpe Ratio: 1.87
Sortino Ratio: 2.34
Calmar Ratio: 2.15

=== WALK-FORWARD ===
Window 1 (2016-2018 → 2019): Sharpe = 1.65
Window 2 (2017-2019 → 2020): Sharpe = 2.12
Window 3 (2018-2020 → 2021): Sharpe = 1.78
Window 4 (2019-2021 → 2022): Sharpe = 1.45
Window 5 (2020-2022 → 2023): Sharpe = 1.92
Window 6 (2021-2023 → 2024): Sharpe = 1.83
Window 7 (2022-2024 → 2025): Sharpe = 1.71

Median Sharpe: 1.83
Std Dev: 0.22
Consistency: GOOD

=== SCENARIO BREAKDOWN ===
Trend (Bull): Sharpe = 2.15, WR = 62%, DD = 8%
Trend (Bear): Sharpe = 1.65, WR = 56%, DD = 11%
Range: Sharpe = 1.20, WR = 52%, DD = 7%
High Volatility: Sharpe = 1.35, WR = 53%, DD = 14%
Low Volatility: Sharpe = 1.75, WR = 59%, DD = 6%
News-Heavy: Sharpe = 1.55, WR = 55%, DD = 10%

=== MONTE CARLO (1000 runs) ===
P(Ruin): 0.3%
5th Percentile Sharpe: 0.85
95th Percentile Max DD: 18.5%

=== SENSITIVITY ===
Risk per trade: Sensitivity = 0.8 (Moderate)
SL multiplier: Sensitivity = 1.2 (Moderate)
TP multiplier: Sensitivity = 0.6 (Low)
GSI threshold: Sensitivity = 1.5 (High)

=== VALIDATION ===
Sharpe > 1.5: ✅ (1.87)
Max DD < 15%: ✅ (11.2%)
Win Rate > 55%: ✅ (58.3%)
PF > 1.5: ✅ (1.82)
WF Sharpe > 1.0: ✅ (1.83)
WF Consistency < 0.5: ✅ (0.22)
OOS Degradation < 30%: ✅ (18%)

OVERALL: PASS ✅
```

---

## M — WHAT IS FIXED

### M.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Training Window | 3 years | Sufficient for parameter estimation |
| Test Window | 1 year | Meaningful out-of-sample |
| Walk-Forward Step | 1 year | Regular retraining |
| Purge Gap | Lookback + Horizon | Prevent leakage |
| Slippage | 0.5 pips | Conservative |
| Commission | $7/lot | Typical |
| Monte Carlo Runs | 1000 | Statistical significance |
| Min Sharpe | 1.5 | Minimum acceptable |
| Max DD | 15% | Risk limit |
| Min Trades | 100 per window | Statistical significance |

### M.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal window sizes | Phase 17 (Optimization) |
| Slippage model | Phase 17 |
| Commission model | Phase 17 |
| Scenario definitions | Phase 17 |
| Validation thresholds | Phase 17 |

---

## N — WHAT REQUIRES TESTING

### N.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | Walk-forward outperforms in-sample | Compare metrics | WF more robust |
| H2 | Monte Carlo confirms stability | Check P(Ruin) | < 1% |
| H3 | Sensitivity analysis shows robustness | Check max sensitivity | < 2.0 |
| H4 | All scenarios pass minimum criteria | Check per-scenario | All pass |
| H5 | Out-of-sample degradation is acceptable | Check OOS degradation | < 30% |

### N.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Is 3-year training window optimal? | Test [2, 3, 4] years |
| Q2 | Should we use purged or standard walk-forward? | Test both |
| Q3 | How many Monte Carlo runs are sufficient? | Test [500, 1000, 2000] |
| Q4 | Should scenario-specific thresholds be different? | Test per-scenario |

---

## O — OUTPUT SCHEMA

### O.1 — Backtest Result

```python
@dataclass(frozen=True)
class BacktestResult:
    """Complete backtest result."""
    
    # Period
    start_date: datetime
    end_date: datetime
    total_bars: int
    
    # Trade Statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    expectancy: float
    
    # Risk Metrics
    max_drawdown: float
    max_drawdown_duration: int  # bars
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Walk-Forward
    wf_sharpe_median: float
    wf_sharpe_std: float
    wf_consistency: str
    
    # Scenario Results
    scenario_results: dict[str, ScenarioResult]
    
    # Monte Carlo
    mc_ruin_probability: float
    mc_sharpe_5th: float
    mc_sharpe_95th: float
    mc_dd_95th: float
    
    # Sensitivity
    sensitivity_results: dict[str, float]
    
    # Validation
    validation_passed: bool
    validation_details: dict[str, bool]
```

---

## P — APPROVAL GATE

### The Phase 16 — Backtest Architecture specification is now complete.

**Summary of what is defined:**

1. ✅ 7 bias prevention methods
2. ✅ Temporal split (Training/Validation/Test)
3. ✅ Walk-Forward with purging
4. ✅ 12 test scenarios
5. ✅ Primary and secondary performance metrics
6. ✅ Validation criteria (must-pass and nice-to-have)
7. ✅ Monte Carlo simulation
8. ✅ Sensitivity analysis
9. ✅ Backtest report format
10. ✅ Edge cases and handling

---

### 📋 Points Requiring Your Approval:

1. **Training Window (3 years):** Sufficient for parameter estimation?

2. **Walk-Forward Step (1 year):** Appropriate retraining frequency?

3. **Slippage (0.5 pips):** Conservative enough?

4. **Min Sharpe (1.5):** Minimum acceptable?

5. **Max Drawdown (15%):** Risk limit appropriate?

6. **Monte Carlo (1000 runs):** Sufficient for significance?

7. **Scenario Coverage:** Comprehensive enough?

8. **Red Flags:** Sharpe > 4.0 = likely overfitting — acceptable?

---

**Please review and approve (or request modifications) before I proceed to Phase 17 — Robustness.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
