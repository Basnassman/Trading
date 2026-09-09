# PHASE 8 — HISTORICAL ENGINE

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
**Status:** PENDING APPROVAL
| Classification | Pre-Implementation — No Code |

---

## A — OBJECTIVE

Define the mathematical framework for **Historical Similarity Analysis** — comparing the current market state to historical states to estimate the probability of future outcomes.

This engine produces:
1. Feature Vector construction (current state representation)
2. Historical similarity computation (distance metrics)
3. K-Nearest Neighbor retrieval
4. Historical probability estimation
5. Outcome tracking and calibration

**Scope Boundary:**
- This engine uses **all prior engine outputs** as features.
- It does **not** use future data (strict temporal rules).
- Probability estimation follows Rule 5 (no cosmetic probabilities).

---

## B — INPUTS

### B.1 — Required Data (Feature Vector Components)

| Feature | Source | Range | Phase |
|---------|--------|-------|-------|
| GSI | Phase 6 | [-100, +100] | 6 |
| Structure Score | Phase 2 | [-100, +100] | 2 |
| Liquidity Score | Phase 3 | [-100, +100] | 3 |
| Flow Score | Phase 4 | [-100, +100] | 4 |
| Trend Score | Phase 5 | [-100, +100] | 5 |
| Momentum Score | Phase 5 | [-100, +100] | 5 |
| Volatility Score | Phase 5 | [-100, +100] | 5 |
| ATR (normalized) | Phase 5 | [0, +∞) | 5 |
| DXY Score | Phase 7 | [-100, +100] | 7 |
| Yield Score | Phase 7 | [-100, +100] | 7 |
| News Score | Phase 7 | [-100, +100] | 7 |
| Session | Phase 1 | Categorical | 1 |
| Distance to Nearest Liquidity | Phase 3 | [0, +∞) | 3 |
| Market Regime | Phase 9 | Categorical | 9 |

### B.2 — Parameters

| Parameter | Initial Value | Description |
|-----------|--------------|-------------|
| `K_NEIGHBORS` | 250 | Minimum similar cases for probability |
| `K_SEARCH` | 500 | Number of neighbors to search |
| `SIMILARITY_THRESHOLD` | 0.80 | Minimum similarity score to include |
| `OUTCOME_HORIZON` | 15 | Bars (M5) for outcome measurement |
| `OUTCOME_TARGET_ATR` | 2.0 | ATR multiplier for target |
| `OUTCOME_STOP_ATR` | 1.0 | ATR multiplier for stop |
| `NORMALIZATION_METHOD` | "robust" | RobustScaler (median/IQR) |
| `DISTANCE_METRIC` | "mahalanobis" | Primary distance metric |

---

## C — FEATURE VECTOR CONSTRUCTION

### C.1 — Vector Definition

For each bar $t$, construct the feature vector:

$$\mathbf{x}_t = \begin{bmatrix}
\text{GSI}_t \\
\text{Struct}_t \\
\text{Liquidity}_t \\
\text{Flow}_t \\
\text{Trend}_t \\
\text{Momentum}_t \\
\text{Volatility}_t \\
\text{ATR}_{\text{norm},t} \\
\text{DXY}_t \\
\text{Yield}_t \\
\text{News}_t \\
\text{Session}_{\text{encoded},t} \\
\text{DistLiquidity}_t \\
\text{Regime}_{\text{encoded},t}
\end{bmatrix}$$

$$\mathbf{x}_t \in \mathbb{R}^{14}$$

### C.2 — Feature Normalization

Raw features have different scales. Normalization is required before distance computation.

#### Robust Scaling (Recommended)

$$x_{\text{norm},i} = \frac{x_i - \text{median}_i}{\text{IQR}_i}$$

Where:
- $\text{median}_i$ = median of feature $i$ over historical data
- $\text{IQR}_i$ = interquartile range (Q3 - Q1) of feature $i$

**Why Robust Scaling?**
- Resistant to outliers (unlike StandardScaler)
- Handles skewed distributions (common in financial data)
- Preserves relative distances

#### Alternative: Z-Score Standardization

$$x_{\text{norm},i} = \frac{x_i - \mu_i}{\sigma_i}$$

**Risk:** Sensitive to outliers and non-normal distributions.

#### Alternative: Min-Max Scaling

