# PHASE 20 — LIVE TRADING

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the **Live Trading** framework — the final deployment phase where real capital is at risk.

This engine produces:
1. Conservative starting parameters
2. Hard risk limits
3. Emergency stop mechanisms
4. Kill switches (daily, drawdown)
5. Connection failure protection
6. Abnormal spread protection
7. Gradual scaling plan

**Critical Rule:** Start small. Prove performance. Scale gradually.

---

## B — PRE-LIVE CHECKLIST

### B.1 — Mandatory Requirements

| # | Requirement | Status |
|---|-------------|--------|
| 1 | Backtest passes all criteria (Phase 16) | ☐ |
| 2 | Robustness testing passes (Phase 17) | ☐ |
| 3 | Paper trading ≥ 4 weeks (Phase 18) | ☐ |
| 4 | Paper trading Go/Live decision: GO | ☐ |
| 5 | Execution quality verified (Phase 19) | ☐ |
| 6 | Broker account funded | ☐ |
| 7 | VPS/Infrastructure ready | ☐ |
| 8 | Monitoring dashboard active | ☐ |
| 9 | Alert system configured (Telegram) | ☐ |
| 10 | Emergency contacts identified | ☐ |

### B.2 — Go-Live Decision

$$\text{GoLive} \iff \bigwedge_{i=1}^{10} \text{Requirement}_i = \text{Met}$$

**All 10 requirements must be met.** No exceptions.

---

## C — CONSERVATIVE STARTING PARAMETERS

### C.1 — Phase 1: Initial Live (Weeks 1–4)

| Parameter | Paper Value | Live Value | Reduction |
|-----------|------------|-----------|-----------|
| Position Size | 100% | 25% | 75% |
| Risk per Trade | 1.0% | 0.25% | 75% |
| Max Positions | 5 | 2 | 60% |
| Max Exposure | 50% | 20% | 60% |
| Max Daily Loss | 5% | 2% | 60% |
| Max Drawdown | 20% | 10% | 50% |

### C.2 — Phase 2: Scaling (Weeks 5–8)

| Parameter | Phase 1 | Phase 2 | Change |
|-----------|---------|---------|--------|
| Position Size | 25% | 50% | +100% |
| Risk per Trade | 0.25% | 0.50% | +100% |
| Max Positions | 2 | 3 | +50% |
| Max Exposure | 20% | 30% | +50% |
| Max Daily Loss | 2% | 3% | +50% |
| Max Drawdown | 10% | 15% | +50% |

### C.3 — Phase 3: Full Size (Weeks 9+)

| Parameter | Phase 2 | Phase 3 | Change |
|-----------|---------|---------|--------|
| Position Size | 50% | 100% | +100% |
| Risk per Trade | 0.50% | 1.00% | +100% |
| Max Positions | 3 | 5 | +67% |
| Max Exposure | 30% | 50% | +67% |
| Max Daily Loss | 3% | 5% | +67% |
| Max Drawdown | 15% | 20% | +33% |

### C.4 — Scaling Criteria

$$\text{ScaleUp} \iff \text{PreviousPhasePerformance} \geq \text{Threshold}$$

| Phase | Required Performance to Scale |
|-------|------------------------------|
| Phase 1 → 2 | Sharpe > 1.0, Max DD < 8%, Win Rate > 50% |
| Phase 2 → 3 | Sharpe > 1.5, Max DD < 12%, Win Rate > 55% |

### C.5 — Scale-Down Criteria

$$\text{ScaleDown} \iff \text{Performance} < \text{MinimumThreshold}$$

| Condition | Action |
|-----------|--------|
| Max DD > Phase limit | Reduce to previous phase |
| Sharpe < 0.5 for 2 weeks | Reduce to previous phase |
| 5 consecutive losses | Reduce by 50% |
| Daily loss hit limit 3 times in 1 week | Reduce to Phase 1 |

---

## D — HARD RISK LIMITS

### D.1 — Per-Trade Limits

| Limit | Value | Action if Breached |
|-------|-------|-------------------|
| Risk per Trade | 0.25% (Phase 1) | Position size capped |
| Max Lot Size | Calculated from risk | No override |
| Min Lot Size | 0.01 | Standard |
| SL Required | **MANDATORY** | No entry without SL |

### D.2 — Daily Limits

| Limit | Phase 1 | Phase 2 | Phase 3 |
|-------|---------|---------|---------|
| Max Daily Loss | 2% | 3% | 5% |
| Max Trades per Day | 10 | 15 | 20 |
| Max Daily Loss (Hard Stop) | 3% | 4% | 6% |

### D.3 — Weekly/Monthly Limits

| Limit | Phase 1 | Phase 2 | Phase 3 |
|-------|---------|---------|---------|
| Max Weekly Loss | 5% | 7% | 10% |
| Max Monthly Loss | 8% | 12% | 15% |

