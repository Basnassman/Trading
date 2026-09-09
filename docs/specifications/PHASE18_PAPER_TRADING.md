# PHASE 18 — PAPER TRADING

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the **Paper Trading** framework — a live-data simulation phase that validates the system's real-world performance before committing real capital.

Paper Trading bridges the gap between backtesting (historical) and live trading (real money).

This engine produces:
1. Live data → Signal → Paper order pipeline
2. Backtest vs. Paper Trading comparison
3. Slippage/Spread/Latency measurement
4. Signal timing analysis
5. Entry/Exit difference tracking
6. Go/No-Go decision for live trading

---

## B — PAPER TRADING FLOW

### B.1 — Pipeline

```
Live Market Data (MT5)
    ↓
Real-Time Engine Computation
    ├── Phase 2: Market Structure
    ├── Phase 3: Liquidity
    ├── Phase 4: Flow
    ├── Phase 5: Trend/Momentum/Volatility
    ├── Phase 6: GSI
    ├── Phase 7: News/Macro
    ├── Phase 8: Historical
    ├── Phase 9: Regime
    ├── Phase 10: Probability
    ├── Phase 11: Setup
    ├── Phase 12: Risk
    ├── Phase 13: Trade Management
    ├── Phase 14: No-Trade
    └── Phase 15: Decision
    ↓
Signal Generated
    ↓
Paper Order (Simulated)
    ├── Record intended entry/SL/TP
    ├── Record actual market price
    ├── Simulate execution
    └── Track P&L
    ↓
Performance Logging
    ↓
Backtest vs. Paper Comparison
    ↓
Go/No-Go Decision
```

### B.2 — Paper Order Execution

Paper orders are simulated with realistic conditions:

| Factor | Paper Trading Simulation |
|--------|------------------------|
| Entry Price | Actual market price at signal time |
| Slippage | Measured from order to fill |
| Spread | Actual spread at execution time |
| Latency | Time from signal to execution |
| Partial Fills | Not modeled (assume full fill) |
| Requotes | Logged if price moved |

### B.3 — Paper Trading Duration

| Phase | Duration | Purpose |
|-------|----------|---------|
| Minimum | 4 weeks | Statistical significance |
| Recommended | 8 weeks | Comprehensive validation |
| Maximum | 12 weeks | If criteria not met |

---

## C — COMPARISON METRICS

### C.1 — Backtest vs. Paper Trading

| Metric | Backtest | Paper | Acceptable Difference |
|--------|---------|-------|----------------------|
| Win Rate | X% | Y% | |X - Y| < 5% |
| Sharpe Ratio | X | Y | Y > 0.8 × X |
| Max Drawdown | X% | Y% | Y < 1.3 × X |
| Avg Trade Duration | X bars | Y bars | |X - Y| < 20% |
| Profit Factor | X | Y | Y > 0.7 × X |
| Total Trades | X | Y | Y > 0.5 × X |

### C.2 — Execution Quality Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| Slippage | Actual fill - Intended fill | < 1.0 pip average |
| Spread Cost | Average spread at execution | < 2.0 pips |
| Latency | Time from signal to fill | < 1.0 second |
| Entry Difference | Paper entry vs. backtest entry | < 0.5 pip average |
| Exit Difference | Paper exit vs. backtest exit | < 1.0 pip average |

### C.3 — Signal Timing Analysis

| Metric | Definition | Target |
|--------|-----------|--------|
| Signal-to-Execution Time | Time from decision to paper order | < 2 seconds |
| Signal Accuracy | % of signals that would have been profitable | > 55% |
| Signal Rejection Rate | % of signals blocked by No-Trade | Logged |
| Signal Stability | How often signals change before execution | < 20% |

---

## D — MEASUREMENT METHODOLOGY

### D.1 — Slippage Measurement

$$\text{Slippage}_i = \text{FillPrice}_i - \text{IntendedPrice}_i$$

For LONG: positive slippage = worse fill (paid more)
For SHORT: negative slippage = worse fill (sold less)

$$\text{AvgSlippage} = \frac{1}{N} \sum_{i=1}^{N} |\text{Slippage}_i|$$

### D.2 — Spread Measurement

$$\text{SpreadCost}_i = \text{Ask}_i - \text{Bid}_i \quad \text{(at execution time)}$$

$$\text{AvgSpread} = \frac{1}{N} \sum_{i=1}^{N} \text{SpreadCost}_i$$

### D.3 — Latency Measurement

$$\text{Latency}_i = \text{ExecutionTime}_i - \text{SignalTime}_i$$

$$\text{AvgLatency} = \frac{1}{N} \sum_{i=1}^{N} \text{Latency}_i$$

### D.4 — Entry Difference