$$x_{\text{norm},i} = \frac{x_i - \min_i}{\max_i - \min_i}$$

**Risk:** Sensitive to extreme values; compresses normal data.

### C.3 — Categorical Encoding

#### Session Encoding

| Session | Encoding |
|---------|----------|
| Asian | 0.0 |
| London | 0.33 |
| Overlap | 0.67 |
| New York | 1.0 |
| OffSession | -1.0 (flag) |

**Alternative:** One-hot encoding (5 binary features) — increases dimensionality but avoids ordinal assumption.

#### Regime Encoding

| Regime | Encoding |
|--------|----------|
| Normal Trend | 0.0 |
| Range | 0.25 |
| Breakout | 0.50 |
| High Volatility | 0.75 |
| Liquidity Sweep | 1.0 |
| News | -0.25 |
| Post-News | -0.50 |
| Low Liquidity | -0.75 |
| Transition | -1.0 |

**Alternative:** One-hot encoding (9 binary features).

### C.4 — Feature Selection Rationale

| Feature | Why Included | Potential Overlap |
|---------|-------------|-------------------|
| GSI | Composite of Structure/Trend/Mom/Flow | Overlaps with individual components |
| Structure | Primary directional context | Overlaps with GSI |
| Liquidity | Level-based context | Independent |
| Flow | Volume-based context | Independent |
| Trend | Smoothed direction | Overlaps with Structure |
| Momentum | Rate of change | Independent |
| Volatility | Dispersion context | Independent |
| ATR | Absolute volatility | Overlaps with Volatility Score |
| DXY | Dollar strength | Independent |
| Yield | Interest rate environment | Independent |
| News | Event impact | Independent |
| Session | Time-of-day context | Independent |
| DistLiquidity | Proximity to levels | Independent |
| Regime | Market state | Independent |

**Overlap Note:** GSI overlaps with Structure, Trend, Flow, and Momentum. This is **by design** — GSI is a composite, and including both composite and components allows the distance metric to weigh them appropriately.

### C.5 — Missing Feature Handling

If a feature is unavailable at time $t$:

$$x_{t,i} = \text{median}_i \quad \text{(impute with historical median)}$$

**Flag:** `feature_missing: [list of missing features]`

**Risk:** Imputation reduces discrimination. If > 3 features are missing, the bar is excluded from similarity analysis.

---

## D — HISTORICAL SIMILARITY

### D.1 — Distance Metrics Comparison

#### Euclidean Distance

$$d_{\text{eucl}}(\mathbf{x}, \mathbf{y}) = \sqrt{\sum_{i=1}^{n} (x_i - y_i)^2}$$

**Properties:**
- Simple, intuitive
- Sensitive to scale (requires normalization)
- Assumes features are independent
- Sensitive to outliers

**Suitability for Financial Data:** Moderate — doesn't account for correlations between features.

#### Manhattan Distance

$$d_{\text{manh}}(\mathbf{x}, \mathbf{y}) = \sum_{i=1}^{n} |x_i - y_i|$$

**Properties:**
- Less sensitive to outliers than Euclidean
- Still assumes feature independence
- Robust in high dimensions

**Suitability for Financial Data:** Moderate — useful when features have different noise characteristics.

#### Mahalanobis Distance

$$d_{\text{mahal}}(\mathbf{x}, \mathbf{y}) = \sqrt{(\mathbf{x} - \mathbf{y})^T \mathbf{S}^{-1} (\mathbf{x} - \mathbf{y})}$$

Where $\mathbf{S}$ = covariance matrix of the features.

**Properties:**
- Accounts for correlations between features
- Scale-invariant (no normalization needed, but recommended)
- Sensitive to outliers (covariance estimation)
- Requires $\mathbf{S}$ to be positive definite

**Suitability for Financial Data:** **Best** — financial features are correlated (e.g., Trend and Structure, DXY and Yield).

#### KNN (K-Nearest Neighbors)

Not a distance metric per se, but a retrieval method using any distance metric.

$$\mathcal{N}_K(\mathbf{x}) = \text{K nearest historical vectors to } \mathbf{x}$$

**Properties:**
- Non-parametric (no distributional assumptions)
- Adapts to local structure
- Computationally expensive for large datasets
- Curse of dimensionality (mitigated by 14 features)

### D.2 — Recommended Metric: Mahalanobis Distance

