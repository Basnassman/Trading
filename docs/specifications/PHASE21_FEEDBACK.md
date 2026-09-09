# PHASE 21 — FEEDBACK / RESEARCH

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the **Feedback and Research** framework — capturing every trade's complete context and using historical performance data to improve the system over time.

This engine produces:
1. Complete trade data storage (every field specified)
2. Performance analysis by dimension
3. Model weakness identification
4. Regime performance analysis
5. Setup quality analysis
6. Parameter stability monitoring
7. Continuous improvement recommendations

**Critical Rule:** Every trade is a data point for learning. No trade is wasted.

---

## B — TRADE DATA STORAGE

### B.1 — Required Fields (Every Trade)

| Field | Type | Description |
|-------|------|-------------|
| `trade_id` | string | Unique identifier |
| `timestamp_entry` | datetime | When trade was entered |
| `timestamp_exit` | datetime | When trade was closed |
| `direction` | string | "long" or "short" |
| `entry_price` | float | Actual entry price |
| `exit_price` | float | Actual exit price |
| `exit_reason` | string | "tp1", "tp2", "tp3", "sl", "trailing", "emergency", "manual" |
| `lots` | float | Position size |
| `pnl` | float | Realized profit/loss |
| `pnl_pct` | float | P&L as % of equity |
| `duration_bars` | int | Bars held |
| `duration_minutes` | int | Minutes held |

### B.2 — Market Context Fields

| Field | Type | Description |
|-------|------|-------------|
| `market_regime` | string | Regime at entry (Phase 9) |
| `gsi_score` | float | GSI at entry (Phase 6) |
| `structure_score` | float | Structure Score at entry (Phase 2) |
| `liquidity_score` | float | Liquidity Score at entry (Phase 3) |
| `flow_score` | float | Flow Score at entry (Phase 4) |
| `trend_score` | float | Trend Score at entry (Phase 5) |
| `momentum_score` | float | Momentum Score at entry (Phase 5) |
| `volatility_score` | float | Volatility Score at entry (Phase 5) |
| `atr` | float | ATR at entry |
| `news_score` | float | News Score at entry (Phase 7) |
| `macro_score` | float | Macro Score at entry (Phase 7) |
| `dxy_value` | float | DXY at entry |
| `yield_10y` | float | 10Y Yield at entry |

### B.3 — Setup Quality Fields

| Field | Type | Description |
|-------|------|-------------|
| `setup_quality` | float | Setup quality score (Phase 11) |
| `setup_type` | string | "bos", "retest", "mss", "candle" |
| `rr_ratio` | float | Risk:Reward at entry |
| `probability_long` | float | P(Long) at entry |
| `probability_short` | float | P(Short) at entry |
| `confidence` | float | Confidence at entry |
| `families_aligned` | int | Number of families aligned |

### B.4 — Execution Quality Fields

| Field | Type | Description |
|-------|------|-------------|
| `intended_entry` | float | Price at signal time |
| `actual_entry` | float | Fill price |
| `slippage` | float | Actual - Intended |
| `spread` | float | Spread at execution |
| `latency_ms` | float | Signal to execution time |
| `sl_price` | float | Stop loss price |
| `tp1_price` | float | Take profit 1 price |
| `tp2_price` | float | Take profit 2 price |
| `tp3_price` | float | Take profit 3 price |

### B.5 — Outcome Fields

| Field | Type | Description |
|-------|------|-------------|
| `max_favorable_excursion` | float | Best P&L reached during trade |
| `max_adverse_excursion` | float | Worst P&L reached during trade |
| `mfe_pips` | float | MFE in pips |
| `mae_pips` | float | MAE in pips |
| `mfe_price` | float | Price at MFE |
| `mae_price` | float | Price at MAE |
| `result` | string | "win", "loss", "breakeven" |
| `r_multiple` | float | P&L / Initial Risk |

### B.6 — Session Fields

| Field | Type | Description |
|-------|------|-------------|
| `session` | string | "asian", "london", "overlap", "newyork" |
| `day_of_week` | int | 0=Monday, 6=Sunday |
| `hour_of_day` | int | 0–23 UTC |

