# PHASE 10 — PROBABILITY ENGINE

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
**Classification:** Pre-Implementation — No Code

---

## A — OBJECTIVE

Define the mathematical framework for **Probability Estimation** — combining all evidence into calibrated probability estimates for Long, Short, and No-Trade decisions.

This engine produces:
1. Evidence Family grouping (prevents double counting)
2. Bayesian probability model (Prior + Likelihood → Posterior)
3. Calibrated probabilities: P(Long), P(Short), P(No Trade)
4. Market Reaction Engine (post-news monitoring)
5. Anomaly detection (expected vs. actual market behavior)

**Critical Rule (Rule 5 — No Cosmetic Probabilities):**
- Every probability must have: source, sample, outcome definition, horizon, methodology, calibration
- "Probability = 80%" is invalid without these components

**Critical Rule (Rule 6 — No Double Counting):**
- Evidence is grouped into Families
- Within a Family, evidence is combined BEFORE cross-Family comparison
- Each Family contributes ONCE to the final probability

---

## B — INPUTS

### B.1 — Evidence Sources

| Evidence | Source | Phase | Family |
|----------|--------|-------|--------|
| Structure Score | Phase 2 | 2 | Structure |
| BOS/CHoCH | Phase 2 | 2 | Structure |
| Liquidity Score | Phase 3 | 3 | Liquidity |
| Sweep Detection | Phase 3 | 3 | Liquidity |
| Flow Score | Phase 4 | 4 | Flow |
| Absorption/Exhaustion | Phase 4 | 4 | Flow |
| Trend Score | Phase 5 | 5 | Trend/Momentum |
| Momentum Score | Phase 5 | 5 | Trend/Momentum |
| Volatility Score | Phase 5 | 5 | Volatility |
| GSI | Phase 6 | 6 | Composite |
| News Score | Phase 7 | 7 | Macro |
| Macro Score | Phase 7 | 7 | Macro |
| Historical Probability | Phase 8 | 8 | Historical |
| Regime | Phase 9 | 9 | Context |

### B.2 — Parameters

| Parameter | Initial Value | Description |
|-----------|--------------|-------------|
| `PRIOR_P_LONG` | 0.33 | Base rate for long trades |
| `PRIOR_P_SHORT` | 0.33 | Base rate for short trades |
| `PRIOR_P_NO_TRADE` | 0.34 | Base rate for no-trade |
| `EVIDENCE_WEIGHTS` | See Section D | Per-Family weights |
| `CALIBRATION_WINDOW` | 500 bars | Bars for calibration |
| `MIN_EVIDENCE_FOR_PROB` | 4 | Minimum families with evidence |
| `CONFIDENCE_THRESHOLD` | 0.55 | Min P(action) for signal |

---

## C — EVIDENCE FAMILIES

### C.1 — Family Definition

An **Evidence Family** groups related evidence that shares information content:

| Family | Members | Rationale |
|--------|---------|-----------|
| **Structure** | Structure Score, BOS, CHoCH, MSS | Price structure analysis |
| **Liquidity** | Liquidity Score, Sweep, Absorption | Level-based analysis |
| **Flow** | Flow Score, Absorption, Exhaustion | Volume-based analysis |
| **Trend/Momentum** | Trend Score, Momentum Score | Directional momentum |
| **Macro** | News Score, Macro Score, DXY, Yield | External factors |
| **Historical** | Historical Probability | Similarity-based |
| **Volatility** | Volatility Score, ATR | Dispersion context |
| **Context** | Regime, Session | Environmental context |

### C.2 — Why Families Matter

Without Families:
$$\text{GSI} = 0.25 \cdot S_{\text{struct}} + 0.15 \cdot S_{\text{trend}} + 0.15 \cdot S_{\text{mom}} + 0.20 \cdot S_{\text{flow}} + ...$$

**Problem:** GSI already combines Structure + Trend + Momentum + Flow. If we also use Structure Score, Trend Score, etc. independently, we **double count**.

With Families:
$$\text{Each Family} \rightarrow \text{One combined score} \rightarrow \text{Probability}$$

Each Family is counted **once**, regardless of how many members it has.

