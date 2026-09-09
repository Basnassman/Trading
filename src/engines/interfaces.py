"""Engine interfaces for the XAUUSD Trading System.

Each engine defines:
- Input Contract (what it needs)
- Output Contract (what it produces)
- Version
- Required Availability
- Failure Behavior

No business logic is implemented here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from src.canonical.contracts import (
    CanonicalBar, CanonicalSwing, CanonicalLiquidityLevel, CanonicalSweep,
    CanonicalFlowObservation, CanonicalEvidence, CanonicalGSI,
    CanonicalHistoricalMatch, CanonicalProbability, CanonicalRegime,
    CanonicalSetup, CanonicalRiskDecision, CanonicalNoTradeFlags,
    CanonicalDecision, FeatureRecord,
)
from src.canonical.enums import (
    StructureState, FlowState, MarketRegime, Direction, EvidenceFamily,
    NoTradeSeverity, Timeframe,
)


# ─────────────────────────────────────────────
# BASE ENGINE
# ─────────────────────────────────────────────

class BaseEngine(ABC):
    """Base class for all engines."""
    
    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Engine identifier."""
        ...
    
    @property
    @abstractmethod
    def engine_version(self) -> str:
        """Engine version."""
        ...
    
    @abstractmethod
    def validate_inputs(self, **kwargs) -> bool:
        """Validate that required inputs are available and valid."""
        ...
    
    @abstractmethod
    def get_availability_requirements(self) -> dict[str, str]:
        """Return what data must be available for this engine to run."""
        ...


# ─────────────────────────────────────────────
# MARKET STRUCTURE ENGINE
# ─────────────────────────────────────────────

class MarketStructureEngine(BaseEngine):
    """Phase 2: Market Structure Engine.
    
    Input: OHLCV bars
    Output: Structure Score, State, Swing Points, BOS/CHoCH
    """
    
    @abstractmethod
    def compute_swings(
        self,
        bars: list[CanonicalBar],
        k: int = 3,
    ) -> list[CanonicalSwing]:
        """Compute swing points from bars."""
        ...
    
    @abstractmethod
    def compute_structure_state(
        self,
        swings: list[CanonicalSwing],
    ) -> StructureState:
        """Compute current structure state."""
        ...
    
    @abstractmethod
    def compute_structure_score(
        self,
        state: StructureState,
        swings: list[CanonicalSwing],
    ) -> float:
        """Compute structure score [-100, +100]."""
        ...
    
    @abstractmethod
    def detect_bos(
        self,
        bars: list[CanonicalBar],
        swings: list[CanonicalSwing],
        atr: float,
    ) -> Optional[dict]:
        """Detect Break of Structure."""
        ...
    
    @abstractmethod
    def detect_mss(
        self,
        bars: list[CanonicalBar],
        swings: list[CanonicalSwing],
    ) -> Optional[dict]:
        """Detect Market Structure Shift / Change of Character."""
        ...


# ─────────────────────────────────────────────
# LIQUIDITY ENGINE
# ─────────────────────────────────────────────

class LiquidityEngine(BaseEngine):
    """Phase 3: Liquidity Engine.
    
    Input: OHLCV, Swing Points, Sessions
    Output: Liquidity Levels, Clusters, Sweep Detection, Liquidity Score
    """
    
    @abstractmethod
    def compute_liquidity_levels(
        self,
        bars: list[CanonicalBar],
        swings: list[CanonicalSwing],
        sessions: list,
    ) -> list[CanonicalLiquidityLevel]:
        """Compute liquidity levels."""
        ...
    
    @abstractmethod
    def detect_sweep(
        self,
        bars: list[CanonicalBar],
        levels: list[CanonicalLiquidityLevel],
        atr: float,
    ) -> Optional[CanonicalSweep]:
        """Detect liquidity sweep."""
        ...
    
    @abstractmethod
    def compute_liquidity_score(
        self,
        levels: list[CanonicalLiquidityLevel],
        sweep: Optional[CanonicalSweep],
    ) -> float:
        """Compute liquidity score [-100, +100]."""
        ...


# ─────────────────────────────────────────────
# FLOW ENGINE
# ─────────────────────────────────────────────

class FlowEngine(BaseEngine):
    """Phase 4: Flow Engine (Institutional Flow Proxy).
    
    Input: OHLCV, Volume, Liquidity Levels
    Output: IFP Score, Flow State, Data Quality Level
    """
    
    @abstractmethod
    def compute_flow_features(
        self,
        bar: CanonicalBar,
        atr: float,
    ) -> dict[str, float]:
        """Compute flow features (RVOL, BP, SP, CE, VA, MV)."""
        ...
    
    @abstractmethod
    def compute_ifp_score(
        self,
        features: dict[str, float],
    ) -> float:
        """Compute Institutional Flow Proxy score [-100, +100]."""
        ...
    
    @abstractmethod
    def classify_flow_state(
        self,
        features: dict[str, float],
        ifp_score: float,
    ) -> FlowState:
        """Classify flow state."""
        ...
    
    @abstractmethod
    def compute_confidence(
        self,
        volume_source: str,
        features_available: list[str],
    ) -> float:
        """Compute IFP confidence based on data quality."""
        ...


