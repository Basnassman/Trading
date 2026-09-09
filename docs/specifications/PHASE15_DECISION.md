# PHASE 15 — DECISION ENGINE

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the **Decision Engine** — the final aggregation layer that synthesizes ALL engine outputs into a single, actionable decision with full transparency.

This engine produces:
1. Consolidated market state summary
2. Final decision (Execute, Wait, No Trade, Halt)
3. Complete trade plan (Entry, SL, TP₁/TP₂/TP₃)
4. Decision reasoning and audit trail
5. Confidence assessment

**Critical Rule:** Every number in the output must come from the model. No hardcoded, fake, or cosmetic values.

---

## B — INPUTS

### B.1 — All Engine Outputs

| Engine | Output | Phase |
|--------|--------|-------|
| Market Structure | Structure Score, State, BOS/MSS | 2 |
| Liquidity | Liquidity Score, Sweep, Levels | 3 |
| Flow | Flow Score, State, Absorption/Exhaustion | 4 |
| Trend | Trend Score, Direction, Strength | 5 |
| Momentum | Momentum Score, RSI, MACD | 5 |
| Volatility | Volatility Score, Regime | 5 |
| GSI | GSI Score, Direction, Confidence | 6 |
| News/Macro | News Score, Macro Score, DXY, Yields | 7 |
| Historical | P(Long), P(Short), P(NoTrade) | 8 |
| Regime | Regime Type, Confidence | 9 |
| Probability | Final P(Long), P(Short), P(NoTrade) | 10 |
| Setup | Setup Valid, Quality, Entry Trigger | 11 |
| Risk | Position Size, SL, TP, RR | 12 |
| Trade Management | TP₁/TP₂/TP₃, Partial Close Rules | 13 |
| No-Trade | Conditions, Severity, Decision | 14 |

### B.2 — Parameters

| Parameter | Initial Value | Description |
|-----------|--------------|-------------|
| `DECISION_CONFIDENCE_THRESHOLD` | 0.55 | Min confidence for execution |
| `DECISION_SETUP_QUALITY_MIN` | 60 | Min setup quality score |
| `DECISION_RR_MIN` | 1.5 | Min risk:reward |
| `DECISION_TIMEOUT_BARS` | 10 | Bars before decision expires |

---

## C — DECISION TYPES

### C.1 — Decision Enum

| Decision | Code | Description |
|----------|------|-------------|
| **EXECUTE** | 1 | Enter trade immediately |
| **WAIT_FOR_TRIGGER** | 2 | Setup valid, waiting for entry trigger |
| **WAIT_FOR_RETEST** | 3 | Setup valid, waiting for retest of level |
| **NO_TRADE** | 4 | Active decision not to trade |
| **HALT** | 5 | All trading halted (emergency) |
| **MANAGE_EXISTING** | 6 | Focus on managing open positions |

### C.2 — Decision Priority

$$\text{Decision} = \text{Priority}(\text{NoTrade}, \text{Halt}, \text{Setup}, \text{Risk})$$

| Priority | Condition | Decision |
|----------|-----------|----------|
| 1 | Halt active (Severity = CRITICAL) | HALT |
| 2 | No-Trade active (Severity ≥ RED) | NO_TRADE |
| 3 | Setup invalid | NO_TRADE |
| 4 | Risk limits exceeded | NO_TRADE |
| 5 | Setup valid + trigger fired | EXECUTE |
| 6 | Setup valid + no trigger | WAIT_FOR_TRIGGER |
| 7 | Setup valid + waiting for retest | WAIT_FOR_RETEST |
| 8 | Open positions need management | MANAGE_EXISTING |

---

## D — DECISION ALGORITHM

### D.1 — Flowchart

```
START
│
├── HALT active? ──YES──→ HALT
│
├── NO_TRADE active? ──YES──→ NO_TRADE
│
├── Open positions to manage? ──YES──→ MANAGE_EXISTING
│
├── Setup valid?
│   ├── NO → NO_TRADE
│   └── YES →
│       ├── Entry trigger fired?
│       │   ├── YES → EXECUTE
│       │   ├── Waiting for retest? → WAIT_FOR_RETEST
│       │   └── NO → WAIT_FOR_TRIGGER
│       │
│       └── Risk approved?
│           ├── NO → NO_TRADE
│           └── YES → (proceed with decision)
│
└── END
```