### D.4 — Drawdown Limits

| Limit | Phase 1 | Phase 2 | Phase 3 |
|-------|---------|---------|---------|
| Max Drawdown | 10% | 15% | 20% |
| Max Drawdown Duration | 14 days | 21 days | 30 days |

---

## E — EMERGENCY STOP

### E.1 — Emergency Conditions

| Condition | Trigger | Action |
|-----------|---------|--------|
| **Drawdown Kill** | DD > Phase max | Close ALL positions, halt |
| **Daily Kill** | Daily loss > Hard Stop | Close ALL positions, halt for day |
| **Weekly Kill** | Weekly loss > Limit | Close ALL positions, halt for week |
| **Connection Failure** | Disconnected > 5 min | Close all positions (if possible) |
| **Abnormal Spread** | Spread > 5.0 pips for > 5 min | Close all positions |
| **Price Anomaly** | Price move > 5% in 1 bar | Halt, alert operator |
| **Manual Kill** | Operator trigger | Close ALL positions, halt |

### E.2 — Emergency Stop Execution

```python
def emergency_stop(reason: str):
    """Execute emergency stop."""
    # 1. Close all positions
    for position in get_positions():
        close_position(position)
    
    # 2. Cancel all pending orders
    for order in get_pending_orders():
        cancel_order(order)
    
    # 3. Halt trading
    set_trading_state(HALT)
    
    # 4. Log emergency
    log_emergency(reason, timestamp, positions_closed)
    
    # 5. Alert operator
    send_alert(f"EMERGENCY STOP: {reason}")
    
    # 6. Require manual intervention to resume
```

### E.3 — Emergency Stop Priority

| Priority | Condition | Speed |
|----------|-----------|-------|
| 1 | Drawdown Kill | Immediate |
| 2 | Daily Kill | Immediate |
| 3 | Price Anomaly | Immediate |
| 4 | Connection Failure | Best effort |
| 5 | Abnormal Spread | Within 1 minute |
| 6 | Manual Kill | Immediate |

---

## F — KILL SWITCHES

### F.1 — Daily Kill Switch

$$\text{DailyKill} \iff \frac{|\text{DailyP\&L}|}{\text{Equity}_{\text{start}}} > \text{DAILY\_HARD\_STOP}$$

| Phase | Daily Hard Stop |
|-------|----------------|
| Phase 1 | 3% |
| Phase 2 | 4% |
| Phase 3 | 6% |

**Effect:** Close all positions, no new trades for rest of day.

**Reset:** Next trading day.

### F.2 — Maximum Drawdown Kill Switch

$$\text{DDKill} \iff \frac{\text{PeakEquity} - \text{Equity}}{\text{PeakEquity}} > \text{MAX\_DRAWDOWN}$$

| Phase | Max Drawdown |
|-------|-------------|
| Phase 1 | 10% |
| Phase 2 | 15% |
| Phase 3 | 20% |

**Effect:** Close all positions, halt trading, require manual intervention.

**Reset:** Manual only (operator must confirm system health).

### F.3 — Kill Switch State Machine

```
NORMAL → WARNING (80% of limit) → KILLED → (Manual Reset) → NORMAL
```

| State | Description | Action |
|-------|-------------|--------|
| NORMAL | All limits within bounds | Trade normally |
| WARNING | Approaching a limit | Alert; reduce caution |
| KILLED | Limit breached | Halt all trading |

---

## G — CONNECTION FAILURE PROTECTION

### G.1 — Detection

$$\text{ConnectionFailure} \iff \text{LastHeartbeat} > \text{TIMEOUT} = 5 \text{ minutes}$$

### G.2 — Response Protocol

| Duration Disconnected | Action |
|----------------------|--------|
| 0–1 min | Attempt reconnect |
| 1–3 min | Attempt reconnect; alert operator |
| 3–5 min | Attempt reconnect; prepare to close |
| > 5 min | **Close all positions** (if possible) |
| > 10 min | **Force close via broker** (if available) |

### G.3 — Position Safety

If connection is lost:
1. SL/TP orders are **already set** on broker server
2. Broker will execute SL/TP even if bot is disconnected
3. Bot only needs to close positions that need manual management

### G.4 — Reconnection Verification

After reconnection:
1. Verify all positions match expected state
2. Verify SL/TP are correctly set
3. Verify no duplicate orders
4. Resume normal operation

---

## H — ABNORMAL SPREAD PROTECTION

### H.1 — Spread Monitoring

$$\text{AbnormalSpread} \iff S_t > \text{ABNORMAL\_SPREAD\_THRESHOLD} = 5.0 \text{ pips}$$

$$\text{Duration} > \text{ABNORMAL\_SPREAD\_DURATION} = 5 \text{ minutes}$$

### H.2 — Response

