# PHASE 13 — TRADE MANAGEMENT

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the **Trade Management** framework — controlling how open positions are managed through partial closes, break-even stops, trailing stops, and emergency exits.

This engine produces:
1. Multi-level TP targets (TP₁, TP₂, TP₃)
2. Partial close rules
3. Break-even logic
4. Fixed trailing stop
5. Structure-based trailing stop
6. Emergency exit conditions
7. Position monitoring and alerts

**Scope Boundary:**
- This engine manages **open positions only**.
- Entry and initial SL/TP are handled by Phase 11–12.
- This engine **modifies** SL/TP after entry based on price action.

---

## B — INPUTS

### B.1 — Required Data

| Data | Source | Phase |
|------|--------|-------|
| Open Positions | MT5 | Phase 1 |
| Current Price (Bid/Ask) | MT5 | Phase 1 |
| ATR | Phase 5 | 5 |
| Structure Levels | Phase 2 | 2 |
| Liquidity Levels | Phase 3 | 3 |
| Regime | Phase 9 | 9 |
| Risk Output | Phase 12 | 12 |

### B.2 — Parameters

| Parameter | Initial Value | Description |
|-----------|--------------|-------------|
| `TP1_RATIO` | 0.50 | % of position to close at TP₁ |
| `TP2_RATIO` | 0.30 | % of position to close at TP₂ |
| `TP3_RATIO` | 0.20 | % remaining (trailing target) |
| `BE_TRIGGER_ATR` | 1.0 | ATR move to trigger break-even |
| `BE_BUFFER_ATR` | 0.05 | ATR buffer above/below entry for BE |
| `TRAIL_FIXED_ATR` | 1.0 | Fixed trailing distance |
| `TRAIL_STEP_ATR` | 0.25 | Minimum step for trailing update |
| `STRUCT_TRAIL_LOOKBACK` | 5 | Bars for structure trailing |
| `EMERGENCY_DROP_ATR` | 3.0 | ATR move against position for emergency exit |
| `EMERGENCY_TIME_BARS` | 3 | Bars for rapid adverse move |

---

## C — TAKE PROFIT LEVELS

### C.1 — TP Target Calculation

For a LONG position:

$$\text{TP}_1 = \text{Entry} + \text{ATR}_{14} \times \text{TP1\_multiplier}$$

$$\text{TP}_2 = \text{Entry} + \text{ATR}_{14} \times \text{TP2\_multiplier}$$

$$\text{TP}_3 = \text{Entry} + \text{ATR}_{14} \times \text{TP3\_multiplier}$$

Where:
- $\text{TP1\_multiplier} = 1.0$ (initial)
- $\text{TP2\_multiplier} = 2.0$ (initial)
- $\text{TP3\_multiplier} = 3.0$ (initial)

For a SHORT position:

$$\text{TP}_1 = \text{Entry} - \text{ATR}_{14} \times \text{TP1\_multiplier}$$

$$\text{TP}_2 = \text{Entry} - \text{ATR}_{14} \times \text{TP2\_multiplier}$$

$$\text{TP}_3 = \text{Entry} - \text{ATR}_{14} \times \text{TP3\_multiplier}$$

### C.2 — Liquidity-Adjusted TP

If a liquidity level exists within the TP range:

$$\text{TP}_i = \text{NearestLiquidityLevel}(\text{direction})$$

**Priority:** Liquidity-based TP overrides ATR-based TP when a significant level is nearby.

### C.3 — Historical TP

From Phase 8, historical outcomes provide target estimates:

$$\text{TP}_{\text{historical}} = \text{Entry} + \text{ATR} \times \text{HistoricalTargetATR}$$

**Usage:** Historical target is used as a reference, not a hard rule.

### C.4 — TP Priority Order

| Priority | Method | When |
|----------|--------|------|
| 1 | Liquidity level | Significant level within range |
| 2 | Historical target | From Phase 8 |
| 3 | ATR-based | Default |

### C.5 — TP Rejection

If calculated TP violates constraints:

$$\text{TP}_{\text{min}} = \text{Entry} + 0.50 \text{ pips}$$

$$\text{TP}_{\text{max}} = \text{Entry} + 10.0 \times \text{ATR}_{14}$$

---

## D — PARTIAL CLOSE RULES

### D.1 — Position Split

At entry, the position is conceptually split:

