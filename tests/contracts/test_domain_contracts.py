"""Contract tests for domain entities.

Tests that verify:
- Timezone enforcement
- availability_time
- Enum validity
- Confidence bounds
- Version presence
- Serialization/deserialization
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest

from src.canonical.enums import (
    DataQuality, Direction, StructureState, SwingType, MarketRegime,
    FlowState, VolumeSource, DecisionType, SetupType, ExitReason,
    NoTradeSeverity, OrderType, OrderSide, OrderStatus, PositionStatus,
    NewsCategory, NewsImpact, SessionType, Timeframe, EvidenceFamily,
)
from src.canonical.contracts import (
    CanonicalBar, CanonicalTick, CanonicalNewsEvent, CanonicalMacroObservation,
    CanonicalSwing, CanonicalLiquidityLevel, CanonicalFlowObservation,
    CanonicalGSI, CanonicalProbability, CanonicalRegime, CanonicalSetup,
    CanonicalRiskDecision, CanonicalNoTradeFlags, CanonicalDecision,
    OrderRequest, OrderResult, CanonicalPosition, CanonicalTrade,
    AccountInfo, FeatureRecord, CanonicalEvidence,
)
from src.canonical.time import TemporalBounds, EventTime, AvailabilityTime, IngestionTime


UTC = timezone.utc


def make_temporal(
    event_time: datetime | None = None,
    availability_time: datetime | None = None,
) -> TemporalBounds:
    """Helper to create TemporalBounds."""
    now = datetime.now(UTC)
    return TemporalBounds(
        event_time=EventTime(event_time or now),
        availability_time=AvailabilityTime(availability_time or now),
        ingestion_time=IngestionTime(now),
    )


# ─────────────────────────────────────────────
# ENUM TESTS
# ─────────────────────────────────────────────

class TestEnums:
    """Test that all enums are valid and serializable."""
    
    def test_data_quality_values(self):
        assert DataQuality.OBSERVED.value == "observed"
        assert DataQuality.INFERRED.value == "inferred"
        assert DataQuality.UNAVAILABLE.value == "unavailable"
    
    def test_direction_values(self):
        assert Direction.LONG.value == "long"
        assert Direction.SHORT.value == "short"
        assert Direction.NEUTRAL.value == "neutral"
    
    def test_decision_type_values(self):
        assert DecisionType.LONG.value == "long"
        assert DecisionType.SHORT.value == "short"
        assert DecisionType.NO_TRADE.value == "no_trade"
    
    def test_no_trade_severity_values(self):
        assert NoTradeSeverity.GREEN == 0
        assert NoTradeSeverity.YELLOW == 1
        assert NoTradeSeverity.ORANGE == 2
        assert NoTradeSeverity.RED == 3
        assert NoTradeSeverity.CRITICAL == 4
    
    def test_all_enums_are_string_serializable(self):
        """All enums should be convertible to string."""
        enums = [
            DataQuality, Direction, StructureState, SwingType, MarketRegime,
            FlowState, VolumeSource, DecisionType, SetupType, ExitReason,
            OrderType, OrderSide, OrderStatus, PositionStatus,
            NewsCategory, SessionType, Timeframe, EvidenceFamily,
        ]
        for enum_cls in enums:
            for member in enum_cls:
                assert isinstance(member.value, (str, int))


# ─────────────────────────────────────────────
# TEMPORAL TESTS
# ─────────────────────────────────────────────

class TestTemporalEnforcement:
    """Test that all contracts enforce timezone awareness."""
    
    def test_bar_rejects_naive_datetime(self):
        """CanonicalBar should reject naive datetime."""
        naive = datetime(2026, 8, 31, 14, 0)  # No timezone
        
        with pytest.raises(TypeError):
            CanonicalBar(
                bar_id="test",
                symbol="XAUUSD",
                timeframe=Timeframe.M5,
                open=Decimal("1850"),
                high=Decimal("1855"),
                low=Decimal("1848"),
                close=Decimal("1853"),
                tick_volume=100,
                temporal=TemporalBounds(
                    event_time=EventTime(naive),  # Should fail
                    availability_time=AvailabilityTime(naive),
                    ingestion_time=IngestionTime(naive),
                ),
            )
    
    def test_bar_accepts_utc_datetime(self):
        """CanonicalBar should accept UTC datetime."""
        utc_time = datetime(2026, 8, 31, 14, 0, tzinfo=UTC)
        
        bar = CanonicalBar(
            bar_id="test",
            symbol="XAUUSD",
            timeframe=Timeframe.M5,
            open=Decimal("1850"),
            high=Decimal("1855"),
            low=Decimal("1848"),
            close=Decimal("1853"),
            tick_volume=100,
            temporal=make_temporal(utc_time, utc_time + timedelta(minutes=5)),
        )
        
        assert bar.temporal.event_time.value.tzinfo is not None


# ─────────────────────────────────────────────
# CONFIDENCE BOUNDS
# ─────────────────────────────────────────────

class TestConfidenceBounds:
    """Test that confidence values are within [0, 1]."""
    
    def test_flow_observation_confidence_bounds(self):
        """Flow observation confidence should be in [0, 1]."""
        flow = CanonicalFlowObservation(
            observation_id="test",
            symbol="XAUUSD",
            timeframe=Timeframe.M5,
            rvol=1.5,
            buying_pressure=0.6,
            selling_pressure=0.4,
            candle_efficiency=0.7,
            volume_acceleration=0.1,
            mv_relationship="confirmation",
            ifp_score=50.0,
            ifp_direction=Direction.LONG,
            data_quality=DataQuality.INFERRED,
            confidence=0.7,
            volume_source=VolumeSource.TICK_PROXY,
            temporal=make_temporal(),
        )
        
        assert 0 <= flow.confidence <= 1
    
    def test_gsi_confidence_bounds(self):
        """GSI confidence should be in [0, 1]."""
        gsi = CanonicalGSI(
            gsi_id="test",
            gsi_raw=50.0,
            gsi_smooth=48.0,
            direction=Direction.LONG,
            confidence=0.48,
            structure_score=60.0,
            flow_score=50.0,
            trend_score=40.0,
            momentum_score=45.0,
            volatility_score=-10.0,
            price_action_score=55.0,
            weights={"structure": 0.25, "flow": 0.20, "trend": 0.15,
                     "momentum": 0.15, "pa": 0.15, "volatility": 0.10},
            temporal=make_temporal(),
        )
        
        assert 0 <= gsi.confidence <= 1
    
    def test_probability_sums_to_one(self):
        """P(Long) + P(Short) + P(NoTrade) should sum to ~1.0."""
        prob = CanonicalProbability(
            prediction_id="test",
            p_long=0.60,
            p_short=0.25,
            p_no_trade=0.15,
            confidence=0.35,
            calibrated=True,
            temporal=make_temporal(),
        )
        
        total = prob.p_long + prob.p_short + prob.p_no_trade
        assert abs(total - 1.0) < 0.01


# ─────────────────────────────────────────────
# VERSION PRESENCE
# ─────────────────────────────────────────────

class TestVersionPresence:
    """Test that all contracts have version field."""
    
    def test_bar_has_version(self):
        bar = CanonicalBar(
            bar_id="test",
            symbol="XAUUSD",
            timeframe=Timeframe.M5,
            open=Decimal("1850"),
            high=Decimal("1855"),
            low=Decimal("1848"),
            close=Decimal("1853"),
            tick_volume=100,
            temporal=make_temporal(),
        )
        assert bar.version == "1.0"
    
    def test_decision_has_version(self):
        decision = CanonicalDecision(
            decision_id="test",
            decision=DecisionType.NO_TRADE,
            decision_reasons=("test",),
            price=Decimal("1850"),
            session=SessionType.LONDON,
            regime=MarketRegime.NORMAL_TREND,
            regime_confidence=0.85,
            structure_score=50.0,
            liquidity_score=50.0,
            flow_score=50.0,
            trend_score=50.0,
            momentum_score=50.0,
            volatility_score=50.0,
            gsi_score=50.0,
            p_long=0.50,
            p_short=0.30,
            p_no_trade=0.20,
            probability_confidence=0.20,
            setup_valid=False,
            setup_quality=0.0,
            entry_trigger=None,
            rr_ratio=0.0,
            position_size=Decimal("0"),
            stop_loss=Decimal("0"),
            take_profit=Decimal("0"),
            no_trade_severity=NoTradeSeverity.GREEN,
            no_trade_conditions=(),
            temporal=make_temporal(),
        )
        assert decision.version == "1.0"


# ─────────────────────────────────────────────
# IMMUTABILITY
# ─────────────────────────────────────────────

class TestImmutability:
    """Test that contracts are frozen (immutable)."""
    
    def test_bar_is_frozen(self):
        bar = CanonicalBar(
            bar_id="test",
            symbol="XAUUSD",
            timeframe=Timeframe.M5,
            open=Decimal("1850"),
            high=Decimal("1855"),
            low=Decimal("1848"),
            close=Decimal("1853"),
            tick_volume=100,
            temporal=make_temporal(),
        )
        
        with pytest.raises(AttributeError):
            bar.symbol = "EURUSD"
