# PHASE 11 — SETUP ENGINE

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the **Setup Validation** framework — ensuring that no trade is entered based on probability alone. Every setup must satisfy a **multi-factor checklist** before entry is permitted.

This engine produces:
1. Setup validation (pass/fail for each requirement)
2. Entry trigger definition
3. Invalidation level
4. Confirmation criteria
5. Retest detection
6. Rejection detection
7. Setup quality score

**Critical Rule:** Probability is **necessary but not sufficient**. A trade requires probability AND structure AND liquidity AND flow AND risk-reward AND execution quality.

---

## B — INPUTS

### B.1 — Required Evidence

| Evidence | Source | Phase | Required for Setup |
|----------|--------|-------|-------------------|
| P(Long) / P(Short) | Phase 10 | 10 | ✅ Minimum threshold |
| GSI | Phase 6 | 6 | ✅ Directional alignment |
| Structure State | Phase 2 | 2 | ✅ BOS/MSS confirmation |
| Liquidity Levels | Phase 3 | 3 | ✅ Support/resistance context |
| Flow Score | Phase 4 | 4 | ✅ Volume confirmation |
| Regime | Phase 9 | 9 | ✅ Regime-appropriate |
| Volatility | Phase 5 | 5 | ✅ ATR for SL/TP |
| Session | Phase 1 | 1 | ✅ Active session |

### B.2 — Parameters

| Parameter | Initial Value | Description |
|-----------|--------------|-------------|
| `MIN_P_ACTION` | 0.55 | Minimum P(Long) or P(Short) |
| `MIN_GSI_ALIGNMENT` | +30 / -30 | GSI must align with direction |
| `MIN_RR_RATIO` | 1.5 | Minimum Risk:Reward ratio |
| `MIN_BOS_SCORE` | 40 | Minimum BOS strength for confirmation |
| `MIN_FLOW_SCORE` | +20 / -20 | Flow must align with direction |
| `ENTRY_SESSION_REQUIRED` | True | Must be in active session |
| `MAX_SPREAD_PIPS` | 2.0 | Maximum spread for entry |
| `SETUP_EXPIRY_BARS` | 10 | Bars before setup expires |

---

## C — SETUP REQUIREMENTS

### C.1 — Long Setup Checklist

| # | Requirement | Condition | Status |
|---|------------|-----------|--------|
| 1 | Probability | P(Long) ≥ `MIN_P_ACTION` (0.55) | ☐ |
| 2 | GSI Direction | GSI > +30 | ☐ |
| 3 | Structure Confirmation | Structure = Bullish OR Bullish BOS/CHoCH detected | ☐ |
| 4 | Liquidity Confirmation | Price above nearest support OR support held | ☐ |
| 5 | Flow Confirmation | FlowScore > +20 | ☐ |
| 6 | Regime Appropriate | Regime ∈ {Trend, Breakout} (not News, not High Vol) | ☐ |
| 7 | Risk:Reward | RR ≥ `MIN_RR_RATIO` (1.5) | ☐ |
| 8 | Session Active | Current session ∈ {London, Overlap, NewYork} | ☐ |
| 9 | Spread Acceptable | Spread ≤ `MAX_SPREAD_PIPS` (2.0) | ☐ |
| 10 | No Conflicting Evidence | < 3 families bearish | ☐ |

### C.2 — Short Setup Checklist

| # | Requirement | Condition | Status |
|---|------------|-----------|--------|
| 1 | Probability | P(Short) ≥ `MIN_P_ACTION` (0.55) | ☐ |
| 2 | GSI Direction | GSI < -30 | ☐ |
| 3 | Structure Confirmation | Structure = Bearish OR Bearish BOS/CHoCH detected | ☐ |
| 4 | Liquidity Confirmation | Price below nearest resistance OR resistance held | ☐ |
| 5 | Flow Confirmation | FlowScore < -20 | ☐ |
| 6 | Regime Appropriate | Regime ∈ {Trend, Breakout} (not News, not High Vol) | ☐ |
| 7 | Risk:Reward | RR ≥ `MIN_RR_RATIO` (1.5) | ☐ |
| 8 | Session Active | Current session ∈ {London, Overlap, NewYork} | ☐ |
| 9 | Spread Acceptable | Spread ≤ `MAX_SPREAD_PIPS` (2.0) | ☐ |
| 10 | No Conflicting Evidence | < 3 families bullish | ☐ |

### C.3 — Setup Pass/Fail