**Rationale:**
1. Financial features are **correlated** (e.g., GSI and Structure, DXY and Yield)
2. Mahalanobis **decorrelates** features automatically via covariance matrix
3. It's the natural metric for multivariate normal-like distributions
4. It handles different feature scales without explicit normalization

**Caveat:**
- Covariance matrix $\mathbf{S}$ must be estimated from historical data
- Requires $\mathbf{S}$ to be invertible (positive definite)
- If $\mathbf{S}$ is singular (e.g., perfectly correlated features), fall back to Euclidean

### D.3 — Covariance Matrix Estimation

$$\mathbf{S} = \frac{1}{N-1} \sum_{i=1}^{N} (\mathbf{x}_i - \bar{\mathbf{x}})(\mathbf{x}_i - \bar{\mathbf{x}})^T$$

Where:
- $N$ = number of historical observations
- $\bar{\mathbf{x}}$ = mean feature vector

**Regularization (if needed):**

$$\mathbf{S}_{\text{reg}} = \mathbf{S} + \lambda \mathbf{I}$$

Where $\lambda = 0.01$ (initial regularization parameter).

### D.4 — Similarity Score

Convert distance to similarity:

$$\text{similarity}(\mathbf{x}, \mathbf{y}) = \exp\left(-\frac{d(\mathbf{x}, \mathbf{y})^2}{2\sigma^2}\right)$$

Where:
- $d$ = Mahalanobis distance
- $\sigma$ = bandwidth parameter (initial: median distance of K nearest neighbors)

$$\text{similarity} \in [0, 1]$$

- 1.0 = identical states
- 0.0 = completely dissimilar

---

## E — K-NEAREST NEIGHBOR RETRIEVAL

### E.1 — Algorithm

```
INPUT: Current vector x_t, Historical dataset X, K_SEARCH
OUTPUT: K nearest neighbors N_K

1. Compute distance from x_t to all x_i in X
2. Sort by distance (ascending)
3. Return top K_SEARCH neighbors
4. Filter by similarity threshold (≥ 0.80)
5. If filtered set < K_NEIGHBORS (250):
   - Flag as "insufficient_similar_cases"
   - Expand search or relax threshold
```

### E.2 — Temporal Constraints

**Critical Rule (Rule 4 — No Look-Ahead):**

Historical neighbors must be from **before** the current bar:

$$\mathcal{N}_K(\mathbf{x}_t) = \{ \mathbf{x}_i : i < t \wedge d(\mathbf{x}_t, \mathbf{x}_i) \leq d_{\text{threshold}} \}$$

**Additional Constraints:**
1. No neighbor from the same day (to avoid autocorrelation)
2. Minimum 1-day gap between neighbors
3. Neighbors from different market regimes are preferred (diversity)

### E.3 — Neighbor Quality Metrics

| Metric | Description | Target |
|--------|-----------|--------|
| Average Similarity | Mean similarity of K neighbors | > 0.80 |
| Regime Diversity | Fraction of distinct regimes in neighbors | > 0.50 |
| Temporal Spread | Time span of neighbors | > 1 year |
| Feature Variance | Variance of each feature across neighbors | Low = consistent |

---

## F — HISTORICAL PROBABILITY

### F.1 — Outcome Definition

For each historical neighbor $\mathbf{x}_i$, compute the **outcome**:

$$\text{Outcome}_i = \begin{cases}
\text{LONG\_WIN} & \text{if price reached target before stop (long)} \\
\text{LONG\_LOSS} & \text{if price reached stop before target (long)} \\
\text{SHORT\_WIN} & \text{if price reached target before stop (short)} \\
\text{SHORT\_LOSS} & \text{if price reached stop before target (short)} \\
\text{NO\_TRADE} & \text{if neither target nor stop reached within horizon}
\end{cases}$$

### F.2 — Outcome Parameters

| Parameter | Definition | Initial Value |
|-----------|-----------|--------------|
| Horizon | Maximum bars to wait for outcome | 15 bars (75 min on M5) |
| Target | Profit target (ATR-based) | 2.0 × ATR₁₄ |
| Stop | Stop loss (ATR-based) | 1.0 × ATR₁₄ |

### F.3 — Outcome Computation

For a long trade entered at $C_i$:

$$\text{Target}_i = C_i + \text{Target}_{\text{ATR}} \times \text{ATR}_{14,i}$$