| Spread Level | Action |
|-------------|--------|
| < 2.0 pips | Normal trading |
| 2.0 – 3.0 pips | Alert; reduce position size |
| 3.0 – 5.0 pips | No new entries |
| > 5.0 pips for > 5 min | **Close all positions** |

### H.3 — Spread Spike Detection

$$\text{SpreadSpike} \iff S_t > 3 \times S_{\text{avg,20}}$$

Where $S_{\text{avg,20}}$ = average spread over last 20 bars.

**Action:** Flag as potential anomaly; do not enter new trades.

---

## I — MONITORING AND ALERTS

### I.1 — Monitoring Dashboard

```
╔══════════════════════════════════════════════════════════════╗
║                    LIVE TRADING DASHBOARD                    ║
╠══════════════════════════════════════════════════════════════╣
║ Status: ACTIVE | Phase: 1 (Conservative)                    ║
║ Uptime: 99.8% | Last Heartbeat: 2s ago                     ║
║                                                              ║
║ ACCOUNT                                                      ║
║ Equity: $10,245.30 | Balance: $10,000.00                   ║
║ unrealized P&L: +$245.30                                    ║
║                                                              ║
║ RISK                                                         ║
║ Daily P&L: +$125.20 (1.25% / 2.0% limit) ✅                ║
║ Weekly P&L: +$456.80 (4.57% / 5.0% limit) ✅               ║
║ Drawdown: 1.8% (from peak) ✅                               ║
║ Open Positions: 1 / 2 ✅                                    ║
║                                                              ║
║ POSITIONS                                                    ║
║ #1234: LONG 0.42 lots @ 1848.50                             ║
║        SL: 1842.50 | TP₁: 1858.50                          ║
║        P&L: +$245.30 (+2.45%)                               ║
║                                                              ║
║ EXECUTION QUALITY                                            ║
║ Trades Today: 3 | Win Rate: 66.7%                          ║
║ Avg Slippage: 0.65 pips | Avg Latency: 0.38 sec            ║
║                                                              ║
║ KILL SWITCHES                                                ║
║ Daily: NORMAL (62.5% remaining)                             ║
║ Drawdown: NORMAL (98.2% remaining)                          ║
║ Connection: NORMAL (last heartbeat: 2s)                     ║
║ Spread: NORMAL (0.8 pips)                                   ║
╚══════════════════════════════════════════════════════════════╝
```

### I.2 — Alert System

| Alert | Channel | Frequency |
|-------|---------|-----------|
| Trade Executed | Telegram | Every trade |
| Daily Summary | Telegram | End of day |
| Warning (80% limit) | Telegram + Email | Real-time |
| Kill Switch Triggered | Telegram + Email + SMS | Immediate |
| Emergency Stop | Telegram + Email + SMS | Immediate |
| Connection Lost | Telegram + Email | Real-time |
| Weekly Report | Email | End of week |

### I.3 — Alert Format

```
🔔 TRADING ALERT
Type: TRADE EXECUTED
Time: 2026-08-31 14:30 UTC

Direction: LONG
Entry: 1848.50
Lots: 0.42
SL: 1842.50
TP₁: 1858.50

Account: $10,245.30
Daily P&L: +$125.20 (1.25%)
Drawdown: 1.8%

Status: NORMAL ✅
```

---

## J — MANUAL INTERVENTION

### J.1 — When Manual Intervention Required

| Situation | Action Required |
|-----------|----------------|
| Kill switch triggered | Operator must verify system health |
| Emergency stop | Operator must confirm resolution |
| Connection failure > 10 min | Operator must check infrastructure |
| Abnormal spread > 30 min | Operator must check broker |
| 5+ consecutive losses | Operator must review system |
| Performance degradation | Operator must decide: continue or halt |

### J.2 — Operator Commands

| Command | Description |
|---------|-------------|
| `RESUME` | Resume trading after halt |
| `HALT` | Immediately halt all trading |
| `CLOSE_ALL` | Close all positions |
| `STATUS` | Get current system status |
| `REPORT` | Get performance report |

---

## K — EDGE CASES

### K.1 — Market Events

| Scenario | Handling |
|----------|----------|
| Flash crash | Emergency stop triggers |
| Weekend gap | SL/TP execute at market open |
| Holiday | No trading |
| News event during live | No-Trade engine blocks |

### K.2 — System Events

| Scenario | Handling |
|----------|----------|
| Broker maintenance | Halt trading; resume after |
| VPS restart | Reconnect; verify positions |
| Software update | Halt; update; resume |
| Power failure | SL/TP on broker server protect |

---

## L — WHAT IS FIXED