$$\text{Setup}_{\text{valid}} \iff \bigwedge_{i=1}^{10} \text{Requirement}_i = \text{Pass}$$

**All 10 requirements must pass.** Partial setups are logged but not traded.

### C.4 — Setup Quality Score

$$\text{SetupQuality} = \frac{\sum_{i=1}^{10} \text{Score}_i}{10} \times 100$$

Where each $\text{Score}_i \in [0, 10]$ based on how strongly the requirement is satisfied.

| Quality | Score | Interpretation |
|---------|-------|---------------|
| Excellent | 85–100 | All requirements strongly met |
| Good | 70–84 | Most requirements well met |
| Adequate | 55–69 | Requirements marginally met |
| Poor | < 55 | Below threshold — do not trade |

---

## D — ENTRY TRIGGER

### D.1 — Definition

The **Entry Trigger** is the specific price action that confirms the setup and initiates entry.

**Entry is NOT automatic when setup passes.** The system waits for a trigger.

### D.2 — Entry Trigger Types

#### Type 1: BOS Entry

$$\text{Trigger}_{\text{BOS}} \iff C_t > s_{\text{last\_high}} + \text{BOS\_tolerance} \quad \text{(Long)}$$

$$\text{Trigger}_{\text{BOS}} \iff C_t < s_{\text{last\_low}} - \text{BOS\_tolerance} \quad \text{(Short)}$$

**Condition:** Setup must be valid at bar $t-1$. Trigger at bar $t$.

#### Type 2: Retest Entry

$$\text{Trigger}_{\text{Retest}} \iff \text{Price returned to level} + \text{Rejection confirmed}$$

**Condition:** After BOS, price retests the broken level and rejects.

#### Type 3: MSS/CHoCH Entry

$$\text{Trigger}_{\text{MSS}} \iff \text{MSS/CHoCH detected at bar } t$$

**Condition:** Setup valid, MSS/CHoCH provides the entry signal.

#### Type 4: Candle Confirmation Entry

$$\text{Trigger}_{\text{Candle}} \iff \text{Bullish engulfing / Pin bar / etc. at key level}$$

**Condition:** Setup valid, price at key level, candle pattern confirms.

### D.3 — Trigger Priority

| Priority | Trigger Type | When to Use |
|----------|-------------|-------------|
| 1 | BOS Entry | Trend continuation |
| 2 | Retest Entry | After BOS, waiting for retest |
| 3 | MSS/CHoCH Entry | Reversal setup |
| 4 | Candle Confirmation | At key levels |

### D.4 — Trigger Timing

$$\text{EntryTime} = \tau_t + \text{bar\_duration}$$

Entry is at the **open of the next bar** after trigger confirmation.

**Backtest Rule:** Entry at next bar open, not at trigger bar close.

---

## E — INVALIDATION

### E.1 — Definition

The **Invalidation Level** is the price at which the setup is **no longer valid**. If price reaches this level, the setup is discarded.

### E.2 — Invalidation for Long Setup

$$\text{Invalidation}_{\text{long}} = \min(\text{Last Swing Low}, \text{Nearest Support}) - \text{Buffer}$$

Where $\text{Buffer} = 0.02 \times \text{ATR}_{14}$.

### E.3 — Invalidation for Short Setup

$$\text{Invalidation}_{\text{short}} = \max(\text{Last Swing High}, \text{Nearest Resistance}) + \text{Buffer}$$

### E.4 — Invalidation Rules

| Rule | Description |
|------|-------------|
| I1 | Invalidation is set BEFORE entry |
| I2 | Invalidation is based on structure/liquidity, not arbitrary |
| I3 | If price reaches invalidation, setup is permanently discarded |
| I4 | Invalidation cannot be moved further from price once set |

### E.5 — Invalidation vs. Stop Loss

| Concept | Invalidation | Stop Loss |
|---------|-------------|-----------|
| Purpose | Setup validity | Trade protection |
| Set when | Before entry | At entry |
| Based on | Structure/Liquidity | Risk management |
| Effect of breach | Setup discarded | Position closed |
| Can be adjusted? | No (fixed) | Yes (trailing) |

---

## F — CONFIRMATION

### F.1 — Definition

**Confirmation** is additional evidence that the setup is valid, beyond the initial checklist.

### F.2 — Confirmation Levels