### C.3 — Family Combination Rules

For each Family $f$, combine members into a single family score:

$$S_f = \frac{\sum_{i \in \text{Family}_f} w_{f,i} \cdot S_{f,i}}{\sum_{i \in \text{Family}_f} w_{f,i}}$$

Where:
- $S_{f,i}$ = score of member $i$ in family $f$
- $w_{f,i}$ = weight of member $i$ within family $f$
- Weights sum to 1.0 within each family

### C.4 — Intra-Family Weights

| Family | Member | Intra-Family Weight |
|--------|--------|-------------------|
| Structure | Structure Score | 0.60 |
| Structure | BOS/CHoCH | 0.40 |
| Liquidity | Liquidity Score | 0.50 |
| Liquidity | Sweep Detection | 0.50 |
| Flow | Flow Score | 0.70 |
| Flow | Absorption/Exhaustion | 0.30 |
| Trend/Mom | Trend Score | 0.50 |
| Trend/Mom | Momentum Score | 0.50 |
| Macro | News Score | 0.50 |
| Macro | Macro Score (DXY/Yields) | 0.50 |
| Historical | Historical Probability | 1.00 (single member) |
| Volatility | Volatility Score | 1.00 (single member) |
| Context | Regime | 0.60 |
| Context | Session | 0.40 |

---

## D — BAYESIAN PROBABILITY MODEL

### D.1 — Prior Probabilities

Base rates before any evidence:

$$P_0(\text{Long}) = 0.33$$
$$P_0(\text{Short}) = 0.33$$
$$P_0(\text{NoTrade}) = 0.34$$

**Note:** These are **initial** priors. They will be calibrated from historical data (Section F).

### D.2 — Likelihood Ratios

For each Family $f$, compute the **likelihood ratio** — how much the evidence changes the probability:

$$\text{LR}_f = \frac{P(S_f | \text{Long})}{P(S_f | \text{NoTrade})}$$

This measures: "If the market is going Long, how likely is this Family's evidence?"

### D.3 — Likelihood Ratio from Score

Convert Family score to Likelihood Ratio:

$$\text{LR}_f = \exp\left(\frac{S_f}{100} \times \lambda_f\right)$$

Where:
- $S_f \in [-100, +100]$ = Family score
- $\lambda_f$ = sensitivity parameter (initial: 0.5 for all families)

**Interpretation:**
- $S_f = +100$: $\text{LR}_f = e^{0.5} \approx 1.65$ (strong evidence for Long)
- $S_f = 0$: $\text{LR}_f = e^0 = 1.0$ (no evidence)
- $S_f = -100$: $\text{LR}_f = e^{-0.5} \approx 0.61$ (strong evidence for Short)

### D.4 — Posterior Probability (Bayes' Theorem)

For Long direction:

$$P(\text{Long} | \mathbf{E}) = \frac{P_0(\text{Long}) \times \prod_{f} \text{LR}_{f,\text{long}}}{P_0(\text{Long}) \times \prod_{f} \text{LR}_{f,\text{long}} + P_0(\text{Short}) \times \prod_{f} \text{LR}_{f,\text{short}} + P_0(\text{NoTrade}) \times 1}$$

Where:
- $\text{LR}_{f,\text{long}}$ = likelihood ratio for Long given Family $f$ evidence
- $\text{LR}_{f,\text{short}}$ = likelihood ratio for Short given Family $f$ evidence

### D.5 — Simplified Form

For binary classification (Long vs. Not Long):

$$P(\text{Long} | \mathbf{E}) = \frac{1}{1 + \frac{P_0(\text{NotLong})}{P_0(\text{Long})} \times \prod_{f} \frac{1}{\text{LR}_{f,\text{long}}}}$$

### D.6 — Three-Class Output

$$P(\text{Long}) + P(\text{Short}) + P(\text{NoTrade}) = 1.0$$

The system outputs all three probabilities.

### D.7 — Family Direction Mapping

Not all Families have the same direction for Long vs. Short:

