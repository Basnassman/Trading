# PHASE 12 — RISK ENGINE

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the **Risk Management** framework — controlling position sizing, exposure limits, drawdown protection, and stop loss placement to ensure capital preservation.

This engine produces:
1. Position size calculation
2. Stop Loss placement (structure-based, not fixed)
3. Take Profit placement
4. Risk per trade limits
5. Daily/Weekly/Monthly loss limits
6. Maximum exposure controls
7. Drawdown protection
8. Circuit breakers

**Critical Rule:** SL is **never** a fixed number. It is always based on market structure, liquidity, ATR, or volatility.

---

## B — INPUTS

### B.1 — Required Data

| Data | Source | Phase |
|------|--------|-------|
| Account Balance | MT5 | Phase 1 |
| Equity | MT5 | Phase 1 |
| Open Positions | MT5 | Phase 1 |
| ATR | Phase 5 | 5 |
| Structure Levels | Phase 2 | 2 |
| Liquidity Levels | Phase 3 | 3 |
| Volatility Regime | Phase 9 | 9 |
| Setup Output | Phase 11 | 11 |

### B.2 — Parameters

| Parameter | Initial Value | Description |
|-----------|--------------|-------------|
| `RISK_PER_TRADE` | 0.01 (1%) | Max risk per trade as fraction of equity |
| `MAX_DAILY_LOSS` | 0.05 (5%) | Max daily loss as fraction of equity |
| `MAX_WEEKLY_LOSS` | 0.10 (10%) | Max weekly loss |
| `MAX_MONTHLY_LOSS` | 0.15 (15%) | Max monthly loss |
| `MAX_DRAWDOWN` | 0.20 (20%) | Max drawdown from peak equity |
| `MAX_POSITIONS` | 5 | Maximum simultaneous open positions |
| `MAX_EXPOSURE` | 0.50 (50%) | Max total notional as fraction of equity |
| `MAX_SINGLE_DIRECTION` | 0.30 (30%) | Max net exposure in one direction |
| `MIN_LOT_SIZE` | 0.01 | Minimum position size |
| `MAX_LOT_SIZE` | 5.0 | Maximum position size |
| `CONTRACT_SIZE` | 100 | Oz per lot (standard) |
| `SL_BUFFER_ATR` | 0.05 | ATR buffer beyond SL level |

---

## C — POSITION SIZE CALCULATION

### C.1 — Core Formula

$$\text{PositionSize} = \frac{\text{RiskAmount}}{\text{StopDistance} \times \text{PointValue}}$$

Where:
- $\text{RiskAmount} = \text{Equity} \times \text{RISK\_PER\_TRADE}$
- $\text{StopDistance} = |Entry - SL|$ in price units
- $\text{PointValue} = \text{ContractSize} \times \text{Point}$

### C.2 — Risk Amount

$$\text{RiskAmount} = \text{Equity}_t \times \text{RISK\_PER\_TRADE}$$

**Equity** (not Balance) is used because it accounts for unrealized P&L.

### C.3 — Stop Distance

$$\text{StopDistance} = |Entry - SL|$$

Where SL is determined by the SL Engine (Section D).

### C.4 — Position Size in Lots

$$\text{Lots} = \frac{\text{RiskAmount}}{\text{StopDistance} \times \text{ContractSize} \times \text{Point}}$$

**Constraints:**

$$\text{Lots} = \max(\text{MIN\_LOT\_SIZE}, \min(\text{MAX\_LOT\_SIZE}, \text{Lots}))$$

$$\text{Lots} = \text{round}(\text{Lots}, 2) \quad \text{(round to 0.01)}$$

### C.5 — Example

```
Equity: $10,000
Risk per trade: 1% → RiskAmount = $100
Entry: 1850.00
SL: 1842.50 (from Structure)
StopDistance: 7.50
ContractSize: 100

Lots = $100 / (7.50 × 100 × 0.01)
     = $100 / 7.50
     = 13.33 → capped at MAX_LOT_SIZE
```

Wait — XAUUSD point = 0.01, so:

$$\text{Lots} = \frac{100}{7.50 \times 100 \times 0.01} = \frac{100}{7.50} = 13.33$$

This seems high. Let me reconsider:

For XAUUSD:
- 1 lot = 100 oz
- 1 pip (0.01) = $0.01 × 100 = $1.00 per lot
- StopDistance = 7.50 = 750 pips
- Risk per lot = 750 × $1.00 = $750