---

## C — DATABASE SCHEMA

### C.1 — Trades Table

```sql
CREATE TABLE trades (
    trade_id VARCHAR(50) PRIMARY KEY,
    
    -- Timing
    timestamp_entry TIMESTAMP NOT NULL,
    timestamp_exit TIMESTAMP,
    duration_bars INT,
    duration_minutes INT,
    
    -- Trade Details
    direction VARCHAR(10) NOT NULL,
    entry_price DECIMAL(10,2) NOT NULL,
    exit_price DECIMAL(10,2),
    exit_reason VARCHAR(20),
    lots DECIMAL(5,2) NOT NULL,
    pnl DECIMAL(10,2),
    pnl_pct DECIMAL(5,4),
    
    -- Market Context
    market_regime VARCHAR(20),
    gsi_score DECIMAL(5,2),
    structure_score DECIMAL(5,2),
    liquidity_score DECIMAL(5,2),
    flow_score DECIMAL(5,2),
    trend_score DECIMAL(5,2),
    momentum_score DECIMAL(5,2),
    volatility_score DECIMAL(5,2),
    atr DECIMAL(10,2),
    news_score DECIMAL(5,2),
    macro_score DECIMAL(5,2),
    dxy_value DECIMAL(10,2),
    yield_10y DECIMAL(5,3),
    
    -- Setup Quality
    setup_quality DECIMAL(5,2),
    setup_type VARCHAR(20),
    rr_ratio DECIMAL(5,2),
    probability_long DECIMAL(5,4),
    probability_short DECIMAL(5,4),
    confidence DECIMAL(5,4),
    families_aligned INT,
    
    -- Execution Quality
    intended_entry DECIMAL(10,2),
    slippage DECIMAL(5,2),
    spread DECIMAL(5,2),
    latency_ms DECIMAL(8,2),
    sl_price DECIMAL(10,2),
    tp1_price DECIMAL(10,2),
    tp2_price DECIMAL(10,2),
    tp3_price DECIMAL(10,2),
    
    -- Outcome
    max_favorable_excursion DECIMAL(10,2),
    max_adverse_excursion DECIMAL(10,2),
    mfe_pips DECIMAL(5,2),
    mae_pips DECIMAL(5,2),
    result VARCHAR(10),
    r_multiple DECIMAL(5,2),
    
    -- Session
    session VARCHAR(20),
    day_of_week INT,
    hour_of_day INT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### C.2 — Daily Performance Table

```sql
CREATE TABLE daily_performance (
    date DATE PRIMARY KEY,
    trades INT,
    wins INT,
    losses INT,
    win_rate DECIMAL(5,4),
    total_pnl DECIMAL(10,2),
    max_drawdown DECIMAL(5,4),
    avg_slippage DECIMAL(5,2),
    avg_spread DECIMAL(5,2),
    avg_latency DECIMAL(8,2),
    regimes_traded JSON,
    setups_used JSON
);
```

---

## D — ANALYSIS DIMENSIONS

### D.1 — Performance by Regime

$$\text{Performance}_{\text{regime}} = f(\text{Win Rate}, \text{Sharpe}, \text{Avg R}, \text{Count})$$

| Regime | Trades | Win Rate | Sharpe | Avg R | Assessment |
|--------|--------|----------|--------|-------|------------|
| Normal Trend | 45 | 62% | 2.15 | 1.8 | Strong |
| Range | 28 | 48% | 0.85 | 0.9 | Weak |
| Breakout | 15 | 67% | 2.45 | 2.1 | Strong |
| High Volatility | 12 | 50% | 1.10 | 1.2 | Moderate |
| Post-News | 8 | 55% | 1.35 | 1.4 | Moderate |

**Insight:** Range regime is weakest → consider reducing trades or adjusting parameters.

### D.2 — Performance by Setup Type

$$\text{Performance}_{\text{setup}} = f(\text{Win Rate}, \text{Sharpe}, \text{Avg R}, \text{Count})$$

| Setup Type | Trades | Win Rate | Sharpe | Avg R | Assessment |
|-----------|--------|----------|--------|-------|------------|
| BOS Entry | 52 | 60% | 1.95 | 1.7 | Strong |
| Retest Entry | 35 | 65% | 2.25 | 1.9 | Strong |
| MSS/CHoCH | 18 | 50% | 1.10 | 1.1 | Moderate |
| Candle Confirmation | 13 | 45% | 0.75 | 0.8 | Weak |

**Insight:** Candle Confirmation is weakest → consider removing or improving.

### D.3 — Performance by Session

| Session | Trades | Win Rate | Sharpe | Avg R | Assessment |
|---------|--------|----------|--------|-------|------------|
| Asian | 15 | 47% | 0.80 | 0.85 | Weak |
| London | 52 | 63% | 2.15 | 1.75 | Strong |
| Overlap | 28 | 60% | 1.85 | 1.65 | Strong |
| New York | 33 | 55% | 1.45 | 1.40 | Moderate |

**Insight:** Asian session is weakest → consider reducing trades or skipping.

### D.4 — Performance by Probability Bucket

| P(Long) Bucket | Trades | Win Rate | Expected | Actual | Calibration |
|---------------|--------|----------|----------|--------|-------------|
| 55–60% | 25 | 52% | 57.5% | 52% | Under-performing |
| 60–65% | 35 | 58% | 62.5% | 58% | Slightly under |
| 65–70% | 30 | 63% | 67.5% | 63% | Slightly under |
| 70–75% | 20 | 68% | 72.5% | 68% | Slightly under |
| 75%+ | 15 | 73% | 77.5% | 73% | Slightly under |

**Insight:** Probabilities are slightly over-estimated → recalibrate.

### D.5 — Performance by Day of Week

| Day | Trades | Win Rate | Sharpe | Assessment |
|-----|--------|----------|--------|------------|
| Monday | 22 | 55% | 1.35 | Moderate |
| Tuesday | 28 | 62% | 1.95 | Strong |
| Wednesday | 30 | 60% | 1.85 | Strong |
| Thursday | 25 | 58% | 1.65 | Moderate |
| Friday | 20 | 52% | 1.10 | Moderate (cautious) |

### D.6 — Performance by Hour

| Hour (UTC) | Trades | Win Rate | Sharpe | Assessment |
|-----------|--------|----------|--------|------------|
| 00–04 | 8 | 45% | 0.70 | Weak (Asian) |
| 07–09 | 18 | 65% | 2.20 | Strong (London open) |
| 12–14 | 25 | 62% | 1.95 | Strong (NY open) |
| 15–17 | 20 | 58% | 1.65 | Moderate |
| 18–21 | 12 | 50% | 0.95 | Weak (late NY) |

---

## E — MODEL WEAKNESS IDENTIFICATION

### E.1 — Weakness Categories

| Category | Indicators | Action |
|----------|-----------|--------|
| **Regime Weakness** | Low win rate in specific regime | Reduce trades or adjust parameters |
| **Setup Weakness** | Low win rate for specific setup | Improve or remove setup |
| **Session Weakness** | Low win rate in specific session | Skip session or adjust |
| **Probability Weakness** | Calibration error > 10% | Recalibrate |
| **Execution Weakness** | High slippage/latency | Improve execution |
| **Timing Weakness** | Low win rate at specific hours | Avoid those hours |

### E.2 — Weakness Detection Algorithm

```
For each dimension d (regime, setup, session, etc.):
    For each bucket b in dimension d:
        1. Compute win rate, Sharpe, Avg R
        2. Compare to overall average
        3. If performance < 70% of overall:
            - Flag as weakness
            - Compute severity
            - Generate recommendation