$$\text{EntryDiff}_i = |\text{PaperEntry}_i - \text{BacktestEntry}_i|$$

$$\text{AvgEntryDiff} = \frac{1}{N} \sum_{i=1}^{N} \text{EntryDiff}_i$$

### D.5 — Exit Difference

$$\text{ExitDiff}_i = |\text{PaperExit}_i - \text{BacktestExit}_i|$$

$$\text{AvgExitDiff} = \frac{1}{N} \sum_{i=1}^{N} \text{ExitDiff}_i$$

---

## E — ACCEPTANCE CRITERIA

### E.1 — Go/No-Go Decision

$$\text{GoLive} \iff \bigwedge_{i=1}^{K} \text{Criterion}_i = \text{Pass}$$

### E.2 — Must-Pass Criteria

| Criterion | Threshold | Consequence if Failed |
|-----------|-----------|----------------------|
| Paper Sharpe > 0 | Sharpe > 0 | Do not go live |
| Paper Win Rate > 50% | WR > 50% | Investigate |
| Avg Slippage < 1.5 pips | < 1.5 | Investigate execution |
| Avg Spread < 2.5 pips | < 2.5 | Check broker |
| Avg Latency < 2.0 sec | < 2.0 | Check infrastructure |
| Backtest Degradation < 30% | Sharpe_y > 0.7 × Sharpe_x | Investigate |
| Minimum Trades | ≥ 30 trades in paper period | Extend paper period |
| No Catastrophic Loss | Max DD < 25% | Do not go live |

### E.3 — Nice-to-Have Criteria

| Criterion | Threshold | Benefit |
|-----------|-----------|---------|
| Paper Sharpe > 1.0 | > 1.0 | High confidence |
| Degradation < 15% | Sharpe_y > 0.85 × Sharpe_x | Strong consistency |
| Avg Slippage < 0.5 pips | < 0.5 | Excellent execution |
| All sessions profitable | Positive P&L per session | Robust |

### E.4 — Red Flags

| Red Flag | Action |
|----------|--------|
| Paper Sharpe << Backtest Sharpe | Investigate overfitting |
| Paper Win Rate << Backtest Win Rate | Investigate signal quality |
| High slippage | Check broker/execution |
| Signal stability low | Investigate signal generation |
| Few trades | Extend paper period |

---

## F — PAPER TRADING LOG

### F.1 — Per-Trade Log

| Field | Description |
|-------|-------------|
| Trade ID | Unique identifier |
| Timestamp | When signal was generated |
| Direction | Long/Short |
| Intended Entry | Price at signal time |
| Actual Entry | Fill price |
| Entry Difference | Actual - Intended |
| Slippage | Execution slippage |
| Spread | Spread at execution |
| Latency | Signal to execution time |
| Stop Loss | Initial SL |
| Take Profit | Initial TP |
| Exit Price | Actual exit |
| Exit Reason | SL/TP/Trailing/Emergency |
| P&L | Realized profit/loss |
| Duration | Bars held |
| Backtest Comparison | What backtest would have done |

### F.2 — Daily Summary

```
=== PAPER TRADING DAILY SUMMARY ===
Date: 2026-09-15

Trades Today: 3
Wins: 2 | Losses: 1
Win Rate: 66.7%
Daily P&L: +$185.20

Avg Slippage: 0.8 pips
Avg Spread: 1.2 pips
Avg Latency: 0.45 seconds

Active Positions: 1
Total Paper Equity: $10,245.30
Drawdown from Peak: 1.2%

Signals Generated: 5
Signals Executed: 3
Signals Blocked (No-Trade): 2
```

### F.3 — Weekly Summary

```
=== PAPER TRADING WEEKLY SUMMARY ===
Week: 2026-W38 (Sep 15–19)

Total Trades: 14
Win Rate: 57.1%
Weekly P&L: +$892.40
Sharpe (Week): 2.15

Avg Slippage: 0.75 pips
Avg Spread: 1.15 pips
Avg Latency: 0.42 seconds

=== BACKTEST COMPARISON ===
Backtest Win Rate: 58.3% | Paper: 57.1% (Δ: -1.2%)
Backtest Sharpe: 1.87 | Paper: 2.15 (Δ: +15.0%)
Backtest Avg Trade: +$32.15 | Paper: +$63.74

Assessment: CONSISTENT ✅
```

---

## G — BACKTEST VS. PAPER ANALYSIS

### G.1 — Performance Comparison Table

| Metric | Backtest | Paper | Difference | Status |
|--------|---------|-------|-----------|--------|
| Win Rate | 58.3% | 57.1% | -1.2% | ✅ Pass |
| Sharpe Ratio | 1.87 | 2.15 | +15.0% | ✅ Pass |
| Max Drawdown | 11.2% | 8.5% | -24.1% | ✅ Pass |
| Profit Factor | 1.82 | 1.95 | +7.1% | ✅ Pass |
| Avg Trade | $32.15 | $63.74 | +98.3% | ✅ Pass |
| Total Trades | 1,247 | 45* | — | ⚠️ Sample |