$$\text{Position} = \text{TP}_1 \text{ portion} + \text{TP}_2 \text{ portion} + \text{TP}_3 \text{ portion}$$

| Level | % of Position | Action |
|-------|-------------|--------|
| TP₁ | 50% | Close 50% of position |
| TP₂ | 30% | Close 30% of remaining |
| TP₃ | 20% | Close final 20% (or trail) |

### D.2 — Partial Close Execution

**At TP₁:**

$$\text{Lots}_{\text{close}} = \text{Lots}_{\text{total}} \times \text{TP1\_RATIO} = \text{Lots} \times 0.50$$

**Remaining after TP₁:**

$$\text{Lots}_{\text{remaining}} = \text{Lots} \times (1 - 0.50) = \text{Lots} \times 0.50$$

**At TP₂:**

$$\text{Lots}_{\text{close}} = \text{Lots}_{\text{remaining}} \times \text{TP2\_RATIO} = \text{Lots} \times 0.50 \times 0.30 = \text{Lots} \times 0.15$$

**Remaining after TP₂:**

$$\text{Lots}_{\text{remaining}} = \text{Lots} \times 0.35$$

**At TP₃:**

$$\text{Lots}_{\text{close}} = \text{Lots}_{\text{remaining}} = \text{Lots} \times 0.35$$

### D.3 — Partial Close Summary

| Event | Close | Remaining | Cumulative Closed |
|-------|-------|-----------|-------------------|
| Entry | 0% | 100% | 0% |
| TP₁ hit | 50% | 50% | 50% |
| TP₂ hit | 15% | 35% | 65% |
| TP₃ hit | 35% | 0% | 100% |

### D.4 — Partial Close Logging

Every partial close is logged with:
- Timestamp
- Price at close
- Lots closed
- Lots remaining
- Realized P&L for closed portion
- Unrealized P&L for remaining

---

## E — BREAK-EVEN LOGIC

### E.1 — Break-Even Trigger

$$\text{BE\_Triggered}_{\text{long}} \iff \text{Price} - \text{Entry} \geq \text{BE\_TRIGGER\_ATR} \times \text{ATR}_{14}$$

$$\text{BE\_Triggered}_{\text{short}} \iff \text{Entry} - \text{Price} \geq \text{BE\_TRIGGER\_ATR} \times \text{ATR}_{14}$$

Where $\text{BE\_TRIGGER\_ATR} = 1.0$.

### E.2 — Break-Even SL Placement

$$\text{SL}_{\text{BE}} = \text{Entry} + \text{BE\_BUFFER\_ATR} \times \text{ATR}_{14} \quad \text{(Long)}$$

$$\text{SL}_{\text{BE}} = \text{Entry} - \text{BE\_BUFFER\_ATR} \times \text{ATR}_{14} \quad \text{(Short)}$$

Where $\text{BE\_BUFFER\_ATR} = 0.05$.

**Interpretation:** SL moves to entry + small buffer (covers spread/commission).

### E.3 — Break-Even Rules

| Rule | Description |
|------|-------------|
| BE1 | Once triggered, SL is moved to break-even + buffer |
| BE2 | BE is a **one-way** operation — SL never moves back |
| BE3 | BE applies to the **remaining** position after partial closes |
| BE4 | BE is skipped if regime is High Volatility (SL stays wider) |

### E.4 — Break-Even Timing

$$\text{BE\_Time} = \min\{t : \text{BE\_Triggered}(t) = \text{True}\}$$

BE is applied at the **first bar** where the trigger condition is met.

---

## F — TRAILING STOP

### F.1 — Fixed Trailing Stop

$$\text{SL}_{\text{trail}} = \text{Price} - \text{TRAIL\_FIXED\_ATR} \times \text{ATR}_{14} \quad \text{(Long)}$$

$$\text{SL}_{\text{trail}} = \text{Price} + \text{TRAIL\_FIXED\_ATR} \times \text{ATR}_{14} \quad \text{(Short)}$$

Where $\text{TRAIL\_FIXED\_ATR} = 1.0$.

### F.2 — Trailing Step

To prevent constant SL updates:

$$\text{SL}_{\text{updated}} \iff |\text{NewSL} - \text{CurrentSL}| \geq \text{TRAIL\_STEP\_ATR} \times \text{ATR}_{14}$$

Where $\text{TRAIL\_STEP\_ATR} = 0.25$.