```

### E.3 — Weakness Severity

$$\text{Severity} = \frac{\text{OverallPerformance} - \text{BucketPerformance}}{\text{OverallPerformance}}$$

| Severity | Classification | Action |
|----------|---------------|--------|
| < 10% | Minor | Monitor |
| 10–20% | Moderate | Investigate |
| 20–30% | Significant | Consider changes |
| > 30% | Critical | Immediate action |

---

## F — PARAMETER STABILITY MONITORING

### F.1 — What to Monitor

| Parameter | Monitoring Method | Alert Threshold |
|-----------|------------------|-----------------|
| GSI weights | Track performance per weight set | Performance drop > 10% |
| SL/TP multipliers | Track outcome distribution | Win rate drop > 5% |
| Setup thresholds | Track signal quality | False signal increase > 20% |
| Risk parameters | Track risk-adjusted returns | Sharpe drop > 0.5 |

### F.2 — Stability Score

$$\text{StabilityScore} = 1 - \frac{\text{StdDev}(\text{Performance}_{\text{recent}})}{\text{Mean}(\text{Performance}_{\text{recent}})}$$

Where recent = last 50 trades.

| Stability | Score | Action |
|-----------|-------|--------|
| High | > 0.8 | Continue |
| Moderate | 0.6 – 0.8 | Monitor closely |
| Low | < 0.6 | Investigate; consider recalibration |

### F.3 — Recalibration Triggers

| Trigger | Action |
|---------|--------|
| Stability < 0.6 | Recalibrate affected parameters |
| Win rate drops > 10% over 30 trades | Review system |
| Sharpe drops > 0.5 over 30 trades | Review system |
| Calibration ECE > 0.15 | Recalibrate probabilities |

---

## G — CONTINUOUS IMPROVEMENT

### G.1 — Weekly Review

```
=== WEEKLY REVIEW ===
Period: Week 38 (Sep 15–19, 2026)