*Paper period is shorter than backtest period.

### G.2 — Execution Quality Table

| Metric | Measured | Target | Status |
|--------|----------|--------|--------|
| Avg Slippage | 0.75 pips | < 1.5 pips | ✅ Pass |
| Avg Spread | 1.15 pips | < 2.5 pips | ✅ Pass |
| Avg Latency | 0.42 sec | < 2.0 sec | ✅ Pass |
| Entry Difference | 0.35 pips | < 0.5 pip | ✅ Pass |
| Exit Difference | 0.62 pips | < 1.0 pip | ✅ Pass |

### G.3 — Degradation Analysis

$$\text{Degradation} = \frac{\text{BacktestMetric} - \text{PaperMetric}}{\text{BacktestMetric}} \times 100$$

| Metric | Degradation | Acceptable? |
|--------|------------|-------------|
| Sharpe | -15% (Paper better) | ✅ |
| Win Rate | +1.2% | ✅ |
| Profit Factor | -7.1% | ✅ |
| Max Drawdown | +24.1% (Paper better) | ✅ |

---

## H — GO/LIVE DECISION

### H.1 — Decision Framework

```
Paper Trading Complete (≥ 4 weeks)
    ↓
Compare Backtest vs. Paper
    ↓
Evaluate Acceptance Criteria
    ├── ALL PASS → GO LIVE
    ├── MOST PASS → INVESTIGATE → RE-PAPER or GO LIVE
    └── MAJOR FAIL → DO NOT GO LIVE → FIX ISSUES
```

### H.2 — Go Live Checklist

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Paper period ≥ 4 weeks | ☐ |
| 2 | Minimum 30 trades | ☐ |
| 3 | Paper Sharpe > 0 | ☐ |
| 4 | Paper Win Rate > 50% | ☐ |
| 5 | Degradation < 30% | ☐ |
| 6 | Slippage < 1.5 pips | ☐ |
| 7 | Spread < 2.5 pips | ☐ |
| 8 | Latency < 2.0 sec | ☐ |
| 9 | Max DD < 25% | ☐ |
| 10 | No catastrophic loss | ☐ |
| 11 | All sessions tested | ☐ |
| 12 | Risk limits respected | ☐ |

### H.3 — Live Trading Parameters

When going live:

| Parameter | Paper Value | Live Value | Change |
|-----------|------------|-----------|--------|
| Position Size | 100% | 50% (start) | Reduce |
| Risk per Trade | 1% | 0.5% (start) | Reduce |
| Max Positions | 5 | 3 (start) | Reduce |
| Max Drawdown | 20% | 15% (start) | Tighter |

**Rationale:** Start conservative; increase after proven live performance.

---

## I — EDGE CASES

### I.1 — Paper Trading Issues

| Scenario | Handling |
|----------|----------|
| No trades generated | Extend paper period; check system |
| All trades profitable | Likely paper execution is too optimistic |
| High slippage | Check broker; may need different broker |
| High latency | Check infrastructure; may need VPS |
| Signal instability | Investigate signal generation |

### I.2 — Comparison Issues

| Scenario | Handling |
|----------|----------|
| Paper much worse than backtest | Investigate overfitting |
| Paper much better than backtest | Unlikely; check paper execution |
| Insufficient trades | Extend paper period |

---

## J — BIAS PREVENTION

### J.1 — Look-Ahead Bias

**Prevention:**
1. Paper orders executed at actual market price
2. No future data in signal generation
3. Same temporal rules as backtest

### J.2 — Execution Bias

**Prevention:**
1. Paper execution uses actual spread/slippage
2. No favorable fills assumed
3. Latency measured realistically

---

## K — WHAT IS FIXED

### K.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Minimum Paper Period | 4 weeks | Statistical significance |
| Minimum Trades | 30 | Minimum sample |
| Max Degradation | 30% | Acceptable difference |
| Max Slippage | 1.5 pips | Execution quality |
| Max Spread | 2.5 pips | Broker quality |
| Max Latency | 2.0 sec | Infrastructure quality |
| Start Position Size | 50% | Conservative start |
| Start Risk per Trade | 0.5% | Conservative start |

### K.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal paper period | From paper trading results |
| Optimal start parameters | From paper trading results |
| Broker selection | From execution quality |
| Infrastructure optimization | From latency measurements |

---

## L — WHAT REQUIRES TESTING