**Interpretation:** SL only moves when the improvement exceeds 0.25 ATR.

### F.3 — Trailing Rules

| Rule | Description |
|------|-------------|
| T1 | Trailing activates after BE is triggered |
| T2 | SL only moves **in favor** (closer to profit) |
| T3 | SL never moves against the position |
| T4 | Trailing uses current ATR (dynamic) |
| T5 | Trailing is checked every bar |

### F.4 — Trailing Activation Sequence

```
Entry → BE Triggered → Trailing Activated → TP₁ → TP₂ → TP₃
```

Trailing is **not** active before BE is triggered.

---

## G — STRUCTURE-BASED TRAILING

### G.1 — Definition

Structure trailing uses **swing points** from Phase 2 to set trailing SL:

$$\text{SL}_{\text{struct}} = \text{LastSwingLow} - \text{Buffer} \quad \text{(Long)}$$

$$\text{SL}_{\text{struct}} = \text{LastSwingHigh} + \text{Buffer} \quad \text{(Short)}$$

Where $\text{Buffer} = 0.05 \times \text{ATR}_{14}$.

### G.2 — Structure Trailing Rules

| Rule | Description |
|------|-------------|
| ST1 | SL follows the most recent confirmed swing |
| ST2 | SL only moves **in favor** |
| ST3 | If no new swing formed, SL stays at last position |
| ST4 | Structure trailing overrides fixed trailing when structure is clear |
| ST5 | Structure trailing is checked every bar |

### G.3 — Structure vs. Fixed Trailing

| Aspect | Fixed Trailing | Structure Trailing |
|--------|---------------|-------------------|
| Basis | ATR distance | Swing points |
| Adaptiveness | Volatility-based | Structure-based |
| Tightness | Constant distance | Variable (depends on swing spacing) |
| Best for | Trending markets | Markets with clear structure |

### G.4 — Selection Logic

$$\text{TrailingMethod} = \begin{cases}
\text{Structure} & \text{if } |\text{LastSwingHigh} - \text{LastSwingLow}| > 0.5 \times \text{ATR} \\
\text{Fixed} & \text{otherwise}
\end{cases}$$

**Interpretation:** Use structure trailing when swings are well-defined; fall back to fixed trailing when structure is unclear.

---

## H — EMERGENCY EXIT

### H.1 — Emergency Exit Conditions

| Condition | Trigger | Action |
|-----------|---------|--------|
| Rapid Adverse Move | Price moves against position by > 3.0 ATR within 3 bars | Close immediately |
| Spread Spike | Spread > 5.0 pips | Close if in loss |
| Connection Lost | MT5 connection lost for > 30 seconds | Close at market |
| Regime Emergency | Regime changes to "Emergency" | Close all positions |
| Drawdown Limit | Total drawdown > 20% | Close all positions |
| Daily Loss Limit | Daily loss > 5% | Close all positions |

### H.2 — Rapid Adverse Move Detection

$$\text{Emergency}_{\text{rapid}} \iff \sum_{i=0}^{2} |\Delta \text{Price}_{t-i}| > \text{EMERGENCY\_DROP\_ATR} \times \text{ATR}_{14}$$

$$\wedge \quad \text{sign}(\Delta \text{Price}) \neq \text{PositionDirection}$$

Where $\text{EMERGENCY\_DROP\_ATR} = 3.0$ and the sum is over 3 bars.

**Interpretation:** If price moves 3 ATR against the position within 3 bars, exit immediately.

### H.3 — Emergency Exit Priority

| Priority | Condition | Speed |
|----------|-----------|-------|
| 1 | Drawdown > 20% | Immediate |
| 2 | Daily loss > 5% | Immediate |
| 3 | Rapid adverse move | Immediate |
| 4 | Connection lost | Best effort |
| 5 | Spread spike | If in loss |

### H.4 — Emergency Exit Logging

Every emergency exit is logged with:
- Timestamp
- Trigger condition
- Price at exit
- P&L at exit
- Position details
- Market context (regime, GSI, etc.)

---

## I — POSITION MONITORING

### I.1 — Monitoring Frequency

| Check | Frequency |
|-------|-----------|
| Price monitoring | Every tick (real-time) / Every bar (backtest) |
| SL/TP check | Every bar |
| BE trigger | Every bar |
| Trailing update | Every bar |
| Emergency conditions | Every bar |
| Partial close | On price touch |