| Family | Positive Score → | Negative Score → |
|--------|-----------------|-----------------|
| Structure | Long evidence | Short evidence |
| Liquidity | Long evidence (support held) | Short evidence (resistance held) |
| Flow | Long evidence (buying pressure) | Short evidence (selling pressure) |
| Trend/Mom | Long evidence (bullish) | Short evidence (bearish) |
| Macro | Long evidence (weak USD) | Short evidence (strong USD) |
| Historical | Long evidence (P(Long) > P(Short)) | Short evidence |
| Volatility | Context (not directional) | Context |
| Context | Context (not directional) | Context |

**Non-directional Families** (Volatility, Context) modify the **confidence** but not the **direction**.

---

## E — EVIDENCE COMBINATION

### E.1 — Family Score to Probability Contribution

For each Family $f$ with score $S_f$:

$$\text{Contribution}_f = w_f \times \frac{S_f}{100}$$

Where $w_f$ = inter-Family weight.

### E.2 — Inter-Family Weights

| Family | Weight $w_f$ | Rationale |
|--------|-------------|-----------|
| Structure | 0.20 | Primary directional context |
| Flow | 0.18 | Volume confirmation |
| Trend/Momentum | 0.15 | Directional momentum |
| Macro | 0.15 | External factors |
| Historical | 0.15 | Empirical evidence |
| Liquidity | 0.10 | Level-based context |
| Volatility | 0.04 | Context modifier |
| Context | 0.03 | Environmental context |

$$\sum w_f = 1.00$$

### E.3 — Combined Evidence Score

$$\text{CombinedScore} = \sum_{f} w_f \times S_f$$

$$\text{CombinedScore} \in [-100, +100]$$

### E.4 — Probability from Combined Score

$$P(\text{Long}) = P_0(\text{Long}) \times \exp\left(\alpha \times \frac{\text{CombinedScore}}{100}\right)$$

$$P(\text{Short}) = P_0(\text{Short}) \times \exp\left(-\alpha \times \frac{\text{CombinedScore}}{100}\right)$$

$$P(\text{NoTrade}) = 1 - P(\text{Long}) - P(\text{Short})$$

Where $\alpha = 0.5$ (initial sensitivity parameter).

**Normalization:** Ensure $P(\text{Long}) + P(\text{Short}) + P(\text{NoTrade}) = 1.0$.

### E.5 — Confidence Score

$$\text{Confidence} = |P(\text{Long}) - P(\text{Short})|$$

$$\text{Confidence} \in [0, 1]$$

| Confidence | Level | Interpretation |
|-----------|-------|---------------|
| > 0.30 | High | Strong directional conviction |
| 0.15 – 0.30 | Moderate | Decent conviction |
| 0.05 – 0.15 | Low | Weak conviction |
| < 0.05 | Negligible | Insufficient evidence |

---

## F — CALIBRATION

### F.1 — Why Calibration Matters

Raw Bayesian probabilities may not match observed frequencies. Calibration ensures:

$$P(\text{Long}) = 0.70 \implies \text{Historically, 70% of similar cases resulted in Long wins}$$

### F.2 — Calibration Method

#### Platt Scaling (Logistic Calibration)

$$P_{\text{calibrated}}(\text{Long}) = \frac{1}{1 + \exp(a \cdot \text{CombinedScore} + b)}$$

Where $a$ and $b$ are learned from calibration data.

#### Isotonic Regression (Non-parametric)

$$P_{\text{calibrated}} = \text{IsotonicRegression}(P_{\text{raw}})$$

Maps raw probabilities to calibrated probabilities using monotonic function.

### F.3 — Calibration Data

- Separate from training and test data
- Minimum 500 bars for reliable calibration
- Re-calibrated every 500 bars (walk-forward)

### F.4 — Calibration Quality

$$\text{ECE} = \sum_{b=1}^{B} \frac{n_b}{N} \cdot |\text{predicted}_b - \text{observed}_b|$$

**Target:** ECE < 0.10.

### F.5 — Calibration Output

```
Calibration Status: Active
Method: Platt Scaling
ECE: 0.07
Last Calibrated: 2026-08-30 16:00 UTC
Calibration Window: 500 bars
```

---

## G — MARKET REACTION ENGINE

### G.1 — Objective