# ─────────────────────────────────────────────
# TREND ENGINE
# ─────────────────────────────────────────────

class TrendEngine(BaseEngine):
    """Phase 5: Trend Engine.
    
    Input: OHLCV
    Output: Trend Score [-100, +100]
    """
    
    @abstractmethod
    def compute_trend_score(self, bars: list[CanonicalBar]) -> float:
        """Compute trend score [-100, +100]."""
        ...


# ─────────────────────────────────────────────
# MOMENTUM ENGINE
# ─────────────────────────────────────────────

class MomentumEngine(BaseEngine):
    """Phase 5: Momentum Engine.
    
    Input: OHLCV
    Output: Momentum Score [-100, +100]
    """
    
    @abstractmethod
    def compute_momentum_score(self, bars: list[CanonicalBar]) -> float:
        """Compute momentum score [-100, +100]."""
        ...


# ─────────────────────────────────────────────
# VOLATILITY ENGINE
# ─────────────────────────────────────────────

class VolatilityEngine(BaseEngine):
    """Phase 5: Volatility Engine.
    
    Input: OHLCV
    Output: Volatility Score [-100, +100], ATR
    """
    
    @abstractmethod
    def compute_volatility_score(self, bars: list[CanonicalBar]) -> float:
        """Compute volatility score [-100, +100]."""
        ...
    
    @abstractmethod
    def compute_atr(self, bars: list[CanonicalBar], period: int = 14) -> float:
        """Compute Average True Range."""
        ...


# ─────────────────────────────────────────────
# GSI ENGINE
# ─────────────────────────────────────────────

class GSIEngine(BaseEngine):
    """Phase 6: Gold Smart Index.
    
    Input: Structure, Flow, Trend, Momentum, PA, Volatility Scores
    Output: GSI [-100, +100]
    
    CRITICAL: GSI is a DIAGNOSTIC INDEX only.
    GSI is NEVER an input to the Probability Engine.
    """
    
    @abstractmethod
    def compute_gsi(
        self,
        structure_score: float,
        flow_score: float,
        trend_score: float,
        momentum_score: float,
        volatility_score: float,
        price_action_score: float,
    ) -> CanonicalGSI:
        """Compute Gold Smart Index."""
        ...


# ─────────────────────────────────────────────
# NEWS/MACRO ENGINE
# ─────────────────────────────────────────────

class NewsMacroEngine(BaseEngine):
    """Phase 7: News/Macro Engine.
    
    Input: News Events, DXY, Yields, FFR
    Output: News Score, Macro Score
    """
    
    @abstractmethod
    def compute_news_score(self, events: list) -> float:
        """Compute news score [-100, +100]."""
        ...
    
    @abstractmethod
    def compute_macro_score(
        self,
        dxy: Optional[float],
        yield_2y: Optional[float],
        yield_10y: Optional[float],
        ffr: Optional[float],
    ) -> float:
        """Compute macro score [-100, +100]."""
        ...


# ─────────────────────────────────────────────
# HISTORICAL SIMILARITY ENGINE
# ─────────────────────────────────────────────

class HistoricalSimilarityEngine(BaseEngine):
    """Phase 8: Historical Similarity Engine.
    
    Input: Feature Vector (14 dimensions)
    Output: Historical Probability P(Long), P(Short), P(NoTrade)
    """
    
    @abstractmethod
    def find_neighbors(
        self,
        feature_vector: list[float],
        historical_data: list[list[float]],
        k_search: int = 500,
    ) -> list[tuple[int, float]]:
        """Find K nearest neighbors.
        
        Returns:
            List of (index, similarity) tuples
        """
        ...
    
    @abstractmethod
    def compute_probability(
        self,
        neighbors: list[tuple[int, float]],
        outcomes: list[str],
        k_min: int = 250,
    ) -> Optional[CanonicalProbability]:
        """Compute historical probability."""
        ...


# ─────────────────────────────────────────────
# REGIME ENGINE
# ─────────────────────────────────────────────

class RegimeEngine(BaseEngine):
    """Phase 9: Regime Detection Engine.
    
    Input: Structure, Liquidity, Flow, Trend, Volatility, News
    Output: Regime Type, Confidence, Parameter Adjustments
    """
    
    @abstractmethod
    def classify_regime(
        self,
        structure_state: StructureState,
        atr_ratio: float,
        adx: float,
        trend_score: float,
        flow_score: float,
        news_blocking: bool,
        sweep_detected: bool,
        rvol: float,
    ) -> CanonicalRegime:
        """Classify current market regime."""
        ...


