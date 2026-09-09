# PHASE 5 — TREND / MOMENTUM / VOLATILITY ENGINES

## XAUUSD Quantitative Trading System
## Mathematical & Engineering Specification

**Version:** 1.0.0-DRAFT
**Date:** 2026-08-31
| Status | PENDING APPROVAL |
|--------|-----------------|
| Classification | Pre-Implementation — No Code |

---

## A — OBJECTIVE

Define three **independent** engines that analyze different aspects of price dynamics:

1. **Trend Engine** — Direction and strength of the prevailing trend
2. **Momentum Engine** — Rate and acceleration of price movement
3. **Volatility Engine** — Dispersion and regime of price movement

Each engine produces a **unified score** that feeds into the GSI (Phase 6) and Probability Engine (Phase 10).

**Critical Rule (Rule 6 — No Double Counting):**
- Each engine measures a **distinct** aspect of price behavior
- Overlap between engines is **explicitly documented** and minimized
- Where overlap exists, it is treated as **cross-confirmation**, not independent evidence

**Scope Boundary:**
- These engines use **price-derived metrics only**.
- Volume and flow are handled by Phase 4 (Flow Engine).
- Structure and liquidity are handled by Phase 2–3.
- The engines do **not** generate trading signals — they provide context scores.

---

## B — INPUTS

### B.1 — Required Data

| Data | Source | Reference |
|------|--------|-----------|
| OHLCV (all timeframes) | MT5 | Phase 1 |
| ATR | Derived | Phase 5 (this document) |
| Session Data | Phase 1 | Phase 1 |

### B.2 — Parameters

| Parameter | Initial Value | Description |
|-----------|--------------|-------------|
| `TREND_MA_FAST` | 20 | Fast MA period for trend |
| `TREND_MA_SLOW` | 50 | Slow MA period for trend |
| `TREND_ADX_PERIOD` | 14 | ADX period for trend strength |
| `TREND_ADX_THRESHOLD` | 25 | ADX above which trend is "strong" |
| `MOM_RSI_PERIOD` | 14 | RSI period |
| `MOM_ROC_PERIOD` | 10 | ROC period |
| `MOM_MACD_FAST` | 12 | MACD fast EMA |
| `MOM_MACD_SLOW` | 26 | MACD slow EMA |
| `MOM_MACD_SIGNAL` | 9 | MACD signal line |
| `MOM_VELOCITY_PERIOD` | 5 | Price velocity lookback |
| `MOM_ACCELERATION_PERIOD` | 5 | Velocity acceleration lookback |
| `VOL_ATR_PERIOD` | 14 | ATR period |
| `VOL_EXPANSION_LOOKBACK` | 20 | Lookback for expansion/contraction |
| `VOL_REGIME_LOOKBACK` | 50 | Lookback for regime classification |

---

## C — TREND ENGINE

### C.1 — Objective

Measure the **direction and strength** of the prevailing price trend across multiple timeframes.

### C.2 — Trend Direction (Moving Average Crossover)

$$\text{TrendDir}_t = \text{sign}(\text{EMA}_{\text{fast},t} - \text{EMA}_{\text{slow},t})$$

Where:
- $\text{EMA}_{\text{fast}} = \text{EMA}(C, 20)$
- $\text{EMA}_{\text{slow}} = \text{EMA}(C, 50)$

$$\text{TrendDir}_t = \begin{cases}
+1 & \text{if } \text{EMA}_{20} > \text{EMA}_{50} \quad \text{(Bullish)} \\
-1 & \text{if } \text{EMA}_{20} < \text{EMA}_{50} \quad \text{(Bearish)} \\
0 & \text{if } \text{EMA}_{20} = \text{EMA}_{50} \quad \text{(Neutral)}
\end{cases}$$

### C.3 — Trend Strength (ADX)

The **Average Directional Index** measures trend strength regardless of direction:

$$\text{ADX}_t = \text{EMA}\left(\left|\frac{+DI_t - (-DI_t)}{+DI_t + (-DI_t)}\right|, 14\right)$$

Where:
- $+DI_t = \text{EMA}(\max(H_t - H_{t-1}, 0), 14)$
- $-DI_t = \text{EMA}(\max(L_{t-1} - L_t, 0), 14)$

**Interpretation:**

| ADX | Trend Strength |
|-----|---------------|
| < 20 | Weak / No trend |
| 20 – 25 | Developing trend |
| 25 – 40 | Strong trend |
| 40 – 60 | Very strong trend |
| > 60 | Extreme trend (potential exhaustion) |