### D.2 — EXECUTE Decision

$$\text{Decision} = \text{EXECUTE} \iff$$

$$\text{HaltActive} = \text{False}$$

$$\wedge \quad \text{NoTradeActive} = \text{False}$$

$$\wedge \quad \text{SetupValid} = \text{True}$$

$$\wedge \quad \text{EntryTriggerFired} = \text{True}$$

$$\wedge \quad \text{RiskApproved} = \text{True}$$

$$\wedge \quad P(\text{action}) \geq \text{DECISION\_CONFIDENCE\_THRESHOLD}$$

$$\wedge \quad \text{SetupQuality} \geq \text{DECISION\_SETUP\_QUALITY\_MIN}$$

$$\wedge \quad \text{RR} \geq \text{DECISION\_RR\_MIN}$$

### D.3 — WAIT_FOR_TRIGGER Decision

$$\text{Decision} = \text{WAIT\_FOR\_TRIGGER} \iff$$

$$\text{SetupValid} = \text{True}$$

$$\wedge \quad \text{EntryTriggerFired} = \text{False}$$

$$\wedge \quad \text{SetupExpired} = \text{False}$$

$$\wedge \quad \text{NoTradeActive} = \text{False}$$

### D.4 — WAIT_FOR_RETEST Decision

$$\text{Decision} = \text{WAIT\_FOR\_RETEST} \iff$$

$$\text{SetupValid} = \text{True}$$

$$\wedge \quad \text{EntryTriggerType} = \text{RETEST}$$

$$\wedge \quad \text{RetestPending} = \text{True}$$

$$\wedge \quad \text{NoTradeActive} = \text{False}$$

### D.5 — NO_TRADE Decision

$$\text{Decision} = \text{NO\_TRADE} \iff$$

$$\text{HaltActive} = \text{False}$$

$$\wedge \quad (\text{NoTradeActive} = \text{True} \vee \text{SetupValid} = \text{False} \vee \text{RiskApproved} = \text{False})$$

### D.6 — HALT Decision

$$\text{Decision} = \text{HALT} \iff \text{HaltActive} = \text{True}$$

**Halt conditions:**
- Drawdown > 20%
- Daily loss > 5%
- Connection lost
- Emergency exit triggered

---

## E — CONSOLIDATED STATE SUMMARY

### E.1 — Market State

The Decision Engine produces a consolidated view:

```
=== MARKET STATE ===
Instrument: XAUUSD
Time: 2026-08-31 14:30 UTC
Session: London

=== STRUCTURE ===
State: Bullish (+78)
Last Swing: High @ 1852.30
BOS: Bullish @ 1853.10 (Score: 72)
MSS: None

=== LIQUIDITY ===
Score: +91
Nearest Support: 1842.50 (Swing Low, LS=72)
Nearest Resistance: 1858.30 (EQH Cluster, LS=85)
Sweep: None

=== FLOW ===
Score: +87
State: Buying
RVOL: 1.8 (Above Average)
Pressure: BP=0.72, SP=0.28

=== TREND/MOMENTUM/VOLATILITY ===
Trend: Bullish (+65)
Momentum: Bullish (+42)
Volatility: Normal (-8)

=== GSI ===
Score: +82
Direction: Strong Bullish
Confidence: 0.82

=== NEWS/MACRO ===
News Score: +15 (Neutral)
Macro Score: +35 (Slightly Bullish Gold)
DXY: 104.85 (Bullish)
10Y Yield: 4.35% (Rising)

=== HISTORICAL ===
P(Long): 79% (K=312, calibrated)
P(Short): 14%
P(NoTrade): 7%

=== REGIME ===
Type: Normal Trend
Confidence: 0.85
Duration: 34 bars

=== PROBABILITY ===
P(Long): 84% (calibrated)
P(Short): 12%
P(NoTrade): 4%
Confidence: 0.72 (High)
```

### E.2 — No numbers are hardcoded