$$\text{Lots} = \frac{100}{750} = 0.13 \text{ lots}$$

**Corrected Formula:**

$$\text{Lots} = \frac{\text{RiskAmount}}{\text{StopDistance} \times \text{PipValue}}$$

Where $\text{PipValue} = \text{ContractSize} \times \text{Point} = 100 \times 0.01 = 1.00$ per pip.

### C.6 — Regime-Adjusted Position Size

$$\text{Lots}_{\text{final}} = \text{Lots} \times \text{SizeFactor}_{\text{Regime}}$$

From Phase 9:

| Regime | Size Factor |
|--------|------------|
| Normal Trend | 1.00 |
| Range | 0.70 |
| Breakout | 1.00 |
| High Volatility | 0.50 |
| Liquidity Sweep | 0.60 |
| Post-News | 0.40 |
| Low Liquidity | 0.50 |
| Transition | 0.60 |

---

## D — STOP LOSS PLACEMENT

### D.1 — Core Principle

**SL is never a fixed number.** It is always based on market structure.

### D.2 — SL Methods (Priority Order)

| Priority | Method | When to Use | Formula |
|----------|--------|-------------|---------|
| 1 | Structure-based | BOS/CHoCH entry | Below last swing low (long) / Above last swing high (short) |
| 2 | Liquidity-based | Sweep entry | Beyond swept level + buffer |
| 3 | ATR-based | When structure unclear | Entry ∓ ATR × multiplier |
| 4 | Volatility-based | High vol regime | Entry ∓ ATR × regime-adjusted multiplier |

### D.3 — Structure-Based SL

$$\text{SL}_{\text{long}} = \min(\text{LastSwingLow}, \text{NearestSupport}) - \text{Buffer}$$

$$\text{SL}_{\text{short}} = \max(\text{LastSwingHigh}, \text{NearestResistance}) + \text{Buffer}$$

Where $\text{Buffer} = 0.05 \times \text{ATR}_{14}$.

**Rationale:** SL is placed just beyond the structural level that would invalidate the setup.

### D.4 — Liquidity-Based SL

$$\text{SL}_{\text{long}} = \text{SweptLevel} - \text{Buffer}$$

$$\text{SL}_{\text{short}} = \text{SweptLevel} + \text{Buffer}$$

Where $\text{Buffer} = 0.05 \times \text{ATR}_{14}$.

**Rationale:** After a sweep, the swept level becomes the reference for SL.

### D.5 — ATR-Based SL

$$\text{SL}_{\text{long}} = \text{Entry} - \text{ATR}_{14} \times \text{ATR\_multiplier}$$

$$\text{SL}_{\text{short}} = \text{Entry} + \text{ATR}_{14} \times \text{ATR\_multiplier}$$

Where $\text{ATR\_multiplier} = 1.0$ (initial).

**When used:** When structure/liquidity levels are unclear or too far away.

### D.6 — Volatility-Adjusted SL

$$\text{SL}_{\text{long}} = \text{Entry} - \text{ATR}_{14} \times \text{ATR\_multiplier}_{\text{Regime}}$$

| Regime | ATR Multiplier |
|--------|---------------|
| Normal Trend | 1.0 |
| Range | 0.7 |
| Breakout | 1.5 |
| High Volatility | 1.5 |
| Post-News | 1.3 |
| Low Liquidity | 1.0 |

### D.7 — SL Constraints

$$\text{SL}_{\text{min\_distance}} = 0.50 \text{ pips (0.50 for XAUUSD)}$$

$$\text{SL}_{\text{max\_distance}} = 5.0 \times \text{ATR}_{14}$$

If calculated SL violates constraints:
- Too close → Use minimum distance
- Too far → Use maximum distance; flag `wide_sl_warning`

### D.8 — SL Cannot Be Moved Further

Once SL is set at entry:
- SL can only be moved **closer** to price (trailing)
- SL can **never** be moved further from price
- This prevents "moving the goalposts"

---

## E — TAKE PROFIT PLACEMENT

### E.1 — TP Methods

| Priority | Method | Formula |
|----------|--------|---------|
| 1 | Liquidity-based | TP at nearest liquidity level |
| 2 | ATR-based | Entry + ATR × multiplier |
| 3 | Structure-based | TP at next structural level |
| 4 | Historical target | From Phase 8 historical outcomes |