### C.4 — Trend Slope

$$\text{Slope}_t = \frac{\text{EMA}_{\text{fast},t} - \text{EMA}_{\text{fast},t-n}}{n \times \text{ATR}_{14}}$$

Where $n = 10$ bars.

This normalizes the slope by ATR, making it comparable across volatility regimes.

### C.5 — Multi-Timeframe Trend Score

For each timeframe $tf \in \{D1, H4, H1, M15, M5\}$:

$$\text{TrendScore}_{tf} = \text{TrendDir}_{tf} \times \text{ADX}_{tf}$$

$$\text{TrendScore}_{tf} \in [-100, +100]$$

**Normalization:**

$$\text{TrendScore}_{tf} = \text{TrendDir}_{tf} \times \min(100, \text{ADX}_{tf} \times 2.5)$$

### C.6 — Aggregated Trend Score

$$\text{AggTrendScore} = \sum_{i=1}^{5} W_i \times \text{TrendScore}_{tf_i}$$

Using the same weights from Phase 2:

$$W = [0.30, 0.30, 0.20, 0.15, 0.05]$$

$$\text{AggTrendScore} \in [-100, +100]$$

### C.7 — Overlap with Phase 2 (Structure)

| Aspect | Phase 2 (Structure) | Phase 5 (Trend) | Overlap? |
|--------|-------------------|-----------------|----------|
| Direction | Swing pattern (HH/HL/LH/LL) | MA crossover (EMA20/50) | Partial — different mechanisms |
| Strength | BOS Score | ADX | **No** — different measures |
| State | Bullish/Bearish/Transition | Trend/No-Trend | Partial — can diverge |

**Resolution:** Structure uses **swing-based** analysis; Trend uses **smoothed MA-based** analysis. They can diverge (e.g., structure is transitioning but MA still shows trend). This divergence is informative, not redundant.

---

## D — MOMENTUM ENGINE

### D.1 — Objective

Measure the **rate and acceleration** of price movement — how fast and how hard price is moving.

### D.2 — RSI (Relative Strength Index)

$$\text{RSI}_t = 100 - \frac{100}{1 + \text{RS}_t}$$

Where:

$$\text{RS}_t = \frac{\text{EMA}(\max(C_t - C_{t-1}, 0), 14)}{\text{EMA}(\max(C_{t-1} - C_t, 0), 14)}$$

**Interpretation:**

| RSI | Momentum |
|-----|----------|
| > 70 | Overbought (potential exhaustion) |
| 55 – 70 | Bullish momentum |
| 45 – 55 | Neutral |
| 30 – 45 | Bearish momentum |
| < 30 | Oversold (potential exhaustion) |

### D.3 — ROC (Rate of Change)

$$\text{ROC}_t = \frac{C_t - C_{t-n}}{C_{t-n}} \times 100$$

Where $n = 10$ (initial parameter).

**Interpretation:**
- Positive ROC = Price is rising
- Negative ROC = Price is falling
- Magnitude = Speed of movement

### D.4 — MACD

$$\text{MACD}_t = \text{EMA}(C, 12) - \text{EMA}(C, 26)$$

$$\text{Signal}_t = \text{EMA}(\text{MACD}, 9)$$

$$\text{Histogram}_t = \text{MACD}_t - \text{Signal}_t$$

**Interpretation:**
- Histogram > 0: Bullish momentum
- Histogram < 0: Bearish momentum
- Histogram increasing: Momentum accelerating
- Histogram decreasing: Momentum decelerating

### D.5 — Price Velocity

$$\text{Velocity}_t = \frac{C_t - C_{t-n}}{n}$$

Where $n = 5$ (initial parameter).

This measures the **average price change per bar** over the lookback period.

### D.6 — Momentum Acceleration

$$\text{MomAccel}_t = \text{Velocity}_t - \text{Velocity}_{t-n}$$

Where $n = 5$ (same as velocity lookback).

**Interpretation:**
- Positive acceleration: Velocity increasing (momentum building)
- Negative acceleration: Velocity decreasing (momentum fading)

### D.7 — Momentum Score Components

Each component is normalized to $[-100, +100]$:

$$\text{RSI}_{\text{score}} = \frac{\text{RSI}_t - 50}{50} \times 100$$