**Every number in the output comes from:**
- Engine computations (Phase 2–10)
- Real-time data (MT5)
- Model outputs (Phase 11–14)

**The system NEVER outputs:**
- "Probability = 80%" without source
- "GSI = +82" without computation
- Fake or placeholder values

---

## F — TRADE PLAN

### F.1 — Complete Trade Plan (when EXECUTE)

```
=== TRADE PLAN ===
Decision: EXECUTE LONG

=== ENTRY ===
Entry Price: 1848.50 (next bar open)
Entry Trigger: BOS @ 1853.10 (confirmed)
Invalidation: 1841.00

=== STOP LOSS ===
Method: Structure-based
Level: 1842.50 (Last Swing Low - 0.05 ATR)
Distance: 6.00 pips

=== TAKE PROFIT ===
TP₁: 1858.50 (+10.00, RR 1:1.67) — 50% close
TP₂: 1868.50 (+20.00, RR 1:3.33) — 30% close
TP₃: 1878.50 (+30.00, RR 1:5.00) — 20% trail

=== POSITION SIZE ===
Lots: 1.67
Risk Amount: $100.00 (1% of equity)
Notional: $30,919.95

=== RISK ASSESSMENT ===
RR Ratio: 1:1.67 (minimum 1.5 ✓)
Setup Quality: 88/100 (Excellent)
Execution Quality: 86/100
Regime: Normal Trend (Size Factor: 1.0)

=== CONFIDENCE ===
P(Long): 84%
GSI: +82
Families Aligned: 7/8
Confidence Level: HIGH
```

### F.2 — Trade Plan Components

| Component | Source | Phase |
|-----------|--------|-------|
| Entry Price | Next bar open | 11 |
| Entry Trigger | Phase 11 output | 11 |
| Invalidation | Phase 11 output | 11 |
| Stop Loss | Phase 12 output | 12 |
| TP₁/TP₂/TP₃ | Phase 13 output | 13 |
| Position Size | Phase 12 output | 12 |
| Risk Amount | Phase 12 output | 12 |
| RR Ratio | Phase 12 output | 12 |
| Setup Quality | Phase 11 output | 11 |
| Confidence | Phase 10 output | 10 |

---

## G — WAIT DECISION DETAILS

### G.1 — WAIT_FOR_TRIGGER

```
=== DECISION: WAIT FOR TRIGGER ===
Setup: LONG @ 1848.50 (identified)
Status: Valid, waiting for entry trigger

=== WHAT WE'RE WAITING FOR ===
Trigger Type: BOS Entry
Required: Close above 1853.10
Current Price: 1848.50
Distance to Trigger: 4.60 pips

=== SETUP STATUS ===
Setup Valid: ✅
Setup Quality: 88/100
Time Remaining: 7 bars (35 minutes)
Expiry: 15:05 UTC

=== CONDITIONS ===
All 10 requirements: PASS ✅
No-Trade: CLEAR ✅
Risk: APPROVED ✅
```

### G.2 — WAIT_FOR_RETEST

```
=== DECISION: WAIT FOR RETEST ===
Setup: LONG (BOS @ 1853.10)
Status: BOS confirmed, waiting for retest

=== WHAT WE'RE WAITING FOR ===
Retest Level: 1853.10 (broken resistance → support)
Required: Price returns to 1853.10 + rejection
Current Price: 1856.20
Distance to Retest: 3.10 pips

=== SETUP STATUS ===
Setup Valid: ✅
Setup Quality: 88/100
Time Remaining: 7 bars (35 minutes)
```

---

## H — NO_TRADE DECISION DETAILS

### H.1 — No-Trade with Reason

```
=== DECISION: NO TRADE ===
Reason: Extreme Spread (3.5 pips > 3.0 threshold)
Severity: RED (3)

=== CONDITION DETAILS ===
Spread: 3.5 pips (Halt threshold: 3.0)
Duration: 12 minutes
Expected Resolution: When spread ≤ 1.5 for 3 bars

=== WHAT WAS EVALUATED ===
Setup: LONG @ 1848.50
Quality: 88/100
P(Long): 84%
But: Spread blocks execution

=== ALTERNATIVE ===
Wait for spread to normalize
Monitor for spread reduction
Re-evaluate when condition resolves
```