| Level | Confirmation | Required? |
|-------|-------------|-----------|
| L1 (Minimum) | Setup checklist passes | ✅ Yes |
| L2 (Entry) | Entry trigger fires | ✅ Yes |
| L3 (Post-Entry) | Price moves in expected direction within N bars | ⚠️ Optional |
| L4 (Strong) | Multiple timeframe confirmation | ⭐ Bonus |

### F.3 — Post-Entry Confirmation

$$\text{PostEntryConfirm}_{\text{long}} \iff C_{t+n} > C_t + \text{confirmation\_threshold}$$

Where:
- $n = 3$ bars (initial)
- $\text{confirmation\_threshold} = 0.10 \times \text{ATR}_{14}$

**If not confirmed within $n$ bars:** Consider early exit or reduce position.

### F.4 — Multi-Timeframe Confirmation

| Timeframe | Confirmation |
|-----------|-------------|
| D1 | Trend direction aligns |
| H4 | Structure aligns |
| H1 | Entry trigger on H1 |
| M15 | Flow confirms |
| M5 | Entry execution |

**Bonus:** More timeframes aligned = higher setup quality.

---

## G — RETEST

### G.1 — Definition

A **Retest** occurs when price returns to a broken level (after BOS) and tests it as new support/resistance.

### G.2 — Retest Detection

$$\text{Retest}_{\text{long}} \iff \text{After Bullish BOS}$$

$$\wedge \quad \text{Price returned to broken level}$$

$$\wedge \quad |L_t - \text{BOS\_level}| < \tau_{\text{retest}}$$

$$\wedge \quad C_t > \text{BOS\_level} \quad \text{(held as support)}$$

Where $\tau_{\text{retest}} = 0.05 \times \text{ATR}_{14}$.

### G.3 — Retest Quality

$$\text{RetestQuality} = f(\text{TouchCount}, \text{RejectionStrength}, \text{Volume})$$

| Quality | Description |
|---------|-------------|
| Clean Retest | Single touch, strong rejection, high volume |
| Multiple Retest | 2–3 touches, still holding |
| Failed Retest | Level broken again — invalidate |

### G.4 — Retest Entry

Retest entries are often **better** than BOS entries:
- Tighter stop (just below the retested level)
- Clearer invalidation
- Higher probability (level confirmed as support/resistance)

---

## H — REJECTION

### H.1 — Definition

A **Rejection** occurs when price reaches a level but fails to break through, closing back on the original side.

### H.2 — Rejection Detection

$$\text{Rejection}_{\text{bearish}} \iff H_t > \text{Level} + \tau_{\text{penetration}}$$

$$\wedge \quad C_t < \text{Level}$$

$$\wedge \quad \text{Range} > 0.5 \times \text{ATR}_{14}$$

**Interpretation:** Price poked above level, closed below — sellers defended the level.

### H.3 — Rejection Strength

$$\text{RejectionStrength} = \frac{|C_t - H_t|}{H_t - L_t}$$

- Strong rejection: Close near low of bar (large wick above)
- Weak rejection: Close near middle (small wick)

### H.4 — Rejection as Entry Trigger

Rejection at a key level can serve as an entry trigger:

$$\text{Trigger}_{\text{Rejection}} \iff \text{Rejection at liquidity level} + \text{Setup valid}$$

---

## I — SETUP LIFECYCLE

### I.1 — Lifecycle States

```
SETUP IDENTIFIED
    ↓
CHECKLIST EVALUATION
    ├── FAIL → SETUP REJECTED
    └── PASS →
        ↓
WAIT FOR TRIGGER
    ├── EXPIRED → SETUP EXPIRED
    ├── INVALIDATED → SETUP INVALIDATED
    └── TRIGGERED →
        ↓
ENTRY EXECUTED
    ↓
POST-ENTRY CONFIRMATION
    ├── NOT CONFIRMED → CONSIDER EXIT
    └── CONFIRMED →
        ↓
POSITION MANAGEMENT (Phase 13)
```

### I.2 — Setup Expiry

$$\text{Setup}_{\text{expired}} \iff \text{Trigger not fired within } \text{SETUP\_EXPIRY\_BARS} \text{ bars}$$

Where `SETUP_EXPIRY_BARS` = 10 (initial).

**Rationale:** Market conditions change. A valid setup from 10 bars ago may no longer be relevant.

### I.3 — Setup Invalidation

$$\text{Setup}_{\text{invalidated}} \iff \text{Price reached Invalidation Level}$$

**OR**

$$\text{Setup}_{\text{invalidated}} \iff \text{Regime changed to News/PostNews}$$