=== PERFORMANCE ===
Trades: 14 | Win Rate: 57.1% | P&L: +$892.40
Sharpe: 2.15 | Max DD: 3.2%

=== REGIME ANALYSIS ===
Trend: 8 trades, WR=63%, Strong ✅
Range: 3 trades, WR=33%, Weak ⚠️
Breakout: 3 trades, WR=67%, Strong ✅

=== SETUP ANALYSIS ===
BOS: 6 trades, WR=67%, Strong ✅
Retest: 5 trades, WR=60%, Strong ✅
MSS: 3 trades, WR=33%, Weak ⚠️

=== RECOMMENDATIONS ===
1. Consider reducing Range trades
2. MSS setup needs improvement
3. Overall system performing well

=== NEXT WEEK FOCUS ===
- Monitor Range regime performance
- Review MSS setup logic
- Continue Phase 1 live trading
```

### G.2 — Monthly Review

```
=== MONTHLY REVIEW ===
Period: September 2026

=== PERFORMANCE SUMMARY ===
Total Trades: 52 | Win Rate: 58.3%
Total P&L: +$3,245.60 | Sharpe: 1.95
Max DD: 5.8% | Recovery Factor: 3.2

=== COMPARISON ===
vs. Backtest: Degradation = -8.5% (Acceptable) ✅
vs. Paper Trading: Degradation = -3.2% (Consistent) ✅

=== SCALING ASSESSMENT ===
Phase 1 → Phase 2:
  Sharpe > 1.0: ✅ (1.95)
  Max DD < 8%: ✅ (5.8%)
  Win Rate > 50%: ✅ (58.3%)
  Duration ≥ 4 weeks: ✅ (4 weeks)
  
RECOMMENDATION: SCALE TO PHASE 2 ✅

=== PARAMETER STABILITY ===
GSI Weights: Stable (Score: 0.85) ✅
SL/TP Multipliers: Stable (Score: 0.82) ✅
Setup Thresholds: Stable (Score: 0.78) ✅

=== ACTION ITEMS ===
1. Scale to Phase 2 (increase position size to 50%)
2. Continue monitoring Range regime
3. Review MSS setup in Phase 2
```

### G.3 — Quarterly Research

```
=== QUARTERLY RESEARCH ===
Period: Q3 2026 (Jul–Sep)

=== KEY FINDINGS ===
1. London session is most profitable (63% WR)
2. BOS + Retest setup is strongest (65% WR)
3. Range regime needs improvement (48% WR)
4. Probabilities slightly over-estimated (ECE=0.12)