After a news event, monitor actual market behavior to detect:
- Confirmation (expected direction)
- Divergence (unexpected direction)
- Delayed reaction
- Overreaction → Reversal
- Anomaly

### G.2 — Monitoring Windows

After event release at $t_0$:

| Window | Time | What to Measure |
|--------|------|----------------|
| $W_1$ | $t_0 + 30\text{s}$ | Initial reaction |
| $W_2$ | $t_0 + 1\text{min}$ | First absorption |
| $W_3$ | $t_0 + 5\text{min}$ | First wave complete |
| $W_4$ | $t_0 + 15\text{min}$ | Secondary reaction |
| $W_5$ | $t_0 + 30\text{min}$ | Digestion complete |

### G.3 — Monitored Instruments

| Instrument | Source | Relevance |
|-----------|--------|-----------|
| Gold (XAUUSD) | MT5 | Primary |
| DXY | Macro source | USD strength |
| US 2Y Yield | Macro source | Short-term rate expectation |
| US 10Y Yield | Macro source | Long-term rate expectation |

### G.4 — Reaction Metrics

For each instrument $i$ at window $W_k$:

$$\Delta_i(k) = \frac{\text{Price}_i(W_k) - \text{Price}_i(t_0)}{\text{Price}_i(t_0)} \times 100$$

### G.5 — Expected Direction (from Phase 7)

$$\text{Expected} = [\text{Gold}_{\text{dir}}, \text{DXY}_{\text{dir}}, \text{Yield}_{\text{dir}}]$$

From Phase 7 directional mapping.

### G.6 — Actual Direction

$$\text{Actual}(k) = [\text{sign}(\Delta_{\text{Gold}}(k)), \text{sign}(\Delta_{\text{DXY}}(k)), \text{sign}(\Delta_{\text{Yield}}(k))]$$

### G.7 — Reaction Classification

#### Confirmation

$$\text{Confirmation} \iff \text{Actual}(k) = \text{Expected} \quad \forall \, i \in \{\text{Gold}, \text{DXY}, \text{Yield}\}$$

**Interpretation:** Market moved in expected direction across all instruments.

#### Divergence

$$\text{Divergence} \iff \exists \, i: \text{Actual}_i(k) \neq \text{Expected}_i$$

**Sub-types:**
- **Safe Haven Divergence:** Gold ↑ and DXY ↑ (both rising — risk-off)
- **Yield Divergence:** Gold ↓ but Yields ↓ (unusual — yield fall should support gold)
- **Partial Divergence:** Some instruments align, others don't

#### Delayed Reaction

$$\text{DelayedReaction} \iff \text{Actual}(W_1) \neq \text{Expected} \wedge \text{Actual}(W_3) = \text{Expected}$$

**Interpretation:** Initial reaction was wrong, but market corrected within 5 minutes.

#### Overreaction → Reversal

$$\text{Overreaction} \iff \text{sign}(\Delta(W_1)) \neq \text{sign}(\Delta(W_3))$$

**Interpretation:** Initial move was excessive and reversed.

#### No Reaction

$$\text{NoReaction} \iff |\Delta_{\text{Gold}}(W_3)| < \text{threshold}$$

Where threshold = 0.10% (10 pips for XAUUSD).

**Interpretation:** Data was fully anticipated; no market impact.

### G.8 — Anomaly Score

$$\text{AnomalyScore} = \sum_{i} |\text{Expected}_i - \text{Actual}_i(k)| \times \text{Magnitude}_i$$

Where $\text{Magnitude}_i = |\Delta_i(k)|$.

$$\text{AnomalyScore} \in [0, 300]$$

| Score | Classification |
|-------|---------------|
| > 150 | Major Anomaly — investigate |
| 75 – 150 | Moderate Anomaly — note |
| < 75 | Normal — no action |

### G.9 — Anomaly Logging

Every anomaly is stored with:
- Event details (name, time, surprise Z-score)
- Expected vs. actual directions per instrument
- Magnitude per instrument
- Anomaly score
- Market context (regime, GSI at time of event)
- Subsequent price action (next 30 min)

---

## H — PROBABILITY OUTPUT FORMAT

### H.1 — Standard Output