$$\text{Stop}_i = C_i - \text{Stop}_{\text{ATR}} \times \text{ATR}_{14,i}$$

For each subsequent bar $j \in \{i+1, ..., i + \text{Horizon}\}$:

$$\text{Outcome}_i = \begin{cases}
\text{LONG\_WIN} & \text{if } \exists j: H_j \geq \text{Target}_i \wedge \forall k < j: L_k > \text{Stop}_i \\
\text{LONG\_LOSS} & \text{if } \exists j: L_j \leq \text{Stop}_i \wedge \forall k < j: H_k < \text{Target}_i \\
\text{NO\_TRADE} & \text{if } \forall j \in \{i+1, ..., i+H\}: \text{neither reached}
\end{cases}$$

### F.4 — Probability Computation

Given $K$ historical neighbors with outcomes:

$$P(\text{LONG}) = \frac{\text{Count}(\text{LONG\_WIN})}{K}$$

$$P(\text{SHORT}) = \frac{\text{Count}(\text{SHORT\_WIN})}{K}$$

$$P(\text{NO\_TRADE}) = \frac{\text{Count}(\text{NO\_TRADE})}{K}$$

$$P(\text{LONG}) + P(\text{SHORT}) + P(\text{NO\_TRADE}) = 1.0$$

### F.5 — Minimum Sample Requirement (Rule 5 Compliance)

$$K \geq K_{\text{NEIGHBORS}} = 250$$

**Rationale:**
- 250 samples provides ±6% margin of error at 95% confidence
- Below 250: Probability is flagged as `insufficient_sample`
- The system does **not** output probability if $K < 250$

### F.6 — Probability Calibration

Raw frequencies may not be well-calibrated. Apply **Platt Scaling**:

$$P_{\text{calibrated}}(\text{LONG}) = \frac{1}{1 + \exp(a \cdot P_{\text{raw}}(\text{LONG}) + b)}$$

Where $a$ and $b$ are learned from a calibration dataset (separate from main data).

**Calibration Quality:** ECE < 0.10 (from Phase 6 methodology).

---

## G — WHAT MAKES A PROBABILITY STATEMENT VALID

### G.1 — Rule 5 Compliance Checklist

| Requirement | How Met |
|-------------|---------|
| Sample size known | $K \geq 250$ enforced |
| Cases actually similar | Similarity threshold ≥ 0.80 |
| Outcome defined | LONG_WIN / LONG_LOSS / SHORT_WIN / SHORT_LOSS / NO_TRADE |
| No leakage | Temporal constraints enforced |
| Probability calibrated | Platt Scaling applied |
| Horizon defined | 15 bars (M5) |
| Methodology documented | This specification |

### G.2 — Invalid Probability Statements

The system must **never** output:
- "Probability = 80%" without sample size
- "Probability = 80%" with $K < 250$
- "Probability = 80%" with average similarity < 0.80
- "Probability = 80%" using future data
- "Probability = 80%" without calibration

### G.3 — Valid Probability Statement Format

```
Historical Probability:
  P(Long): 62% (K=312, avg_similarity=0.84, calibrated)
  P(Short): 23% (K=312, avg_similarity=0.84, calibrated)
  P(No Trade): 15% (K=312, avg_similarity=0.84, calibrated)
  
  Horizon: 15 bars (75 min)
  Target: 2.0 ATR | Stop: 1.0 ATR
  Sample: 312 similar cases
  Avg Similarity: 0.84
  Regime Diversity: 0.65
  Calibration ECE: 0.07
```

---

## H — EDGE CASES

### H.1 — Insufficient Similar Cases

| Scenario | Handling |
|----------|----------|
| $K < 250$ after filtering | Flag `insufficient_sample`; do not output probability |
| $K < 250$ even with relaxed threshold | Flag `low_confidence`; reduce weight in GSI |
| No similar cases ($K = 0$) | Historical probability = unavailable |

### H.2 — Covariance Matrix Issues

| Scenario | Handling |
|----------|----------|
| $\mathbf{S}$ is singular | Fall back to Euclidean distance |
| $\mathbf{S}$ is ill-conditioned | Apply regularization ($\lambda = 0.01$) |
| Few features available | Reduce feature dimension |

### H.3 — Temporal Clustering

| Scenario | Handling |
|----------|----------|
| All neighbors from same month | Apply temporal diversity penalty |
| Neighbors too close in time | Enforce minimum 1-day gap |