# ─────────────────────────────────────────────
# EVIDENCE ENGINE
# ─────────────────────────────────────────────

class EvidenceEngine(BaseEngine):
    """Phase 10: Evidence Family Aggregator.
    
    Input: All feature scores
    Output: Evidence Families (8 families)
    
    CRITICAL: Evidence Families are the SOLE input to Probability Engine.
    GSI is NOT an input.
    """
    
    @abstractmethod
    def aggregate_evidence(
        self,
        structure_score: float,
        liquidity_score: float,
        flow_score: float,
        trend_score: float,
        momentum_score: float,
        volatility_score: float,
        news_score: float,
        macro_score: float,
        historical_p_long: Optional[float],
        regime: MarketRegime,
        session: str,
    ) -> dict[EvidenceFamily, CanonicalEvidence]:
        """Aggregate evidence into families."""
        ...


# ─────────────────────────────────────────────
# PROBABILITY ENGINE
# ─────────────────────────────────────────────

class ProbabilityEngine(BaseEngine):
    """Phase 10: Probability Engine.
    
    Input: Evidence Families (SOLE input)
    Output: P(Long), P(Short), P(NoTrade)
    
    CRITICAL: GSI is NOT an input to this engine.
    """
    
    @abstractmethod
    def compute_probability(
        self,
        evidence: dict[EvidenceFamily, CanonicalEvidence],
    ) -> CanonicalProbability:
        """Compute calibrated probability from evidence families."""
        ...


# ─────────────────────────────────────────────
# SETUP ENGINE
# ─────────────────────────────────────────────

class SetupEngine(BaseEngine):
    """Phase 11: Setup Engine.
    
    Input: Probability, Structure, Liquidity, Flow, Regime
    Output: Setup Valid/Invalid, Quality, Entry Trigger
    """
    
    @abstractmethod
    def validate_setup(
        self,
        probability: CanonicalProbability,
        structure_state: StructureState,
        liquidity_score: float,
        flow_score: float,
        regime: MarketRegime,
        rr_ratio: float,
        session: str,
        spread: float,
    ) -> CanonicalSetup:
        """Validate trading setup."""
        ...


# ─────────────────────────────────────────────
# RISK ENGINE
# ─────────────────────────────────────────────

class RiskEngine(BaseEngine):
    """Phase 12: Risk Engine.
    
    Input: Setup, Structure, Liquidity, Regime
    Output: Position Size, SL/TP, Risk Limits Check
    """
    
    @abstractmethod
    def compute_risk(
        self,
        setup: CanonicalSetup,
        equity: float,
        atr: float,
        regime: MarketRegime,
    ) -> CanonicalRiskDecision:
        """Compute risk assessment for a potential trade."""
        ...


# ─────────────────────────────────────────────
# NO-TRADE ENGINE
# ─────────────────────────────────────────────

class NoTradeEngine(BaseEngine):
    """Phase 14: No-Trade Condition Evaluator.
    
    Input: Spread, Volatility, News, Risk, Liquidity, Evidence, Regime
    Output: NoTradeFlags + Severity (NOT a decision)
    
    CRITICAL: This engine does NOT make decisions.
    It evaluates conditions and produces severity levels.
    The Decision Engine interprets these.
    """
    
    @abstractmethod
    def evaluate_conditions(
        self,
        spread: float,
        atr_ratio: float,
        news_blocking: bool,
        rr_ratio: float,
        liquidity_score: float,
        evidence_conflict: int,
        daily_pnl_pct: float,
        regime_confidence: float,
    ) -> CanonicalNoTradeFlags:
        """Evaluate no-trade conditions."""
        ...


# ─────────────────────────────────────────────
# DECISION ENGINE
# ─────────────────────────────────────────────

class DecisionEngine(BaseEngine):
    """Phase 15: Decision Engine.
    
    Input: Setup, Risk, NoTradeFlags, Probability, GSI
    Output: Final Decision (LONG / SHORT / NO_TRADE)
    
    CRITICAL: This is the SOLE decision maker.
    """
    
    @abstractmethod
    def make_decision(
        self,
        setup: CanonicalSetup,
        risk: CanonicalRiskDecision,
        no_trade: CanonicalNoTradeFlags,
        probability: CanonicalProbability,
        gsi: CanonicalGSI,
    ) -> CanonicalDecision:
        """Make final trading decision."""
        ...


# ─────────────────────────────────────────────
# TRADE MANAGEMENT ENGINE
# ─────────────────────────────────────────────

class TradeManagementEngine(BaseEngine):
    """Phase 13: Trade Management Engine.
    
    Input: Open Position, Current Price, Structure, Liquidity
    Output: Management Actions (partial close, BE, trailing, emergency)
    """
    
    @abstractmethod
    def manage_position(
        self,
        position: Any,
        current_price: float,
        atr: float,
        swings: list,
        liquidity_levels: list,
    ) -> dict:
        """Determine management actions for open position."""
        ...