### L.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Start Position Size | 25% | Very conservative |
| Start Risk per Trade | 0.25% | Minimal risk |
| Start Max Positions | 2 | Limited exposure |
| Start Max DD | 10% | Tight protection |
| Scaling Duration | 4 weeks per phase | Gradual |
| Emergency Close | All positions | Maximum safety |
| Connection Timeout | 5 minutes | Before closing |
| Spread Threshold | 5.0 pips | Abnormal detection |

### L.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal starting size | From live performance |
| Optimal scaling pace | From live performance |
| Broker-specific adjustments | From live experience |
| VPS optimization | From latency measurements |

---

## M — WHAT REQUIRES TESTING

### M.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | Phase 1 parameters ensure survival | Live monitoring | No kill switch triggers in week 1 |
| H2 | Scaling criteria are appropriate | Track performance | Performance supports scaling |
| H3 | Emergency stops work reliably | Simulate emergency | All positions closed |
| H4 | Kill switches trigger correctly | Simulate limit breach | Trading halted |
| H5 | Connection protection works | Simulate disconnect | Positions protected |

### M.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Is 25% start size too conservative? | From live results |
| Q2 | Should we scale faster? | From performance |
| Q3 | Are kill switch thresholds appropriate? | From live experience |
| Q4 | How often should we review live performance? | Weekly minimum |

---

## N — OUTPUT SCHEMA

### N.1 — Live Trading State

```python
@dataclass(frozen=True)
class LiveTradingState:
    """Current live trading state."""
    
    # Status
    status: str                          # "active", "halted", "emergency"
    phase: int                           # 1, 2, or 3
    uptime_hours: float
    
    # Account
    equity: float
    balance: float
    unrealized_pnl: float
    
    # Risk
    daily_pnl: float
    daily_pnl_pct: float
    weekly_pnl: float
    monthly_pnl: float
    drawdown: float
    drawdown_pct: float
    
    # Positions
    open_positions: int
    max_positions: int
    
    # Kill Switches
    daily_kill_status: str               # "normal", "warning", "killed"
    dd_kill_status: str
    connection_status: str
    spread_status: str
    
    # Execution
    trades_today: int
    win_rate_today: float
    avg_slippage: float
    avg_latency: float
    
    # Alerts
    active_alerts: list[str]
```

---

## O — DECISION OUTPUT

### O.1 — Live Trading Status

```
╔══════════════════════════════════════════════════════════════╗
║                 LIVE TRADING STATUS                          ║
╠══════════════════════════════════════════════════════════════╣
║ Status: ACTIVE ✅ | Phase: 1 (Conservative)                 ║
║ Started: 2026-09-01 | Uptime: 99.8%                        ║
║                                                              ║
║ PERFORMANCE (Week 1)                                         ║
║ Trades: 8 | Win Rate: 62.5% | P&L: +$185.30               ║
║ Sharpe: 1.85 | Max DD: 2.1%                                ║
║                                                              ║
║ SCALING ASSESSMENT                                           ║
║ Required for Phase 2:                                       ║
║   Sharpe > 1.0: ✅ (1.85)                                  ║
║   Max DD < 8%: ✅ (2.1%)                                   ║
║   Win Rate > 50%: ✅ (62.5%)                               ║
║   Duration ≥ 4 weeks: ⏳ (1/4 weeks)                       ║
║                                                              ║
║ Recommendation: CONTINUE PHASE 1                            ║
║ Next Review: 2026-09-29 (Week 4)                            ║
╚══════════════════════════════════════════════════════════════╝
```

---

## P — APPROVAL GATE

### The Phase 20 — Live Trading specification is now complete.

**Summary of what is defined:**

1. ✅ Pre-live checklist (10 requirements)
2. ✅ 3-phase scaling plan (Conservative → Full Size)
3. ✅ Scaling criteria (performance-based)
4. ✅ Scale-down criteria (risk-based)
5. ✅ Hard risk limits (per-trade, daily, weekly, monthly)
6. ✅ Emergency stop (7 conditions)
7. ✅ Kill switches (Daily, Drawdown)
8. ✅ Connection failure protection
9. ✅ Abnormal spread protection
10. ✅ Monitoring dashboard
11. ✅ Alert system
12. ✅ Manual intervention protocols
13. ✅ Edge cases and handling

---

### 📋 Points Requiring Your Approval:

1. **Start Position Size (25%):** Conservative enough?

2. **Start Risk per Trade (0.25%):** Minimal risk?

3. **3-Phase Scaling:** 4 weeks per phase — appropriate?

4. **Scale-Up Criteria:** Sharpe > 1.0, DD < 8%, WR > 50%?

5. **Kill Switch Thresholds:** 3%/4%/6% daily by phase?

6. **Connection Timeout (5 min):** Before closing positions?

7. **Spread Threshold (5.0 pips):** Abnormal detection?

8. **Emergency Close All:** Maximum safety approach?

---

**Please review and approve (or request modifications) before I proceed to Phase 21 — Feedback/Research.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