### H.4 — Outcome Ambiguity

| Scenario | Handling |
|----------|----------|
| Both target and stop reached in same bar | Use bar order: check stop first (conservative) |
| Neither reached within horizon | Mark as NO_TRADE |
| Target reached exactly at horizon | Mark as WIN |

---

## I — BIAS PREVENTION

### I.1 — Look-Ahead Bias

**Prevention:**
1. All neighbors from before current bar ($i < t$)
2. Outcome computed using only future bars relative to neighbor entry
3. Current state features computed from confirmed bars only

### I.2 — Data Leakage

**Prevention:**
1. Temporal split: training data < test data
2. Covariance matrix estimated from training period only
3. Calibration learned from separate calibration set

### I.3 — Survivorship Bias

**Prevention:**
1. Include ALL historical periods, including losing streaks
2. Don't cherry-pick "good"相似 situations
3. Outcome includes NO_TRADE (not just wins/losses)

### I.4 — Overfitting

**Prevention:**
1. Walk-forward validation (not in-sample optimization)
2. Regularization on covariance matrix
3. Minimum sample requirement ($K \geq 250$)
4. Calibrated probabilities (not raw frequencies)

---

## J — BACKTESTABILITY

### J.1 — Backtest Requirements

| Requirement | Implementation |
|-------------|---------------|
| Temporal ordering | Neighbors only from before current bar |
| Feature computation | Use only confirmed bar data |
| Outcome computation | Strict horizon and target/stop rules |
| Covariance estimation | From training window only |
| Calibration | From separate calibration set |

### J.2 — Walk-Forward Implementation

```
Full Historical Data
    ↓
├── Training Window (years 1–5)
│   ├── Feature computation
│   ├── Covariance estimation
│   ├── Calibration learning
│   └── Build neighbor database
│
├── Validation Window (year 6)
│   ├── Test probability accuracy
│   ├── Measure calibration (ECE)
│   └── Adjust parameters
│
└── Test Window (year 7+)
    ├── Live probability computation
    ├── Out-of-sample validation
    └── Performance tracking
```

### J.3 — Backtest Data Flow

```
Historical OHLCV + All Engine Outputs
    ↓
Feature Vector Construction (per bar)
    ↓
Normalization (RobustScaler from training)
    ↓
Covariance Matrix Estimation (from training)
    ↓
Neighbor Database Construction
    ↓
For each bar t in test period:
    ├── Compute x_t
    ├── Find K nearest neighbors (temporal constraint)
    ├── Compute outcomes for neighbors
    ├── Compute probability
    ├── Apply calibration
    └── Store result
    ↓
Evaluate: Calibration, Accuracy, Profitability
```

---

## K — WHAT IS FIXED

### K.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Feature Vector | 14 dimensions | Comprehensive coverage |
| Distance Metric | Mahalanobis | Accounts for correlations |
| K (minimum) | 250 | Statistical significance |
| K (search) | 500 | Enough candidates |
| Similarity Threshold | 0.80 | High similarity required |
| Outcome Horizon | 15 bars (M5) | ~75 minutes |
| Target | 2.0 ATR | Reasonable profit target |
| Stop | 1.0 ATR | Conservative stop |
| Normalization | RobustScaler | Outlier-resistant |
| Calibration | Platt Scaling | Probability calibration |

### K.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal K | Phase 17 (Optimization) |
| Optimal similarity threshold | Phase 17 |
| Target/Stop ATR multipliers | Phase 17 |
| Outcome horizon | Phase 17 |
| Feature selection optimization | Phase 17 |
| Covariance regularization λ | Phase 17 |
| Session/Regime encoding | Phase 17 |

---

## L — WHAT REQUIRES TESTING

### L.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | Mahalanobis outperforms Euclidean | Compare prediction accuracy | Mahalanobis > Euclidean |
| H2 | 250 neighbors is sufficient | Sample size sensitivity | Accuracy plateaus at ~200–300 |
| H3 | Similarity > 0.80 selects good neighbors | Compare similarity bins | Higher similarity → higher accuracy |
| H4 | Historical probability is calibrated | Reliability diagram | ECE < 0.10 |
| H5 | 14-feature vector is better than fewer | Feature ablation | 14 > 10 > 5 features |
| H6 | Walk-forward outperforms in-sample | Compare metrics | WF more robust |
| H7 | Target 2.0 ATR / Stop 1.0 ATR is optimal | Test range [1.5–3.0] / [0.5–1.5] | Positive expectancy |