$$\text{ROC}_{\text{score}} = \text{sign}(\text{ROC}_t) \times \min(100, |\text{ROC}_t| \times 10)$$

$$\text{MACD}_{\text{score}} = \text{sign}(\text{Histogram}_t) \times \min(100, \frac{|\text{Histogram}_t|}{\text{ATR}_{14}} \times 50)$$

$$\text{Velocity}_{\text{score}} = \text{sign}(\text{Velocity}_t) \times \min(100, \frac{|\text{Velocity}_t|}{\text{ATR}_{14}} \times 50)$$

$$\text{Accel}_{\text{score}} = \text{sign}(\text{MomAccel}_t) \times \min(100, \frac{|\text{MomAccel}_t|}{\text{ATR}_{14}} \times 100)$$

### D.8 — Aggregated Momentum Score

$$\text{MomentumScore} = w_1 \cdot \text{RSI}_{\text{score}} + w_2 \cdot \text{ROC}_{\text{score}} + w_3 \cdot \text{MACD}_{\text{score}} + w_4 \cdot \text{Velocity}_{\text{score}} + w_5 \cdot \text{Accel}_{\text{score}}$$

| Component | Weight | Rationale |
|-----------|--------|-----------|
| RSI | $w_1 = 0.25$ | Overbought/oversold + direction |
| ROC | $w_2 = 0.20$ | Pure rate of change |
| MACD | $w_3 = 0.25$ | Trend-following momentum |
| Velocity | $w_4 = 0.15$ | Short-term speed |
| Acceleration | $w_5 = 0.15$ | Momentum change rate |

$$\text{MomentumScore} \in [-100, +100]$$

### D.9 — Overlap Analysis (Rule 6)

| Component | Measures | Overlaps With |
|-----------|----------|--------------|
| RSI | Overbought/Oversold + Direction | Flow (CE), Structure (extremes) |
| ROC | Rate of change | Velocity (same concept, different period) |
| MACD | Trend-following momentum | Trend (EMA-based), Velocity |
| Velocity | Price speed | ROC (scaled), MACD (direction) |
| Acceleration | Speed change | Volume Acceleration (different data) |

**Double Counting Mitigation:**

1. **RSI vs. Flow CE:** RSI uses closing prices over 14 bars; CE uses single-bar range. Different time horizons → **Low overlap**.

2. **ROC vs. Velocity:** ROC is percentage change over $n$ bars; Velocity is absolute change per bar. Same concept, different scaling. **Treat as near-duplicate** — combine into single weight or use only one.

   **Resolution:** Keep both but acknowledge overlap. In GSI (Phase 6), use **Evidence Families** to prevent double counting.

3. **MACD vs. Trend EMA:** MACD uses EMA(12) - EMA(26); Trend uses EMA(20) vs. EMA(50). **Partial overlap** — different periods, different interpretation.

   **Resolution:** MACD measures **momentum** (rate of change of the trend); Trend measures **direction** (cross-over). They answer different questions.

4. **Velocity vs. Acceleration:** Velocity is the first derivative; Acceleration is the second derivative. **No overlap** — they measure different orders of price change.

### D.10 — Overbought/Oversold Handling

RSI extremes (> 70 or < 30) require special treatment:

$$\text{ExtremeFactor}_t = \begin{cases}
\text{exhaustion\_warning} & \text{if } \text{RSI} > 75 \text{ or } \text{RSI} < 25 \\
\text{overbought/oversold} & \text{if } 70 < \text{RSI} \leq 75 \text{ or } 25 \leq \text{RSI} < 30 \\
\text{normal} & \text{otherwise}
\end{cases}$$

This feeds into the **No-Trade Engine** (Phase 14) as a caution signal.

---

## E — VOLATILITY ENGINE

### E.1 — Objective

Measure the **dispersion and regime** of price movement — how much and how fast price is fluctuating.

### E.2 — ATR (Average True Range)

$$\text{TR}_t = \max\left(H_t - L_t, \, |H_t - C_{t-1}|, \, |L_t - C_{t-1}|\right)$$

$$\text{ATR}_{14,t} = \text{EMA}(\text{TR}, 14)_t$$

### E.3 — ATR Normalization

$$\text{ATR}_{\text{norm},t} = \frac{\text{ATR}_{14,t}}{C_t}$$

This gives ATR as a percentage of price, making it comparable across different price levels.

### E.4 — ATR Expansion / Contraction