### E.2 — Liquidity-Based TP

$$\text{TP}_{\text{long}} = \text{NearestResistance}$$

$$\text{TP}_{\text{short}} = \text{NearestSupport}$$

**Rationale:** TP at the next significant level where orders may be concentrated.

### E.3 — ATR-Based TP

$$\text{TP}_{\text{long}} = \text{Entry} + \text{ATR}_{14} \times \text{TP\_multiplier}$$

$$\text{TP}_{\text{short}} = \text{Entry} - \text{ATR}_{14} \times \text{TP\_multiplier}$$

Where $\text{TP\_multiplier} = 2.0$ (initial).

### E.4 — Multiple TP Levels

| Level | % of Position | Target | Formula |
|-------|-------------|--------|---------|
| TP₁ | 50% | Conservative | Entry + 1.0 ATR |
| TP₂ | 30% | Moderate | Entry + 2.0 ATR |
| TP₃ | 20% | Extended / Trail | Entry + 3.0 ATR or trail |

### E.5 — Risk:Reward Validation

$$\text{RR} = \frac{\text{TP} - \text{Entry}}{\text{Entry} - \text{SL}} \geq \text{MIN\_RR} = 1.5$$

If RR < 1.5: **Setup is rejected** (from Phase 11).

---

## F — RISK LIMITS

### F.1 — Per-Trade Risk

$$\text{RiskPerTrade} = \text{Equity} \times \text{RISK\_PER\_TRADE}$$

$$\text{RISK\_PER\_TRADE} = 0.01 \quad (1\%)$$

### F.2 — Daily Loss Limit

$$\text{DailyLoss}_{\text{limit}} = \text{Equity}_{\text{start\_of\_day}} \times \text{MAX\_DAILY\_LOSS}$$

$$\text{MAX\_DAILY\_LOSS} = 0.05 \quad (5\%)$$

**Cascading Alerts:**

| Level | Threshold | Action |
|-------|-----------|--------|
| Level 1 (Yellow) | 2% daily loss | Alert; reduce position size by 50% |
| Level 2 (Orange) | 3% daily loss | Alert; reduce position size by 75% |
| Level 3 (Red) | 4% daily loss | Alert; no new trades |
| Level 4 (Kill) | 5% daily loss | **Halt all trading** |
| Hard Stop | 6% daily loss | **Force close all positions** |

### F.3 — Weekly Loss Limit

$$\text{WeeklyLoss}_{\text{limit}} = \text{Equity}_{\text{start\_of\_week}} \times \text{MAX\_WEEKLY\_LOSS}$$

$$\text{MAX\_WEEKLY\_LOSS} = 0.10 \quad (10\%)$$

### F.4 — Monthly Loss Limit

$$\text{MonthlyLoss}_{\text{limit}} = \text{Equity}_{\text{start\_of\_month}} \times \text{MAX\_MONTHLY\_LOSS}$$

$$\text{MAX\_MONTHLY\_LOSS} = 0.15 \quad (15\%)$$

### F.5 — Maximum Drawdown

$$\text{Drawdown}_t = \frac{\text{PeakEquity} - \text{Equity}_t}{\text{PeakEquity}}$$

$$\text{MAX\_DRAWDOWN} = 0.20 \quad (20\%)$$

**If Drawdown > MAX_DRAWDOWN:**
- **HALT ALL TRADING**
- Close all positions
- Require manual intervention to resume

### F.6 — Maximum Simultaneous Positions

$$\text{OpenPositions} \leq \text{MAX\_POSITIONS} = 5$$

### F.7 — Maximum Exposure

$$\text{TotalNotional} = \sum_{i=1}^{n} \text{Lots}_i \times \text{Price}_i \times \text{ContractSize}$$

$$\text{ExposureRatio} = \frac{\text{TotalNotional}}{\text{Equity}} \leq \text{MAX\_EXPOSURE} = 0.50$$

### F.8 — Maximum Single Direction

$$\text{NetDirectional} = \frac{|\text{LongNotional} - \text{ShortNotional}|}{\text{Equity}} \leq \text{MAX\_SINGLE\_DIRECTION} = 0.30$$

---

## G — CIRCUIT BREAKERS

### G.1 — Automatic Halt Conditions