### L.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Should we weight neighbors by similarity? | Test distance-weighted KNN |
| Q2 | Should different regimes have different K? | Test regime-specific K |
| Q3 | How to handle non-stationarity? | Test rolling covariance estimation |
| Q4 | Should we use probabilistic outcome (continuous) instead of discrete? | Test regression approach |

---

## M — OUTPUT SCHEMA

### M.1 — Historical Output per Bar

```python
@dataclass(frozen=True)
class HistoricalOutput:
    """Historical Engine output for a single bar."""
    timestamp: datetime
    
    # Feature Vector
    feature_vector: np.ndarray          # [14] normalized
    features_missing: list[str]         # Missing feature names
    
    # Neighbors
    k_found: int                        # Number of neighbors found
    k_above_threshold: int              # After similarity filtering
    avg_similarity: float               # Average similarity of K neighbors
    regime_diversity: float             # Fraction of distinct regimes
    
    # Probability
    probability_available: bool         # Whether K ≥ 250
    p_long: float | None                # P(LONG_WIN)
    p_short: float | None               # P(SHORT_WIN)
    p_no_trade: float | None            # P(NO_TRADE)
    probability_calibrated: bool        # Whether calibration applied
    ece_score: float | None             # Calibration error
    
    # Outcome Parameters
    horizon_bars: int                   # 15
    target_atr: float                   # 2.0
    stop_atr: float                     # 1.0
    
    # Diagnostics
    distance_metric: str                # "mahalanobis"
    covariance_singular: bool           # Whether fallback was used
    
    # Provenance
    provenance: DataProvenance
```

---

## N — DECISION OUTPUT

### N.1 — Per-Bar Decision

```
=== HISTORICAL ANALYSIS ===
Feature Vector: [GSI=+58, Struct=+72, Liquidity=+45, Flow=+62, ...]
Features Missing: None

Neighbors Found: 487
Above Threshold (0.80): 312
Avg Similarity: 0.84
Regime Diversity: 0.65

=== HISTORICAL PROBABILITY ===
P(Long):  62% (K=312, calibrated, ECE=0.07)
P(Short): 23% (K=312, calibrated, ECE=0.07)
P(No Trade): 15%

Horizon: 15 bars (75 min)
Target: 2.0 ATR = $36.50
Stop:   1.0 ATR = $18.25

Sample Quality: GOOD (K≥250, Similarity≥0.80, Diverse)
```

---

## O — APPROVAL GATE

### The Phase 8 — Historical Engine specification is now complete.

**Summary of what is defined:**

1. ✅ Feature Vector construction (14 dimensions)
2. ✅ Feature normalization (RobustScaler)
3. ✅ Distance metrics comparison (Euclidean, Manhattan, Mahalanobis, KNN)
4. ✅ Recommended metric: Mahalanobis (correlation-aware)
5. ✅ K-Nearest Neighbor retrieval with temporal constraints
6. ✅ Historical probability computation (P(Long), P(Short), P(No Trade))
7. ✅ Minimum sample requirement (K ≥ 250)
8. ✅ Outcome definition (Horizon, Target, Stop)
9. ✅ Probability calibration (Platt Scaling)
10. ✅ Rule 5 compliance checklist
11. ✅ Edge cases and handling
12. ✅ Bias prevention measures
13. ✅ Backtest requirements (walk-forward)
14. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **Feature Vector (14 dimensions):** Are all features appropriate? Missing any important ones?

2. **Mahalanobis Distance:** Is this the right choice over Euclidean?

3. **K = 250 Minimum:** Is this sufficient for statistical significance?

4. **Similarity Threshold (0.80):** Too strict, too loose, or just right?

5. **Outcome Horizon (15 bars = 75 min):** Appropriate for XAUUSD M5?

6. **Target/Stop (2.0/1.0 ATR):** Reasonable risk-reward for historical outcomes?

7. **Normalization (RobustScaler):** Better than StandardScaler for financial data?

8. **Covariance Regularization:** Is $\lambda = 0.01$ appropriate?

---

**Please review and approve (or request modifications) before I proceed to Phase 9 — Market Regime Engine.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