=== RECOMMENDATIONS ===
1. Increase London session weight
2. Prioritize BOS + Retest setups
3. Reduce Range regime trades
4. Recalibrate probabilities

=== SYSTEM HEALTH ===
Overall Score: 78/100 (Good)
Stability: 0.82 (High)
Robustness: Confirmed
Ready for continued live trading
```

---

## H — FEEDBACK LOOP

### H.1 — Feedback Integration

```
Live Trading
    ↓
Trade Data Stored
    ↓
Performance Analysis (Weekly/Monthly/Quarterly)
    ↓
Weakness Identification
    ↓
Recommendation Generation
    ↓
Parameter Adjustment (if approved)
    ↓
Backtest Validation (if parameters changed)
    ↓
Paper Trading (if significant changes)
    ↓
Live Trading (with new parameters)
```

### H.2 — Change Management

| Change Type | Approval Required | Validation Required |
|-------------|------------------|-------------------|
| Minor parameter tweak | Operator | Backtest only |
| Major parameter change | Operator + Review | Backtest + Paper |
| Setup removal/addition | Full review | Backtest + Paper |
| Regime change | Full review | Backtest + Paper |

### H.3 — Version Control

Every parameter change is versioned:

$$\text{Version} = v\text{MAJOR.MINOR.PATCH}$$

| Change Type | Version Bump |
|-------------|-------------|
| Minor tweak | PATCH |
| Parameter change | MINOR |
| Architecture change | MAJOR |

---

## I — EDGE CASES

### I.1 — Data Issues

| Scenario | Handling |
|----------|----------|
| Missing trade data | Flag; do not include in analysis |
| Corrupted data | Restore from backup |
| Insufficient trades | Extend analysis period |

### I.2 — Analysis Issues

| Scenario | Handling |
|----------|----------|
| Too few trades per bucket | Combine buckets |
| Conflicting signals | Use majority rule |
| Overfitting to recent data | Use longer lookback |

---

## J — WHAT IS FIXED

### J.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Trade Fields | 50+ fields | Comprehensive capture |
| Database | PostgreSQL | Existing infrastructure |
| Review Frequency | Weekly/Monthly/Quarterly | Regular cadence |
| Weakness Threshold | 70% of overall | Meaningful detection |
| Stability Threshold | 0.6 minimum | Acceptable stability |
| Calibration Threshold | ECE < 0.15 | Recalibration trigger |
| Version Control | MAJOR.MINOR.PATCH | Change tracking |

### J.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Specific parameter adjustments | From analysis results |
| Setup modifications | From weakness analysis |
| Regime-specific tuning | From performance data |
| Research priorities | From quarterly reviews |

---

## K — WHAT REQUIRES TESTING

### K.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | Trade data capture is complete | Audit sample | 100% fields populated |
| H2 | Weakness detection identifies real issues | Backtest analysis | Known weaknesses detected |
| H3 | Parameter stability monitoring works | Simulate degradation | Alert triggered |
| H4 | Feedback loop improves performance | Track over time | Performance improves |
| H5 | Version control prevents regression | Test changes | No regression |

### K.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | How often should we recalibrate? | From stability monitoring |
| Q2 | Which dimensions are most informative? | From analysis results |
| Q3 | Should we automate parameter adjustments? | From experience |
| Q4 | How to handle regime changes in analysis? | Test approaches |

---

## L — OUTPUT SCHEMA

### L.1 — Trade Record

```python
@dataclass(frozen=True)
class TradeRecord:
    """Complete trade record for storage."""
    
    # Identity
    trade_id: str
    
    # Timing
    timestamp_entry: datetime
    timestamp_exit: datetime | None
    duration_bars: int | None
    duration_minutes: int | None
    
    # Trade
    direction: str
    entry_price: float
    exit_price: float | None
    exit_reason: str | None
    lots: float
    pnl: float | None
    pnl_pct: float | None
    
    # Market Context
    market_regime: str
    gsi_score: float
    structure_score: float
    liquidity_score: float
    flow_score: float
    trend_score: float
    momentum_score: float
    volatility_score: float
    atr: float
    news_score: float
    macro_score: float
    dxy_value: float
    yield_10y: float
    
    # Setup
    setup_quality: float
    setup_type: str
    rr_ratio: float
    probability_long: float
    probability_short: float
    confidence: float
    families_aligned: int
    
    # Execution
    intended_entry: float
    slippage: float
    spread: float
    latency_ms: float
    sl_price: float
    tp1_price: float
    tp2_price: float
    tp3_price: float
    
    # Outcome
    max_favorable_excursion: float
    max_adverse_excursion: float
    mfe_pips: float
    mae_pips: float
    result: str
    r_multiple: float
    
    # Session
    session: str
    day_of_week: int
    hour_of_day: int