| Condition | Action | Recovery |
|-----------|--------|----------|
| Daily loss > 5% | Halt trading | Next day |
| Weekly loss > 10% | Halt trading | Next week |
| Monthly loss > 15% | Halt trading | Manual review |
| Drawdown > 20% | Force close all | Manual review |
| Spread > 5.0 pips | Halt new entries | When spread normalizes |
| Connection lost | Halt trading | When reconnected |
| Abnormal price (> 5% move in 1 bar) | Halt + alert | Manual review |

### G.2 — Circuit Breaker States

```
NORMAL → WARNING → RESTRICTED → HALTED → (Manual Recovery) → NORMAL
```

| State | Description |
|-------|-------------|
| NORMAL | All limits within bounds |
| WARNING | Approaching a limit (80% of threshold) |
| RESTRICTED | Reduced position sizes, tighter filters |
| HALTED | No new trades; existing positions managed |

---

## H — EDGE CASES

### H.1 — Insufficient Margin

| Scenario | Handling |
|----------|----------|
| Not enough margin for calculated lot size | Reduce lots to fit available margin |
| Margin utilization > 80% | Alert; no new positions |
| Margin utilization > 90% | Force close weakest position |

### H.2 — Gap Events

| Scenario | Handling |
|----------|----------|
| Weekend gap through SL | SL executed at next available price (may be worse) |
| Holiday gap | Same as weekend gap |
| Flash crash | Circuit breaker triggers; halt trading |

### H.3 — Multiple Positions

| Scenario | Handling |
|----------|----------|
| Adding to winning position | Total risk still ≤ 1% per trade |
| Adding to losing position | **NOT allowed** — no averaging down |
| Correlated positions | Check total exposure, not per-trade |

---

## I — BIAS PREVENTION

### I.1 — Look-Ahead Bias

**Prevention:**
1. Position size computed at entry time only
2. SL/TP set at entry, not adjusted with future knowledge
3. Risk limits checked in real-time

### I.2 — Overfitting

**Prevention:**
1. Risk parameters are conservative (1% per trade, 5% daily)
2. Circuit breakers are hard limits, not adjustable
3. Walk-forward validation of risk model

---

## J — BACKTESTABILITY

### J.1 — Backtest Requirements

| Requirement | Implementation |
|-------------|---------------|
| Position sizing | Recomputed per trade |
| SL/TP | Set at entry, enforced per bar |
| Risk limits | Checked per bar |
| Circuit breakers | Enforced in backtest |
| Slippage | Modeled (see Phase 17) |

### J.2 — Realistic Backtest Assumptions

| Factor | Assumption |
|--------|-----------|
| Slippage | 0.5 pips per trade |
| Spread | Variable (use historical) |
| Commission | $7 per lot round-trip |
| Execution delay | 1 bar (next bar open) |
| Partial fills | Not modeled (assume full fill) |

---

## K — WHAT IS FIXED

### K.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Risk per trade | 1% | Conservative standard |
| Daily loss limit | 5% | Industry standard |
| Weekly loss limit | 10% | 2× daily |
| Monthly loss limit | 15% | 3× daily |
| Max drawdown | 20% | Hard stop |
| Max positions | 5 | Diversification |
| Max exposure | 50% | Margin safety |
| Max single direction | 30% | Directional limit |
| Min lot size | 0.01 | Minimum tradeable |
| Max lot size | 5.0 | Risk cap |
| SL buffer | 0.05 ATR | Above/below level |
| TP multiplier | 2.0 ATR | Default target |

### K.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal risk per trade | Phase 17 (Optimization) |
| SL/TP multiplier optimization | Phase 17 |
| Circuit breaker thresholds | Phase 17 |
| Slippage model | Phase 17 |
| Position correlation handling | Phase 17 |

---

## L — WHAT REQUIRES TESTING

### L.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | 1% risk per trade ensures survival | Monte Carlo simulation | > 99% survival over 1000 trades |
| H2 | 5% daily limit prevents catastrophic loss | Backtest | No single day > 5% loss |
| H3 | Structure-based SL outperforms fixed ATR SL | Backtest both | Structure SL has better Sharpe |
| H4 | Regime-adjusted sizing improves risk-adjusted returns | Backtest | Higher Sortino ratio |
| H5 | 20% max drawdown is appropriate | Historical analysis | Drawdown stays within bounds |