**OR**

$$\text{Setup}_{\text{invalidated}} \iff \text{Spread exceeded MAX\_SPREAD for > 3 bars}$$

---

## J — EDGE CASES

### J.1 — Multiple Setups

| Scenario | Handling |
|----------|----------|
| Long and Short setups both valid | Take the one with higher P(action) |
| Multiple Long setups at different levels | Take the nearest to current price |
| Setup forms during News regime | Mark as `news_override`; wait for Post-News |

### J.2 — Setup Degradation

| Scenario | Handling |
|----------|----------|
| One requirement fails after passing | Setup becomes `pending_review` |
| Two+ requirements fail | Setup rejected |
| GSI drops below threshold | Setup weakened; reduce quality score |

### J.3 — Rapid Setup Formation

| Scenario | Handling |
|----------|----------|
| Setup forms and expires within 5 bars | Log as `weak_setup`; consider higher threshold |
| > 3 setups expire in 20 bars | Flag `choppy_market`; increase thresholds |

---

## K — BIAS PREVENTION

### K.1 — Look-Ahead Bias

**Prevention:**
1. Setup evaluated using only confirmed bar data
2. Entry trigger requires bar close confirmation
3. Invalidation set before entry

### K.2 — Overfitting

**Prevention:**
1. Setup requirements are initial; optimization in Phase 17
2. Walk-forward validation of setup effectiveness
3. Minimum quality score prevents marginal setups

### K.3 — Confirmation Bias

**Prevention:**
1. Setup checklist is **mandatory** — no exceptions
2. All 10 requirements must pass — no cherry-picking
3. Setup quality score is objective

---

## L — BACKTESTABILITY

### L.1 — Backtest Requirements

| Requirement | Implementation |
|-------------|---------------|
| Setup evaluation | Bar-by-bar, no future data |
| Entry timing | Next bar open after trigger |
| Invalidation | Checked every bar |
| Expiry | Checked every bar |
| Quality scoring | Objective, reproducible |

### L.2 — Backtest Data Flow

```
All Engine Outputs (Phase 2–10)
    ↓
Setup Identification (per bar)
    ↓
Checklist Evaluation (10 requirements)
    ├── FAIL → Log rejection reason
    └── PASS →
        ↓
Wait for Trigger
    ↓
Entry at Next Bar Open
    ↓
Post-Entry Monitoring
    ↓
Setup Outcome (Win/Loss/Expired)
```

---

## M — WHAT IS FIXED

### M.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Setup Requirements | 10 | Comprehensive validation |
| Min P(Action) | 0.55 | Majority probability required |
| Min GSI | ±30 | Meaningful directional evidence |
| Min RR | 1.5 | Positive expectancy required |
| Min BOS Score | 40 | Valid BOS required |
| Min Flow Score | ±20 | Flow must confirm |
| Max Spread | 2.0 pips | Execution quality |
| Setup Expiry | 10 bars | Timeliness |
| Entry Timing | Next bar open | Realistic execution |
| Buffer for Invalidation | 0.02 ATR | Small buffer |

### M.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal setup requirements | Phase 17 (Optimization) |
| Min P(Action) threshold | Phase 17 |
| Min RR ratio | Phase 17 |
| Setup expiry period | Phase 17 |
| Trigger type selection | Phase 17 |
| Post-entry confirmation rules | Phase 17 |

---

## N — WHAT REQUIRES TESTING

### N.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | 10 requirements reduce false signals | Ablation test (remove requirements) | More requirements → fewer but better trades |
| H2 | Min P(Action) of 0.55 is appropriate | Test range [0.50–0.65] | Optimal in [0.53–0.58] |
| H3 | Min RR of 1.5 ensures positive expectancy | Backtest | Expectancy > 0 when RR ≥ 1.5 |
| H4 | Setup expiry of 10 bars is optimal | Test range [5–20] | Optimal in [8–12] |
| H5 | Retest entries outperform BOS entries | Compare win rates | Retest > BOS |
| H6 | Setup quality score predicts outcome | Correlation test | ρ > 0.3 |

### N.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Should some requirements be weighted more? | Test requirement importance |
| Q2 | Is 10 requirements too many (analysis paralysis)? | Test reduced set |
| Q3 | Should regime affect which requirements are needed? | Test regime-specific checklists |
| Q4 | How to handle setup during session transition? | Test session-specific rules |

---

## O — OUTPUT SCHEMA