$$\text{ATR}_{\text{ratio},t} = \frac{\text{ATR}_{14,t}}{\text{EMA}(\text{ATR}_{14}, n)_t}$$

Where $n = 20$ (initial — `VOL_EXPANSION_LOOKBACK`).

**Interpretation:**

| ATR Ratio | Regime | Description |
|-----------|--------|-------------|
| > 1.5 | Expansion | Volatility increasing rapidly |
| 1.2 – 1.5 | Mild Expansion | Volatility above average |
| 0.8 – 1.2 | Normal | Volatility at average |
| 0.5 – 0.8 | Mild Contraction | Volatility below average |
| < 0.5 | Contraction | Volatility decreasing rapidly (squeeze) |

### E.5 — Volatility Regime Classification

$$\text{VolRegime}_t = f(\text{ATR}_{\text{ratio},t}, \text{ATR}_{\text{trend},t})$$

Where $\text{ATR}_{\text{trend}}$ = slope of ATR over lookback.

| Regime | ATR Ratio | ATR Trend | Description |
|--------|-----------|-----------|-------------|
| **High Volatility** | > 1.5 | Rising | Expanding volatility |
| **Normal Volatility** | 0.8 – 1.2 | Stable | Average conditions |
| **Low Volatility** | < 0.8 | Falling | Contracting volatility |
| **Squeeze** | < 0.5 | Falling sharply | Potential breakout setup |
| **Volatility Spike** | > 2.0 | Sharp rise | Event-driven or panic |

### E.6 — Range Expansion

$$\text{Range}_t = H_t - L_t$$

$$\text{Range}_{\text{ratio},t} = \frac{\text{Range}_t}{\text{ATR}_{14,t}}$$

**Interpretation:**

| Range Ratio | Description |
|-------------|-------------|
| > 2.0 | Extended bar (potential exhaustion or breakout) |
| 1.0 – 2.0 | Normal range |
| 0.5 – 1.0 | Compressed range |
| < 0.5 | Very compressed (doji-like) |

### E.7 — Bollinger Band Width

$$\text{BBW}_t = \frac{\text{Upper}_t - \text{Lower}_t}{\text{Middle}_t}$$

Where:
- $\text{Middle}_t = \text{SMA}(C, 20)$
- $\text{Upper}_t = \text{Middle} + 2 \times \text{StdDev}(C, 20)$
- $\text{Lower}_t = \text{Middle} - 2 \times \text{StdDev}(C, 20)$

**Interpretation:**
- Narrow BBW = Low volatility (squeeze)
- Wide BBW = High volatility

### E.8 — Volatility Score

$$\text{VolScore} = w_1 \cdot \text{ATR}_{\text{score}} + w_2 \cdot \text{Range}_{\text{score}} + w_3 \cdot \text{BBW}_{\text{score}}$$

| Component | Weight | Description |
|-----------|--------|-------------|
| ATR Ratio | $w_1 = 0.40$ | Primary volatility measure |
| Range Ratio | $w_2 = 0.30$ | Bar-level volatility |
| BBW | $w_3 = 0.30$ | Statistical volatility |

**Normalization:**

$$\text{ATR}_{\text{score}} = (\text{ATR}_{\text{ratio}} - 1) \times 50$$

$$\text{Range}_{\text{score}} = (\text{Range}_{\text{ratio}} - 1) \times 50$$

$$\text{BBW}_{\text{score}} = (\text{BBW}_t - \text{BBW}_{\text{avg}}) \times 100$$

$$\text{VolScore} \in [-100, +100]$$

**Interpretation:**
- Positive: Volatility above average (expansion)
- Negative: Volatility below average (contraction)
- Near zero: Normal volatility

### E.9 — Volatility State

$$\text{VolState}_t = \begin{cases}
\text{High Volatility} & \text{if } \text{VolScore} > +40 \\
\text{Normal} & \text{if } -20 \leq \text{VolScore} \leq +20 \\
\text{Low Volatility} & \text{if } \text{VolScore} < -20 \\
\text{Squeeze} & \text{if } \text{VolScore} < -40 \\
\text{Spike} & \text{if } \text{VolScore} > +60
\end{cases}$$

### E.10 — Overlap Analysis (Rule 6)

| Aspect | Volatility Engine | Overlaps With |
|--------|------------------|--------------|
| ATR | Range-based dispersion | BOS/MSS tolerance (uses ATR) |
| Range | Single-bar range | Candle Efficiency (uses range) |
| BBW | Statistical dispersion | ATR (related concept) |