### L.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Should risk per trade be dynamic (based on confidence)? | Test Kelly Criterion |
| Q2 | How to handle correlated positions? | Test correlation-adjusted exposure |
| Q3 | Should circuit breakers be tighter? | Test [3%, 4%, 5%] daily limits |
| Q4 | Is 5 max positions optimal? | Test [3, 5, 7, 10] |

---

## M — OUTPUT SCHEMA

### M.1 — Risk Output per Trade

```python
@dataclass(frozen=True)
class RiskOutput:
    """Risk Engine output for a trade."""
    timestamp: datetime
    
    # Position Sizing
    equity: float
    risk_amount: float                   # Equity × RISK_PER_TRADE
    stop_distance: float                 # |Entry - SL|
    position_size: float                 # In lots
    position_size_regime_adjusted: float # After regime factor
    notional_value: float                # Lots × Price × ContractSize
    
    # SL/TP
    stop_loss: float
    take_profit: float
    tp1: float | None                    # Partial close level
    tp2: float | None
    tp3: float | None
    rr_ratio: float
    
    # Limits Check
    daily_loss_used: float               # % of daily limit used
    weekly_loss_used: float
    monthly_loss_used: float
    drawdown_current: float
    open_positions: int
    exposure_ratio: float
    directional_exposure: float
    
    # Circuit Breaker
    circuit_state: str                   # "normal", "warning", "restricted", "halted"
    halt_reason: str | None
    
    # Approval
    risk_approved: bool
    rejection_reason: str | None
    
    # Provenance
    provenance: DataProvenance
```

---

## N — DECISION OUTPUT

### N.1 — Per-Trade Risk Assessment

```
=== RISK ENGINE ===
Equity: $10,000.00
Risk per Trade: 1% = $100.00

=== STOP LOSS ===
Method: Structure-based
Level: 1842.50 (Last Swing Low - 0.05 ATR)
Entry: 1848.50
Stop Distance: 6.00 ($60.00 per lot)

=== POSITION SIZE ===
Lots: $100 / $60 = 1.67 → 1.67 lots
Regime Factor: 1.00 (Normal Trend)
Final Lots: 1.67

=== TAKE PROFIT ===
TP₁: 1854.50 (+6.00, RR 1:1.0) — 50% close
TP₂: 1860.50 (+12.00, RR 1:2.0) — 30% close
TP₃: 1866.50 (+18.00, RR 1:3.0) — 20% trail

=== RISK LIMITS ===
Daily Loss Used: 1.2% / 5.0% ✅
Weekly Loss Used: 3.5% / 10.0% ✅
Monthly Loss Used: 8.2% / 15.0% ✅
Drawdown: 2.1% / 20.0% ✅
Open Positions: 2 / 5 ✅
Exposure: 35% / 50% ✅

Circuit Breaker: NORMAL ✅
Risk Approved: YES ✅
```

---

## O — APPROVAL GATE

### The Phase 12 — Risk Engine specification is now complete.

**Summary of what is defined:**

1. ✅ Position size formula (RiskAmount / StopDistance)
2. ✅ SL placement (Structure > Liquidity > ATR > Volatility)
3. ✅ SL constraints (min/max distance, no moving further)
4. ✅ TP placement (Liquidity > ATR > Structure)
5. ✅ Multiple TP levels (TP₁/TP₂/TP₃)
6. ✅ Risk per trade (1%)
7. ✅ Daily/Weekly/Monthly loss limits
8. ✅ Maximum drawdown (20%)
9. ✅ Maximum positions (5)
10. ✅ Maximum exposure (50%)
11. ✅ Circuit breakers (4 states)
12. ✅ Edge cases and handling
13. ✅ Backtest requirements
14. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **Risk per Trade (1%):** Conservative enough? Too conservative?

2. **Daily Loss Limit (5%):** Appropriate?

3. **Max Drawdown (20%):** Hard stop at 20%?

4. **Max Positions (5):** Appropriate diversification?

5. **Max Exposure (50%):** Safe margin level?

6. **SL Priority:** Structure > Liquidity > ATR > Volatility — correct order?

7. **Multiple TP Levels:** 50/30/20 split — acceptable?

8. **Circuit Breaker States:** NORMAL → WARNING → RESTRICTED → HALTED — sufficient?

---

**Please review and approve (or request modifications) before I proceed to Phase 13 — Trade Management.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