### O.1 — Setup Output

```python
@dataclass(frozen=True)
class SetupOutput:
    """Setup Engine output for a potential trade."""
    timestamp: datetime
    
    # Setup Type
    direction: str                       # "long" or "short"
    setup_type: str                      # "bos", "retest", "mss", "candle"
    
    # Checklist
    requirements: dict[str, bool]        # Each requirement pass/fail
    all_passed: bool                     # All 10 requirements
    failed_requirements: list[str]       # Names of failed requirements
    
    # Quality
    setup_quality: float                 # [0, 100]
    quality_rating: str                  # "excellent", "good", "adequate", "poor"
    
    # Entry
    entry_price: float | None            # Target entry price
    entry_trigger: str | None            # Trigger type
    trigger_bar: datetime | None         # When trigger fired
    
    # Invalidation
    invalidation_price: float            # Invalidation level
    invalidation_reason: str             # What level invalidates
    
    # Risk:Reward
    stop_loss: float                     # Proposed SL
    take_profit: float                   # Proposed TP
    rr_ratio: float                      # Reward / Risk
    
    # Status
    status: str                          # "identified", "waiting", "triggered", "expired", "invalidated"
    expiry_bar: datetime                 # When setup expires
    
    # Provenance
    provenance: DataProvenance
```

---

## P — DECISION OUTPUT

### P.1 — Setup Identified

```
=== SETUP IDENTIFIED ===
Direction: LONG
Type: BOS Entry
Time: 10:30 UTC

=== CHECKLIST ===
✅ P(Long) = 64% ≥ 55%
✅ GSI = +58 ≥ +30
✅ Structure = Bullish (BOS @ 10:15)
✅ Liquidity = Support held @ 1842.50
✅ Flow = +65 ≥ +20
✅ Regime = Normal Trend
✅ RR = 1:2.3 ≥ 1.5
✅ Session = London
✅ Spread = 0.8 pips ≤ 2.0
✅ Conflicting Evidence = 0/8 families

All 10 requirements: PASS ✅

=== QUALITY ===
Score: 88/100 (Excellent)

=== ENTRY PLAN ===
Entry: 1848.50 (next bar open)
Stop: 1842.50 (-$6.00, 1.0 ATR)
Target: 1858.30 (+$9.80, 1.63 ATR)
RR: 1:1.63

Invalidation: 1841.00
Expiry: 11:30 UTC (10 bars)
```

### P.2 — Setup Rejected

```
=== SETUP REJECTED ===
Direction: SHORT
Time: 11:45 UTC

=== CHECKLIST ===
✅ P(Short) = 58% ≥ 55%
❌ GSI = -12 (required < -30)
✅ Structure = Bearish
❌ Flow = +15 (required < -20)
✅ Regime = Normal Trend
✅ RR = 1:1.8 ≥ 1.5
✅ Session = London
✅ Spread = 1.1 pips ≤ 2.0
✅ Conflicting Evidence = 2/8 families

Failed: 2 requirements (GSI, Flow)
Setup: REJECTED ❌
```

---

## Q — APPROVAL GATE

### The Phase 11 — Setup Engine specification is now complete.

**Summary of what is defined:**

1. ✅ 10-requirement checklist (Long and Short)
2. ✅ Probability alone insufficient (multi-factor validation)
3. ✅ Entry Trigger types (BOS, Retest, MSS, Candle)
4. ✅ Invalidation level (structure/liquidity-based)
5. ✅ Confirmation levels (L1–L4)
6. ✅ Retest detection and quality
7. ✅ Rejection detection and strength
8. ✅ Setup lifecycle (Identified → Triggered → Expired/Invalidated)
9. ✅ Setup quality scoring
10. ✅ Edge cases and handling
11. ✅ Bias prevention measures
12. ✅ Backtest requirements
13. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **10 Requirements:** Is this comprehensive enough? Too many?

2. **Min P(Action) = 0.55:** Appropriate threshold?

3. **Min GSI = ±30:** Meaningful directional evidence?

4. **Min RR = 1.5:** Ensures positive expectancy?

5. **Entry Trigger Types:** BOS, Retest, MSS, Candle — sufficient?

6. **Invalidation Based on Structure:** Acceptable approach?

7. **Setup Expiry = 10 bars:** Appropriate for M5?

8. **Setup Quality Score:** 0–100 with rating bands — acceptable?

---

**Please review and approve (or request modifications) before I proceed to Phase 12 — Risk Engine.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