### I.2 — Monitoring Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| Approaching TP | Price within 0.5 ATR of TP | Log |
| Approaching SL | Price within 0.5 ATR of SL | Log |
| BE Triggered | BE condition met | Move SL |
| Partial Close | TP hit | Execute close |
| Trailing Update | New SL computed | Update SL |
| Emergency | Emergency condition met | Close position |

### I.3 — Position State Tracking

Each open position maintains:

| Field | Description |
|-------|-------------|
| Entry Price | Original entry |
| Current SL | Active stop loss |
| Current TP₁/TP₂/TP₃ | Active take profit levels |
| Lots Open | Remaining position size |
| Lots Closed | Partially closed amount |
| BE Triggered | Boolean |
| Trailing Active | Boolean |
| Trailing Method | "fixed" or "structure" |
| Unrealized P&L | Current P&L |
| Duration | Bars since entry |
| Max Favorable Excursion | Best P&L reached |
| Max Adverse Excursion | Worst P&L reached |

---

## J — EDGE CASES

### J.1 — Slippage on Partial Close

| Scenario | Handling |
|----------|----------|
| Partial close at TP₁ with slippage | Execute at available price; log slippage |
| Multiple partial closes in same bar | Execute in order (TP₁ first, then TP₂, then TP₃) |

### J.2 — Gap Events

| Scenario | Handling |
|----------|----------|
| Gap through TP₁ | Close at TP₁ level (or next available price) |
| Gap through SL | Close at SL level (or next available price) |
| Gap through both | Close at SL (conservative) |

### J.3 — Regime Changes During Trade

| Scenario | Handling |
|----------|----------|
| Regime changes to News | Tighten trailing; prepare for volatility |
| Regime changes to High Vol | Widen trailing; reduce position if possible |
| Regime changes to Range | Tighten TP targets |

---

## K — BIAS PREVENTION

### K.1 — Look-Ahead Bias

**Prevention:**
1. All trailing decisions based on confirmed bar data
2. No future knowledge of price action
3. BE/trailing triggered at bar close, not intra-bar

### K.2 — Overfitting

**Prevention:**
1. Trade management parameters are initial; optimization in Phase 17
2. Walk-forward validation
3. Conservative defaults (1 ATR trailing, 1 ATR BE trigger)

---

## L — BACKTESTABILITY

### L.1 — Backtest Requirements

| Requirement | Implementation |
|-------------|---------------|
| Partial close | Simulate at exact TP price (or next bar open) |
| BE trigger | Check every bar |
| Trailing update | Check every bar |
| Emergency exit | Check every bar |
| Slippage model | Add configurable slippage |

### L.2 — Backtest Data Flow

```
For each open position:
    ├── Check Emergency Conditions → Close if triggered
    ├── Check Partial Close (TP₁/TP₂/TP₃) → Execute if hit
    ├── Check BE Trigger → Move SL if triggered
    ├── Check Trailing → Update SL if improved
    ├── Check Structure Trailing → Update SL if structure-based
    └── Log position state
```

---

## M — WHAT IS FIXED

### M.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| TP₁ | 50% of position | Lock in profits |
| TP₂ | 30% of remaining | Capture more gains |
| TP₃ | 20% (final) | Let profits run |
| BE Trigger | 1.0 ATR | Move to break-even after 1 ATR profit |
| BE Buffer | 0.05 ATR | Cover spread/commission |
| Fixed Trailing | 1.0 ATR | Standard trailing distance |
| Trailing Step | 0.25 ATR | Prevent constant updates |
| Emergency Drop | 3.0 ATR in 3 bars | Rapid adverse move |
| Structure Trailing Lookback | 5 bars | For swing detection |

### M.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal TP levels | Phase 17 (Optimization) |
| Optimal partial close ratios | Phase 17 |
| BE trigger threshold | Phase 17 |
| Trailing distance | Phase 17 |
| Emergency thresholds | Phase 17 |

---

## N — WHAT REQUIRES TESTING

### N.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | Partial close (50/30/20) outperforms full close at TP₁ | Backtest both | Partial close has better risk-adjusted returns |
| H2 | BE trigger at 1.0 ATR is optimal | Test range [0.5–2.0] | Optimal in [0.75–1.25] |
| H3 | Structure trailing outperforms fixed trailing | Backtest both | Structure trailing has higher Sharpe |
| H4 | Emergency exit at 3.0 ATR prevents large losses | Backtest | Emergency exits reduce max loss |
| H5 | Liquidity-based TP outperforms ATR-based TP | Backtest both | Liquidity TP has higher win rate |