### H.2 — No-Trade (Setup Invalid)

```
=== DECISION: NO TRADE ===
Reason: Setup requirements not met

=== FAILED REQUIREMENTS ===
❌ GSI = -12 (required > +30)
❌ Flow = +15 (required > +20)

=== PASSED REQUIREMENTS ✅
P(Long) = 64%
Structure = Bullish
Liquidity = Support held
Regime = Normal Trend
RR = 1:1.8
Session = London
Spread = 0.8 pips
Conflicts = 0/8

=== RECOMMENDATION ===
Wait for GSI and Flow to align
Re-evaluate at next bar
```

---

## I — DECISION AUDIT TRAIL

### I.1 — Audit Record

Every decision produces a complete audit record:

```python
@dataclass(frozen=True)
class DecisionAudit:
    """Complete audit trail for a decision."""
    decision_id: str
    timestamp: datetime
    
    # Market State (snapshot)
    price: float
    session: str
    regime: str
    regime_confidence: float
    
    # Engine Outputs
    structure_score: float
    liquidity_score: float
    flow_score: float
    trend_score: float
    momentum_score: float
    volatility_score: float
    gsi_score: float
    news_score: float
    macro_score: float
    historical_p_long: float
    historical_p_short: float
    
    # Probability
    p_long: float
    p_short: float
    p_no_trade: float
    confidence: float
    
    # Setup
    setup_valid: bool
    setup_quality: float
    setup_direction: str | None
    entry_trigger: str | None
    rr_ratio: float
    
    # Risk
    position_size: float
    stop_loss: float
    take_profit: float
    risk_amount: float
    
    # No-Trade
    no_trade_active: bool
    no_trade_conditions: list[str]
    no_trade_severity: int
    
    # Decision
    decision: str
    decision_reasons: list[str]
    
    # Provenance
    provenance: DataProvenance
```

### I.2 — Audit Trail Purpose

| Purpose | Description |
|---------|-------------|
| Accountability | Every decision is traceable |
| Debugging | Identify why decisions were made |
| Optimization | Analyze decision patterns |
| Compliance | Regulatory requirements |
| Learning | Improve system over time |

---

## J — EDGE CASES

### J.1 — Multiple Decisions

| Scenario | Handling |
|----------|----------|
| EXECUTE and MANAGE_EXISTING both applicable | Prioritize EXECUTE (new trade) |
| WAIT and NO_TRADE both applicable | NO_TRADE wins (conservative) |
| HALT overrides everything | HALT always wins |

### J.2 — Decision Expiry

| Scenario | Handling |
|----------|----------|
| WAIT expires (10 bars) | Decision becomes NO_TRADE (setup expired) |
| Setup degrades during WAIT | Re-evaluate; may become NO_TRADE |
| Conditions change during WAIT | Re-evaluate; may become EXECUTE |

### J.3 — Rapid Decision Changes

| Scenario | Handling |
|----------|----------|
| Decision flips every bar | Log as `unstable_decision`; apply stability filter |
| > 3 decision changes in 10 bars | Flag `choppy_market`; increase thresholds |

---

## K — BIAS PREVEntion

### K.1 — Look-Ahead Bias

**Prevention:**
1. All decision inputs from confirmed bar data
2. Entry at next bar open, not current bar close
3. No future knowledge in decision process

### K.2 — Overfitting

**Prevention:**
1. Decision parameters are conservative
2. Walk-forward validation
3. Audit trail enables post-hoc analysis

### K.3 — Confirmation Bias

**Prevention:**
1. Decision algorithm is **deterministic** — same inputs → same decision
2. No human override in automated mode
3. All conditions evaluated objectively

---

## L — BACKTESTABILITY

### L.1 — Backtest Requirements

| Requirement | Implementation |
|-------------|---------------|
| Decision computation | Bar-by-bar, deterministic |
| Entry timing | Next bar open |
| Audit trail | Complete record per decision |
| No-Trade impact | Reduces trade count realistically |

### L.2 — Backtest Output