```
=== PROBABILITY ENGINE ===
Combined Score: +58.3
Confidence: 0.34 (Moderate)

=== EVIDENCE FAMILIES ===
Structure:     +72 (w=0.20) → +14.4
Flow:          +65 (w=0.18) → +11.7
Trend/Mom:     +48 (w=0.15) → +7.2
Macro:         +35 (w=0.15) → +5.3
Historical:    +42 (w=0.15) → +6.3
Liquidity:     +55 (w=0.10) → +5.5
Volatility:    -15 (w=0.04) → -0.6
Context:       +40 (w=0.03) → +1.2
─────────────────────────────
Combined:              → +51.0 → adjusted to +58.3

=== CALIBRATED PROBABILITIES ===
P(Long):   64% (calibrated, ECE=0.07)
P(Short):  21% (calibrated)
P(NoTrade): 15% (calibrated)

=== SAMPLE QUALITY ===
Families with evidence: 8/8
Min family score: -15 (Volatility)
Max family score: +72 (Structure)
Evidence alignment: 7/8 bullish
```

### H.2 — No-Trade Probability Enhancement

$P(\text{NoTrade})$ is enhanced by:

$$P(\text{NoTrade})_{\text{enhanced}} = P(\text{NoTrade})_{\text{base}} + \Delta_{\text{regime}} + \Delta_{\text{news}} + \Delta_{\text{conflict}}$$

Where:
- $\Delta_{\text{regime}}$ = regime-specific no-trade bonus (Phase 9)
- $\Delta_{\text{news}}$ = news blocking bonus (Phase 7)
- $\Delta_{\text{conflict}}$ = evidence conflict penalty

---

## I — EDGE CASES

### I.1 — Insufficient Evidence

| Scenario | Handling |
|----------|----------|
| < 4 families with evidence | Flag `insufficient_evidence`; do not output probability |
| All families neutral | P(Long) ≈ P(Short) ≈ 33%; P(NoTrade) increased |
| One family extreme, others neutral | Moderate probability; low confidence |

### I.2 — Conflicting Evidence

| Scenario | Handling |
|----------|----------|
| Structure bullish + Flow bearish | Conflict detected; reduce confidence |
| Macro bearish + Historical bullish | Weight by family importance |
| 4 families bull, 4 families bear | High conflict; increase P(NoTrade) |

### I.3 — Calibration Failure

| Scenario | Handling |
|----------|----------|
| ECE > 0.15 | Flag `calibration_poor`; reduce confidence |
| Calibration data insufficient | Use raw probabilities with warning |
| Calibration drift detected | Trigger re-calibration |

---

## J — BIAS PREVENTION

### J.1 — Look-Ahead Bias

**Prevention:**
1. All evidence from confirmed bars only
2. Calibration from past data only
3. Walk-forward probability computation

### J.2 — Overfitting

**Prevention:**
1. Bayesian model with regularized priors
2. Calibration on separate dataset
3. Minimum evidence requirements
4. Walk-forward validation

### J.3 — Double Counting

**Prevention:**
1. Evidence Families group related evidence
2. Each Family counted ONCE
3. Inter-Family weights account for overlap
4. GSI is NOT used directly (its components are in Families)

### J.4 — Cosmetic Probabilities

**Prevention:**
1. Every probability output includes: sample size, calibration status, ECE
2. Probability blocked if sample < minimum
3. All methodology documented

---

## K — BACKTESTABILITY

### K.1 — Backtest Requirements

| Requirement | Implementation |
|-------------|---------------|
| Evidence from confirmed bars | Strict temporal ordering |
| Calibration from past data | Walk-forward calibration |
| No future information | Bayesian update uses only past evidence |
| Anomaly detection | Strict temporal ordering |

### K.2 — Walk-Forward Probability

```
Historical Data
    ↓
Training Window → Learn priors, calibration
    ↓
Validation Window → Test probability accuracy
    ↓
Test Window → Live probability computation
    ↓
Each bar: Compute evidence → Bayesian update → Calibrate → Output
```

---

## L — WHAT IS FIXED