**Double Counting Mitigation:**

1. **ATR vs. BOS/MSS Tolerance:** ATR is an **input** to Phase 2 tolerance, not a duplicate. The Volatility Engine **classifies** the volatility regime; Phase 2 **uses** ATR for level tolerance. Different purposes.

2. **Range vs. CE:** Range measures **size** of the bar; CE measures **directionality** within the range. A bar can have large range but low CE (doji). **Low overlap**.

3. **ATR vs. BBW:** Both measure dispersion but using different methods (true range vs. standard deviation). **Moderate overlap** — combine with appropriate weighting.

---

## F — UNIFIED ENGINE OUTPUTS

### F.1 — Per-Engine Scores

| Engine | Score | Range | Direction |
|--------|-------|-------|-----------|
| Trend Engine | `trend_score` | [-100, +100] | Direction + Strength |
| Momentum Engine | `momentum_score` | [-100, +100] | Rate + Direction |
| Volatility Engine | `volatility_score` | [-100, +100] | Dispersion level |

### F.2 — Score Semantics

| Score | Trend | Momentum | Volatility |
|-------|-------|----------|-----------|
| +80 to +100 | Strong Bullish Trend | Strong Bullish Momentum | Extreme Expansion |
| +50 to +79 | Moderate Bullish Trend | Moderate Bullish Momentum | Above-Average Volatility |
| +20 to +49 | Weak Bullish Trend | Weak Bullish Momentum | Mild Expansion |
| -20 to +20 | No Clear Trend | Neutral Momentum | Normal Volatility |
| -49 to -20 | Weak Bearish Trend | Weak Bearish Momentum | Mild Contraction |
| -79 to -50 | Moderate Bearish Trend | Moderate Bearish Momentum | Below-Average Volatility |
| -100 to -80 | Strong Bearish Trend | Strong Bearish Momentum | Extreme Contraction / Squeeze |

### F.3 — Divergence Detection

When scores diverge, the system should note:

| Divergence | Interpretation | Action |
|-----------|---------------|--------|
| Trend Bullish + Momentum Bearish | Trend weakening | Caution |
| Trend Bullish + Volatility Low | Trend may be maturing | Prepare for breakout |
| Momentum Bullish + Volatility High | Strong move, potential exhaustion | Monitor for reversal |
| All three aligned | Strong conviction | Higher confidence |

---

## G — EDGE CASES

### G.1 — Insufficient Data

| Scenario | Handling |
|----------|----------|
| Fewer than 50 bars available | Use available data; mark scores as `provisional` |
| MA periods not yet warmed up | Use simple average until EMA stabilizes |
| ADX unavailable (< 28 bars) | Set ADX = 0; trend strength unknown |

### G.2 — Price Anomalies

| Scenario | Handling |
|----------|----------|
| Gap up/down | ATR handles via TR formula |
| Doji (H=L=C) | Velocity = 0; Momentum = 0 |
| Extreme bar (> 5 ATR) | Cap ATR ratio at 3.0 for scoring |

### G.3 — Regime Transitions

| Scenario | Handling |
|----------|----------|
| Rapid regime changes | Smooth regime classification over 3 bars |
| Squeeze to Spike | Log as potential breakout setup |

---

## H — BIAS PREVENTION

### H.1 — Look-Ahead Bias

**Prevention:**
1. All indicators computed sequentially from bar 1 to bar $t$
2. No future data in any computation
3. EMA/RSI/MACD are inherently causal (use only past data)

### H.2 — Repainting

**Prevention:**
1. Indicators use confirmed bar data only
2. No retroactive recalculation
3. Once a score is computed for bar $t$, it is frozen

### H.3 — Double Counting (Rule 6)

**Prevention:**

| Overlap | Mitigation |
|---------|-----------|
| ROC vs. Velocity | Document as near-duplicates; combine in GSI via Evidence Families |
| MACD vs. Trend EMA | Different questions (momentum vs. direction) |
| ATR vs. BBW | Different methods (range vs. std dev); combine with weighting |
| RSI vs. Flow CE | Different time horizons (14-bar vs. single-bar) |

**Evidence Family Assignment:**

| Engine | Evidence Family |
|--------|---------------|
| Trend | Structure + Trend |
| Momentum | Momentum |
| Volatility | Volatility |

In Phase 10 (Probability Engine), members of the same family are combined before cross-family comparison.

---