### L.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | Paper trading results are consistent with backtest | Compare metrics | Degradation < 30% |
| H2 | Slippage is within acceptable bounds | Measure actual | < 1.5 pips |
| H3 | Signals are stable in live conditions | Measure signal changes | < 20% instability |
| H4 | System performs across all sessions | Check per-session | All positive |
| H5 | Risk limits are respected in live conditions | Monitor | No breaches |

### L.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Is 4 weeks sufficient? | From paper results |
| Q2 | Should we paper trade during news events? | Yes, for validation |
| Q3 | How to handle different broker conditions? | Test multiple brokers |
| Q4 | Should paper trading include position management? | Yes, full simulation |

---

## M — OUTPUT SCHEMA

### M.1 — Paper Trading Result

```python
@dataclass(frozen=True)
class PaperTradingResult:
    """Complete paper trading result."""
    
    # Period
    start_date: datetime
    end_date: datetime
    duration_weeks: int
    
    # Performance
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float
    
    # Execution Quality
    avg_slippage: float
    avg_spread: float
    avg_latency: float
    avg_entry_diff: float
    avg_exit_diff: float
    
    # Backtest Comparison
    backtest_win_rate: float
    backtest_sharpe: float
    degradation_win_rate: float
    degradation_sharpe: float
    
    # Session Analysis
    session_results: dict[str, SessionResult]
    
    # Go/No-Go
    criteria_met: dict[str, bool]
    all_criteria_met: bool
    go_live_recommendation: str
    
    # Trades
    trades: list[PaperTrade]
```

---

## N — DECISION OUTPUT

### N.1 — Paper Trading Summary

```
╔══════════════════════════════════════════════════════════════╗
║              PAPER TRADING REPORT v1.0                       ║
╠══════════════════════════════════════════════════════════════╣
║ Period: Sep 1 – Sep 29, 2026 (4 weeks)                     ║
║ Total Trades: 45                                            ║
╠══════════════════════════════════════════════════════════════╣
║ PERFORMANCE                                                  ║
║ Win Rate: 57.1% | Sharpe: 2.15 | PF: 1.95                  ║
║ Total P&L: +$2,867.30 | Max DD: 8.5%                       ║
║                                                              ║
║ EXECUTION QUALITY                                            ║
║ Avg Slippage: 0.75 pips ✅                                  ║
║ Avg Spread: 1.15 pips ✅                                    ║
║ Avg Latency: 0.42 sec ✅                                    ║
║                                                              ║
║ BACKTEST COMPARISON                                          ║
║ Win Rate: 58.3% → 57.1% (Δ: -1.2%) ✅                      ║
║ Sharpe: 1.87 → 2.15 (Δ: +15.0%) ✅                         ║
║ Max DD: 11.2% → 8.5% (Δ: -24.1%) ✅                        ║
║ Degradation: -15% (Paper better) ✅                         ║
║                                                              ║
║ SESSION ANALYSIS                                             ║
║ Asian: 8 trades, WR=50%, P&L=-$45.20                       ║
║ London: 22 trades, WR=64%, P&L=+$2,150.80                  ║
║ NY: 15 trades, WR=53%, P&L=+$761.70                        ║
║                                                              ║
║ GO/LIVE CRITERIA                                             ║
║ All 12 criteria: PASS ✅                                    ║
║ Recommendation: GO LIVE ✅                                  ║
║                                                              ║
║ LIVE TRADING START PARAMETERS                               ║
║ Position Size: 50% (start)                                  ║
║ Risk per Trade: 0.5% (start)                               ║
║ Max Positions: 3 (start)                                    ║
╚══════════════════════════════════════════════════════════════╝
```

---

## O — APPROVAL GATE

### The Phase 18 — Paper Trading specification is now complete.

**Summary of what is defined:**

1. ✅ Live data → Signal → Paper order pipeline
2. ✅ Paper execution with realistic conditions
3. ✅ Backtest vs. Paper comparison metrics
4. ✅ Execution quality measurement (slippage, spread, latency)
5. ✅ Entry/Exit difference tracking
6. ✅ 12 Go/Live criteria
7. ✅ Conservative start parameters for live
8. ✅ Session analysis
9. ✅ Edge cases and handling
10. ✅ Backtest requirements
11. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **Minimum Paper Period (4 weeks):** Sufficient?

2. **Minimum Trades (30):** Enough for significance?

3. **Max Degradation (30%):** Acceptable difference?

4. **Max Slippage (1.5 pips):** Appropriate?

5. **Start Position Size (50%):** Conservative enough?

6. **Start Risk per Trade (0.5%):** Conservative enough?

7. **Go/Live Criteria (12):** Comprehensive?

8. **Session Analysis Required:** All sessions must be tested?

---

**Please review and approve (or request modifications) before I proceed to Phase 19 — Execution.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