### L.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Evidence Families | 8 | Comprehensive, no double counting |
| Prior Probabilities | 33/33/34 | Neutral baseline |
| Inter-Family Weights | See D.2 | Structure + Flow primary |
| Intra-Family Weights | See C.4 | Per-family member importance |
| Sensitivity Parameter α | 0.5 | Moderate response to evidence |
| Calibration Method | Platt Scaling | Simple, effective |
| Calibration Window | 500 bars | Sufficient for reliability |
| Min Evidence Families | 4 | Minimum for meaningful probability |
| Confidence Threshold | 0.55 | Min P(action) for signal |
| Reaction Windows | 30s, 1m, 5m, 15m, 30m | From Phase 7 |

### L.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal prior probabilities | Phase 17 (from historical base rates) |
| Inter-Family weight optimization | Phase 17 |
| Sensitivity parameter α | Phase 17 |
| Calibration recalibration frequency | Phase 17 |
| Anomaly thresholds | Phase 17 |
| Family membership optimization | Phase 17 |

---

## M — WHAT REQUIRES TESTING

### M.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | Bayesian model outperforms simple averaging | Backtest both | Bayesian has better calibration |
| H2 | 8 Families prevent double counting | Check correlation between Family scores | ρ < 0.4 between Families |
| H3 | Calibration improves probability accuracy | Compare calibrated vs. uncalibrated | ECE reduced by > 50% |
| H4 | 4+ families needed for reliable probability | Test minimum family count | Accuracy improves with more families |
| H5 | Market Reaction Anomaly predicts future moves | Statistical test | Anomalies precede unusual price action |
| H6 | Historical Probability adds value | Ablation test | Removing Historical reduces accuracy |

### M.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Should GSI be used directly or decomposed? | Test both approaches |
| Q2 | Is Platt Scaling better than Isotonic? | Compare ECE |
| Q3 | How often to recalibrate? | Test [250, 500, 1000] bars |
| Q4 | Should anomaly detection affect probability? | Test anomaly-adjusted probabilities |

---

## N — OUTPUT SCHEMA

### N.1 — Probability Output per Bar

```python
@dataclass(frozen=True)
class ProbabilityOutput:
    """Probability Engine output for a single bar."""
    timestamp: datetime
    
    # Evidence Families
    family_scores: dict[str, float]      # Score per family
    family_evidence: dict[str, bool]     # Whether family has evidence
    families_active: int                 # Count of active families
    
    # Combined
    combined_score: float                # [-100, +100]
    combined_direction: str              # "bullish", "bearish", "neutral"
    
    # Probabilities
    p_long: float                        # [0, 1]
    p_short: float                       # [0, 1]
    p_no_trade: float                    # [0, 1]
    confidence: float                    # |P(Long) - P(Short)|
    
    # Calibration
    calibrated: bool
    ece_score: float | None
    calibration_method: str | None
    
    # Decision
    recommended_action: str              # "long", "short", "no_trade"
    action_confidence: float             # P(recommended action)
    
    # Provenance
    provenance: DataProvenance
```

### N.2 — Market Reaction Output

```python
@dataclass(frozen=True)
class MarketReactionOutput:
    """Market Reaction Engine output for a news event."""
    event: NewsEvent
    
    # Reactions per window
    reactions: dict[str, ReactionWindow]  # "30s", "1m", "5m", "15m", "30m"
    
    # Classification
    reaction_type: str                    # "confirmation", "divergence", etc.
    anomaly_score: float                  # [0, 300]
    anomaly_classification: str           # "major", "moderate", "normal"
    
    # Expected vs Actual
    expected_direction: dict[str, int]    # Per instrument
    actual_direction: dict[str, int]      # Per instrument at W_3
    
    # Provenance
    provenance: DataProvenance
```

### N.3 — Reaction Window Schema

```python
@dataclass(frozen=True)
class ReactionWindow:
    """Reaction at a specific time window."""
    window: str                          # "30s", "1m", "5m", "15m", "30m"
    delta_gold: float                    # % change in Gold
    delta_dxy: float                     # % change in DXY
    delta_yield: float                   # % change in 10Y Yield
    gold_direction: int                  # +1, -1, 0
    dxy_direction: int
    yield_direction: int
    is_confirmed: bool                   # Matches expected direction
    is_divergence: bool                  # Partially unexpected
    is_overreaction: bool                # Initial move reversed
```