```

---

## M — DECISION OUTPUT

### M.1 — System Health Report

```
╔══════════════════════════════════════════════════════════════╗
║              SYSTEM HEALTH REPORT                            ║
╠══════════════════════════════════════════════════════════════╣
║ Overall Health: 78/100 (GOOD) ✅                            ║
║                                                              ║
║ PERFORMANCE                                                  ║
║ Total Trades: 156 | Win Rate: 58.3%                        ║
║ Sharpe: 1.87 | Max DD: 8.5%                                ║
║ Expectancy: $32.15 | Profit Factor: 1.82                   ║
║                                                              ║
║ STABILITY                                                    ║
║ GSI Weights: 0.85 (Stable) ✅                               ║
║ SL/TP Multipliers: 0.82 (Stable) ✅                        ║
║ Setup Thresholds: 0.78 (Stable) ✅                          ║
║                                                              ║
║ WEAKNESSES                                                   ║
║ ⚠️ Range Regime: 48% WR (vs 58% overall)                   ║
║ ⚠️ MSS Setup: 50% WR (vs 58% overall)                     ║
║ ⚠️ Asian Session: 47% WR (vs 58% overall)                  ║
║                                                              ║
║ CALIBRATION                                                  ║
║ Probability ECE: 0.12 (Acceptable) ✅                       ║
║ Last Recalibrated: 2026-09-15                               ║
║                                                              ║
║ RECOMMENDATIONS                                              ║
║ 1. Reduce Range regime trades                               ║
║ 2. Improve MSS setup logic                                  ║
║ 3. Skip or reduce Asian session                             ║
║ 4. Recalibrate probabilities (ECE approaching threshold)    ║
║                                                              ║
║ NEXT REVIEW: 2026-10-01 (Monthly)                           ║
╚══════════════════════════════════════════════════════════════╝
```

---

## N — APPROVAL GATE

### The Phase 21 — Feedback/Research specification is now complete.

**Summary of what is defined:**

1. ✅ 50+ trade data fields (every aspect captured)
2. ✅ Database schema (trades + daily performance)
3. ✅ 6 analysis dimensions (regime, setup, session, probability, day, hour)
4. ✅ Weakness detection algorithm
5. ✅ Parameter stability monitoring
6. ✅ Continuous improvement framework (weekly/monthly/quarterly)
7. ✅ Feedback loop mechanism
8. ✅ Change management process
9. ✅ Version control
10. ✅ Edge cases and handling

---

### 📋 Points Requiring Your Approval:

1. **Trade Fields (50+):** Comprehensive enough? Missing any?

2. **Database Schema:** PostgreSQL appropriate?

3. **Analysis Dimensions:** Regime, Setup, Session, Probability, Day, Hour — sufficient?

4. **Weakness Threshold (70% of overall):** Appropriate?

5. **Stability Threshold (0.6):** Minimum for stability?

6. **Review Frequency:** Weekly/Monthly/Quarterly — appropriate?

7. **Feedback Loop:** Changes require backtest validation?

8. **Version Control:** MAJOR.MINOR.PATCH — sufficient?

---

**This is the FINAL phase (Phase 21 of 21). After your approval, all specifications will be complete.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