## I — BACKTESTABILITY

### I.1 — Backtest Requirements

| Requirement | Implementation |
|-------------|---------------|
| Sequential computation | Bar-by-bar, no batch processing |
| MA warmup | First 50 bars = provisional scores |
| ADX warmup | First 28 bars = ADX = 0 |
| No future data | All indicators are causal |
| Score freezing | Once computed, never updated |

### I.2 — Backtest Data Flow

```
OHLCV (per timeframe)
    ↓
├── Trend Engine
│   ├── EMA(20), EMA(50)
│   ├── ADX(14)
│   └── Trend Score [-100, +100]
│
├── Momentum Engine
│   ├── RSI(14)
│   ├── ROC(10)
│   ├── MACD(12,26,9)
│   ├── Velocity(5)
│   ├── Acceleration(5)
│   └── Momentum Score [-100, +100]
│
└── Volatility Engine
    ├── ATR(14)
    ├── Range Ratio
    ├── BBW
    └── Volatility Score [-100, +100]
```

---

## J — WHAT IS FIXED

### J.1 — Fixed at This Stage

| Item | Value | Rationale |
|------|-------|-----------|
| Trend MA Fast | EMA(20) | ~1 trading day on M5 |
| Trend MA Slow | EMA(50) | ~2.5 trading days on M5 |
| ADX Period | 14 | Industry standard |
| ADX Threshold | 25 | Strong trend threshold |
| RSI Period | 14 | Industry standard |
| ROC Period | 10 | Balances responsiveness vs. noise |
| MACD | 12/26/9 | Industry standard |
| Velocity Period | 5 | Short-term speed |
| Acceleration Period | 5 | Velocity change rate |
| ATR Period | 14 | Industry standard |
| ATR Expansion Lookback | 20 | ~1 trading day |
| Volatility Regime Lookback | 50 | ~2.5 trading days |
| MTF Weights | [0.30, 0.30, 0.20, 0.15, 0.05] | From Phase 2 |

### J.2 — Not Fixed (Deferred)

| Item | Deferred To |
|------|-------------|
| Optimal MA periods | Phase 17 (Optimization) |
| Momentum weight optimization | Phase 17 |
| Volatility weight optimization | Phase 17 |
| ADX threshold optimization | Phase 17 |
| RSI extreme thresholds | Phase 17 |
| Regime classification boundaries | Phase 17 |

---

## K — WHAT REQUIRES TESTING

### K.1 — Hypotheses

| # | Hypothesis | Test Method | Expected |
|---|-----------|-------------|----------|
| H1 | EMA(20/50) captures XAUUSD trend on M5 | Visual + statistical | > 70% trend identification accuracy |
| H2 | ADX > 25 identifies "strong" trends | Backtest trend-following | Higher win rate when ADX > 25 |
| H3 | RSI extremes precede reversals | Statistical test | Reversal probability > 55% within 10 bars |
| H4 | MACD histogram correlates with price acceleration | Compute correlation | ρ > 0.4 |
| H5 | ATR regime classification is stable | Check regime duration | Average regime > 20 bars |
| H6 | Squeeze precedes breakout | Statistical test | Breakout within 10 bars > 40% |
| H7 | Three-engine alignment predicts direction | Backtest aligned vs. unaligned | Aligned signals have higher win rate |

### K.2 — Open Questions

| # | Question | Resolution |
|---|----------|------------|
| Q1 | Should RSI use Wilder's smoothing or standard EMA? | Test both |
| Q2 | Is MACD(12,26,9) optimal for XAUUSD M5? | Test variations |
| Q3 | Should volatility regime boundaries be session-specific? | Test per-session calibration |
| Q4 | How to handle regime transitions in scoring? | Test smoothing approaches |

---

## L — OUTPUT SCHEMA

### L.1 — Trend Output

```python
@dataclass(frozen=True)
class TrendOutput:
    """Trend Engine output for a single bar."""
    timestamp: datetime
    
    # Direction
    trend_direction: str                 # "bullish", "bearish", "neutral"
    ema_fast: float                      # EMA(20)
    ema_slow: float                      # EMA(50)
    ema_cross: str                       # "bullish_cross", "bearish_cross", "none"
    
    # Strength
    adx: float                           # ADX value
    trend_strength: str                  # "weak", "developing", "strong", "very_strong", "extreme"
    slope: float                         # Normalized slope
    
    # Multi-Timeframe
    mtf_score: float                     # [-100, +100]
    per_tf_scores: dict[str, float]      # Score per timeframe
    
    # Aggregate
    trend_score: float                   # [-100, +100]
    trend_state: str                     # "trending_up", "trending_down", "no_trend"
    
    # Provenance
    provenance: DataProvenance
```