---

## O — DECISION OUTPUT

### O.1 — Per-Bar Probability

```
=== PROBABILITY ENGINE v1.0 ===
Combined Score: +58.3 (Bullish)
Confidence: 0.34 (Moderate)

=== EVIDENCE FAMILIES ===
Structure:    +72 ████████████████░░░░ (w=0.20)
Flow:         +65 ██████████████░░░░░░ (w=0.18)
Trend/Mom:    +48 ██████████░░░░░░░░░░ (w=0.15)
Macro:        +35 ███████░░░░░░░░░░░░░ (w=0.15)
Historical:   +42 █████████░░░░░░░░░░░ (w=0.15)
Liquidity:    +55 ███████████░░░░░░░░░ (w=0.10)
Volatility:   -15 ███░░░░░░░░░░░░░░░░░ (w=0.04)
Context:      +40 ████████░░░░░░░░░░░░ (w=0.03)

=== CALIBRATED PROBABILITIES ===
P(Long):    64% ████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░
P(Short):   21% ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
P(NoTrade): 15% ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

Calibration: Active (ECE=0.07, Platt Scaling)
Families Active: 8/8

=== RECOMMENDATION ===
Action: LONG
Confidence: 64%
Threshold Met: Yes (64% > 55%)
```

### O.2 — Market Reaction Event

```
=== MARKET REACTION: CPI m/m ===
Released: 13:30 UTC
Surprise: +1.35σ (Positive)

=== EXPECTED DIRECTION ===
Gold: ↓ | DXY: ↑ | Yield: ↑

=== ACTUAL REACTION ===
@ 30s:  Gold -5 pips  | DXY +0.08% | Yield +0.01%  ✅ Confirm
@ 1m:   Gold -12 pips | DXY +0.15% | Yield +0.02%  ✅ Confirm
@ 5m:   Gold -18 pips | DXY +0.22% | Yield +0.03%  ✅ Confirm
@ 15m:  Gold -15 pips | DXY +0.18% | Yield +0.02%  ✅ Confirm
@ 30m:  Gold -10 pips | DXY +0.12% | Yield +0.01%  ✅ Confirm

Classification: CONFIRMATION
Anomaly Score: 12 (Normal)
No divergence detected.
```

---

## P — APPROVAL GATE

### The Phase 10 — Probability Engine specification is now complete.

**Summary of what is defined:**

1. ✅ 8 Evidence Families (no double counting)
2. ✅ Intra-Family combination rules
3. ✅ Inter-Family weights
4. ✅ Bayesian probability model (Prior + Likelihood → Posterior)
5. ✅ P(Long), P(Short), P(No Trade) output
6. ✅ Confidence scoring
7. ✅ Calibration methodology (Platt Scaling)
8. ✅ Market Reaction Engine (5 windows, 4 instruments)
9. ✅ Reaction classification (Confirmation, Divergence, Anomaly)
10. ✅ Anomaly detection and scoring
11. ✅ Edge cases and handling
12. ✅ Bias prevention (Rule 5, Rule 6 compliance)
13. ✅ Backtest requirements
14. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **8 Evidence Families:** Is this grouping correct? Any overlaps remaining?

2. **Inter-Family Weights:** Structure 20%, Flow 18%, Trend/Mom 15%, Macro 15%, Historical 15%, Liquidity 10%, Volatility 4%, Context 3% — acceptable?

3. **Bayesian Model:** Prior + Likelihood → Posterior — is this the right approach?

4. **Calibration Method:** Platt Scaling — appropriate?

5. **Market Reaction Windows:** 30s, 1m, 5m, 15m, 30m — same as Phase 7?

6. **Anomaly Scoring:** Is the anomaly score formula appropriate?

7. **Min Evidence Families:** 4 minimum for probability output — sufficient?

8. **Confidence Threshold:** 0.55 minimum P(action) — appropriate?

---

**Please review and approve (or request modifications) before I proceed to Phase 11 — Setup Engine.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