For each bar, the backtest records:
- Decision made
- All engine outputs
- Trade plan (if EXECUTE)
- Outcome (if position closed)

---

## M — WHAT IS FIXED

### M.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Decision Types | 6 | Comprehensive coverage |
| Priority Order | Halt > NoTrade > Setup > Risk | Safety-first |
| Confidence Threshold | 0.55 | Minimum for execution |
| Setup Quality Min | 60 | Minimum quality |
| RR Min | 1.5 | Positive expectancy |
| Decision Timeout | 10 bars | Timeliness |
| Audit Trail | Complete | Full transparency |

### M.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal confidence threshold | Phase 17 (Optimization) |
| Optimal setup quality min | Phase 17 |
| Decision timeout period | Phase 17 |
| Stability filter period | Phase 17 |

---

## N — WHAT REQUIRES TESTING

### N.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | Decision engine reduces false signals | Compare with/without | Fewer but better trades |
| H2 | Confidence threshold of 0.55 is optimal | Test range [0.50–0.65] | Optimal in [0.53–0.58] |
| H3 | WAIT decisions improve entry timing | Compare immediate vs. wait | Wait entries have better RR |
| H4 | Audit trail enables useful analysis | Post-hoc review | Identify decision patterns |
| H5 | Deterministic decisions are reproducible | Run same data twice | 100% reproducibility |

### N.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Should decision be more aggressive? | Test lower thresholds |
| Q2 | How many decision types are optimal? | Test simplified set |
| Q3 | Should we add a CONFIDENCE_REVIEW decision? | Test review workflow |
| Q4 | How to handle conflicting engine outputs? | Test priority rules |

---

## O — OUTPUT SCHEMA

### O.1 — Decision Output

```python
@dataclass(frozen=True)
class DecisionOutput:
    """Decision Engine final output."""
    decision_id: str
    timestamp: datetime
    
    # Decision
    decision: str                       # "execute", "wait_trigger", "wait_retest", "no_trade", "halt", "manage"
    decision_code: int                  # 1–6
    
    # Market State Summary
    price: float
    session: str
    regime: str
    gsi: float
    
    # Consolidated Scores
    structure_score: float
    liquidity_score: float
    flow_score: float
    trend_score: float
    momentum_score: float
    volatility_score: float
    
    # Probability
    p_long: float
    p_short: float
    p_no_trade: float
    confidence: float
    
    # Trade Plan (if EXECUTE)
    trade_plan: TradePlan | None
    
    # No-Trade Details (if NO_TRADE)
    no_trade_reasons: list[str]
    no_trade_severity: int
    
    # Wait Details (if WAIT)
    wait_for: str | None                # "trigger" or "retest"
    trigger_required: str | None
    distance_to_trigger: float | None
    time_remaining_bars: int | None
    
    # Quality
    setup_quality: float
    execution_quality: float
    
    # Audit
    audit: DecisionAudit
    
    # Provenance
    provenance: DataProvenance
```

### O.2 — Trade Plan Schema

```python
@dataclass(frozen=True)
class TradePlan:
    """Complete trade plan for EXECUTE decision."""
    direction: str                       # "long" or "short"
    entry_price: float
    entry_trigger: str
    invalidation: float
    
    stop_loss: float
    stop_method: str                     # "structure", "liquidity", "atr"
    
    tp1: float
    tp1_pct: float                       # 0.50
    tp2: float
    tp2_pct: float                       # 0.30
    tp3: float
    tp3_pct: float                       # 0.20
    
    rr_ratio: float
    position_size: float
    risk_amount: float
    
    regime_factor: float
    setup_quality: float
```

---

## P — DECISION OUTPUT

### P.1 — EXECUTE Decision