### L.2 — Momentum Output

```python
@dataclass(frozen=True)
class MomentumOutput:
    """Momentum Engine output for a single bar."""
    timestamp: datetime
    
    # Components
    rsi: float
    roc: float
    macd: float
    macd_signal: float
    macd_histogram: float
    velocity: float
    acceleration: float
    
    # Scores
    rsi_score: float
    roc_score: float
    macd_score: float
    velocity_score: float
    accel_score: float
    
    # Aggregate
    momentum_score: float                # [-100, +100]
    momentum_direction: str              # "bullish", "bearish", "neutral"
    momentum_state: str                  # "accelerating", "decelerating", "stable"
    
    # Extremes
    is_overbought: bool
    is_oversold: bool
    extreme_factor: str                  # "normal", "overbought", "oversold", "exhaustion_warning"
    
    # Provenance
    provenance: DataProvenance
```

### L.3 — Volatility Output

```python
@dataclass(frozen=True)
class VolatilityOutput:
    """Volatility Engine output for a single bar."""
    timestamp: datetime
    
    # Components
    atr: float
    atr_norm: float                      # ATR / Price
    atr_ratio: float                     # ATR / EMA(ATR)
    range_ratio: float                   # Range / ATR
    bbw: float                           # Bollinger Band Width
    
    # Regime
    vol_regime: str                      # "high", "normal", "low", "squeeze", "spike"
    vol_state: str                       # "expanding", "contracting", "stable"
    
    # Scores
    atr_score: float
    range_score: float
    bbw_score: float
    
    # Aggregate
    volatility_score: float              # [-100, +100]
    
    # Provenance
    provenance: DataProvenance
```

---

## M — DECISION OUTPUT

### M.1 — Per-Bar Decision

```
=== ENGINE SCORES ===
Trend:    Bullish (+65) — Strong (ADX=38), EMA20 > EMA50
Momentum: Bullish (+42) — RSI=62, MACD Histogram=+0.85, Velocity=+0.12
Volatility: Normal (-8) — ATR Ratio=0.95, Range Ratio=1.05

=== DIVERGENCE CHECK ===
Trend vs Momentum: Aligned ✅
Momentum vs Volatility: Normal ✅
Trend vs Volatility: Normal ✅

=== REGIME ===
Trend: Trending Up
Momentum: Accelerating
Volatility: Normal (Slight Contraction)
```

---

## N — APPROVAL GATE

### The Phase 5 — Trend / Momentum / Volatility specification is now complete.

**Summary of what is defined:**

1. ✅ Trend Engine (EMA crossover, ADX, slope, multi-TF)
2. ✅ Momentum Engine (RSI, ROC, MACD, Velocity, Acceleration)
3. ✅ Volatility Engine (ATR, Range Ratio, BBW, Regime)
4. ✅ Each engine produces unified score [-100, +100]
5. ✅ Double counting analysis and mitigation
6. ✅ Evidence Family assignment
7. ✅ Edge cases and handling
8. ✅ Bias prevention measures
9. ✅ Backtest requirements
10. ✅ Output schemas

---

### 📋 Points Requiring Your Approval:

1. **Trend MA Periods (20/50):** Appropriate for XAUUSD M5?

2. **ADX Threshold (25):** Good threshold for "strong" trend?

3. **Momentum Weights:** RSI 25%, MACD 25%, ROC 20%, Velocity 15%, Acceleration 15% — acceptable?

4. **Volatility Weights:** ATR 40%, Range 30%, BBW 30% — acceptable?

5. **ROC vs. Velocity Overlap:** Accept the near-duplicate relationship and handle in GSI?

6. **ATR vs. BBW Overlap:** Accept moderate overlap and combine with weighting?

7. **RSI Extreme Thresholds (70/30):** Standard thresholds, or adjust for XAUUSD?

8. **Regime Classification Boundaries:** Are the ATR ratio thresholds appropriate?

---

**Please review and approve (or request modifications) before I proceed to Phase 6 — GSI.**

---

*Document generated as part of the XAUUSD Quantitative Trading System specification.*
*No code has been written. All definitions are mathematical/engineering specifications.*