### N.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Should partial close ratios be regime-dependent? | Test per-regime ratios |
| Q2 | Should structure trailing be the default? | Test both as default |
| Q3 | How to handle emergency exit during news? | Test news-specific rules |
| Q4 | Should we add a time-based exit? | Test max hold period |

---

## O — OUTPUT SCHEMA

### O.1 — Trade Management Output per Bar

```python
@dataclass(frozen=True)
class TradeManagementOutput:
    """Trade Management output for an open position."""
    position_id: str
    timestamp: datetime
    
    # Position State
    direction: str                       # "long" or "short"
    entry_price: float
    lots_open: float
    lots_closed: float
    current_sl: float
    current_tp1: float
    current_tp2: float
    current_tp3: float
    
    # P&L
    unrealized_pnl: float
    realized_pnl: float
    max_favorable_excursion: float
    max_adverse_excursion: float
    
    # Status
    be_triggered: bool
    trailing_active: bool
    trailing_method: str                 # "fixed" or "structure"
    partial_closes_completed: int        # 0, 1, 2, or 3
    
    # Actions
    action_taken: str | None             # "partial_close", "be_move", "trail_update", "emergency_exit"
    action_details: str | None
    
    # Duration
    bars_held: int
    duration_minutes: int
    
    # Provenance
    provenance: DataProvenance
```

---

## P — DECISION OUTPUT

### P.1 — Per-Bar Trade Management

```
=== TRADE MANAGEMENT ===
Position: #1234 (LONG)
Entry: 1848.50 | Lots: 1.67
Current: 1856.20 (+7.70, +$128.59)

=== SL/TP STATUS ===
SL: 1842.50 (Structure) → 1848.55 (BE triggered @ 1849.50)
TP₁: 1858.50 (50%) — Pending
TP₂: 1868.50 (30%) — Pending
TP₃: 1878.50 (20%) — Pending

=== TRAILING ===
Method: Structure
Last Swing Low: 1852.30
Trailing SL: 1852.25 (1852.30 - 0.05 ATR)
Status: Active, waiting for structure update

=== PARTIAL CLOSE ===
TP₁: Not yet hit (need 1858.50)
TP₂: Not yet hit (need 1868.50)
TP₃: Not yet hit (need 1878.50)

=== EMERGENCY CHECK ✅
Rapid Adverse: No
Spread: 0.8 pips (normal)
Connection: OK

Duration: 14 bars (70 minutes)
```

### P.2 — Partial Close Event

```
[14:45] PARTIAL CLOSE EXECUTED
  Position: #1234 (LONG)
  Trigger: TP₁ @ 1858.50
  Lots Closed: 0.84 (50%)
  Lots Remaining: 0.83
  Realized P&L: +$84.00
  SL Updated: 1848.55 (Break-Even + Buffer)
```

---

## Q — APPROVAL GATE

### The Phase 13 — Trade Management specification is now complete.

**Summary of what is defined:**

1. ✅ Multi-level TP (TP₁, TP₂, TP₃) with partial close ratios
2. ✅ Liquidity-based and Historical TP priority
3. ✅ Break-even logic with trigger and buffer
4. ✅ Fixed trailing stop with step
5. ✅ Structure-based trailing stop
6. ✅ Emergency exit conditions (6 triggers)
7. ✅ Position monitoring and state tracking
8. ✅ Edge cases and handling
9. ✅ Bias prevention measures
10. ✅ Backtest requirements
11. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **Partial Close Ratios (50/30/20):** Appropriate split?

2. **BE Trigger (1.0 ATR):** Move to break-even after 1 ATR profit — appropriate?

3. **BE Buffer (0.05 ATR):** Enough to cover spread/commission?

4. **Fixed Trailing (1.0 ATR):** Standard trailing distance?

5. **Trailing Step (0.25 ATR):** Prevents constant updates — appropriate?

6. **Structure Trailing:** Use when swings are well-defined — correct approach?

7. **Emergency Drop (3.0 ATR in 3 bars):** Appropriate threshold?

8. **TP Priority:** Liquidity > Historical > ATR — correct order?

---

**Please review and approve (or request modifications) before I proceed to Phase 14 — No-Trade Engine.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