```
╔══════════════════════════════════════════════════════════════╗
║                    DECISION ENGINE v1.0                      ║
╠══════════════════════════════════════════════════════════════╣
║ Decision: EXECUTE LONG                                       ║
║ Time: 2026-08-31 14:30 UTC                                  ║
║ Confidence: HIGH (84%)                                       ║
╠══════════════════════════════════════════════════════════════╣
║ MARKET STATE                                                 ║
║ Price: 1848.50 | Session: London | Regime: Normal Trend      ║
║                                                              ║
║ SCORES                                                       ║
║ Structure: +78 | Liquidity: +91 | Flow: +87                 ║
║ Trend: +65 | Momentum: +42 | Volatility: -8                 ║
║ GSI: +82 | News: +15 | Macro: +35                           ║
║                                                              ║
║ PROBABILITY                                                  ║
║ P(Long): 84% | P(Short): 12% | P(NoTrade): 4%              ║
║ Confidence: 0.72 (High) | Calibrated: Yes (ECE=0.07)       ║
╠══════════════════════════════════════════════════════════════╣
║ TRADE PLAN                                                   ║
║ Entry: 1848.50 (next bar open)                               ║
║ Trigger: BOS @ 1853.10 (Score: 72)                          ║
║ Invalidation: 1841.00                                        ║
║                                                              ║
║ SL: 1842.50 (Structure, -6.00)                              ║
║ TP₁: 1858.50 (+10.00, 50%)                                 ║
║ TP₂: 1868.50 (+20.00, 30%)                                 ║
║ TP₃: 1878.50 (+30.00, 20%)                                 ║
║                                                              ║
║ RR: 1:1.67 | Lots: 1.67 | Risk: $100 (1%)                  ║
║ Setup Quality: 88/100 | Execution Quality: 86/100           ║
╠══════════════════════════════════════════════════════════════╣
║ NO-TRADE: CLEAR ✅                                           ║
║ Risk Limits: ALL CLEAR ✅                                    ║
║ Audit ID: DEC-20260831-143000-001                           ║
╚══════════════════════════════════════════════════════════════╝
```

### P.2 — NO_TRADE Decision

```
╔══════════════════════════════════════════════════════════════╗
║                    DECISION ENGINE v1.0                      ║
╠══════════════════════════════════════════════════════════════╣
║ Decision: NO TRADE                                           ║
║ Time: 2026-08-31 14:30 UTC                                  ║
║ Severity: RED (3)                                            ║
╠══════════════════════════════════════════════════════════════╣
║ REASON                                                       ║
║ Extreme Spread: 3.5 pips (threshold: 3.0)                   ║
║ Duration: 12 minutes                                         ║
║ Resolution: When spread ≤ 1.5 for 3 bars                    ║
║                                                              ║
║ EVALUATED SETUP                                              ║
║ Direction: LONG | Quality: 88/100                           ║
║ P(Long): 84% | RR: 1:1.67                                  ║
║ All 10 requirements: PASS ✅                                ║
║ But: Spread blocks execution                                ║
╠══════════════════════════════════════════════════════════════╣
║ RECOMMENDATION                                               ║
║ Wait for spread to normalize                                ║
║ Re-evaluate when condition resolves                         ║
║ Audit ID: DEC-20260831-143000-002                           ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Q — APPROVAL GATE

### The Phase 15 — Decision Engine specification is now complete.

**Summary of what is defined:**

1. ✅ 6 Decision types (Execute, Wait×2, No Trade, Halt, Manage)
2. ✅ Decision priority algorithm
3. ✅ Consolidated market state summary
4. ✅ Complete trade plan (Entry, SL, TP₁/TP₂/TP₃)
5. ✅ All numbers from model (no fake values)
6. ✅ Decision audit trail
7. ✅ Wait decision details (what we're waiting for)
8. ✅ No-Trade decision details (why not trading)
9. ✅ Edge cases and handling
10. ✅ Bias prevention measures
11. ✅ Backtest requirements
12. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **6 Decision Types:** Comprehensive enough?

2. **Priority Order:** Halt > NoTrade > Setup > Risk — correct?

3. **Confidence Threshold (0.55):** Minimum for execution?

4. **Decision Timeout (10 bars):** Appropriate for M5?

5. **Audit Trail:** Complete enough for accountability?

6. **Output Format:** Clear and actionable?

7. **No Fake Numbers:** Is the rule enforced in the schema?

8. **Trade Plan Completeness:** All necessary components included?

---

**Please review and approve (or request modifications) before I proceed to Phase 16 — Backtest Architecture.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
