"""Core enumerations for the XAUUSD Trading System.

These enums are shared across all modules and define the vocabulary
of the system. Do not add business logic here.
"""

from enum import Enum, IntEnum


# ─────────────────────────────────────────────
# DATA QUALITY
# ─────────────────────────────────────────────

class DataQuality(str, Enum):
    """Data quality classification.
    
    Rule: Every observation must carry a quality label.
    OBSERVED = directly measured from market
    INFERRED = derived from observed data
    UNAVAILABLE = cannot be obtained
    """
    OBSERVED = "observed"
    INFERRED = "inferred"
    UNAVAILABLE = "unavailable"


class Confidence(str, Enum):
    """Confidence levels for inferred data."""
    HIGH = "high"           # [0.8, 1.0]
    MODERATE = "moderate"   # [0.6, 0.8)
    LOW = "low"             # [0.4, 0.6)
    VERY_LOW = "very_low"   # [0.2, 0.4)
    NONE = "none"           # [0.0, 0.2)


# ─────────────────────────────────────────────
# DIRECTION
# ─────────────────────────────────────────────

class Direction(str, Enum):
    """Trade direction."""
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


class StructureState(str, Enum):
    """Market structure state from Phase 2."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    TRANSITION = "transition"
    COMPRESSION = "compression"
    NEUTRAL = "neutral"


class SwingType(str, Enum):
    """Swing point type."""
    HIGH = "high"
    LOW = "low"


# ─────────────────────────────────────────────
# REGIME
# ─────────────────────────────────────────────

class MarketRegime(str, Enum):
    """Market regime from Phase 9."""
    NORMAL_TREND = "normal_trend"
    RANGE = "range"
    BREAKOUT = "breakout"
    HIGH_VOLATILITY = "high_volatility"
    LIQUIDITY_SWEEP = "liquidity_sweep"
    NEWS = "news"
    POST_NEWS = "post_news"
    LOW_LIQUIDITY = "low_liquidity"
    TRANSITION = "transition"


# ─────────────────────────────────────────────
# FLOW
# ─────────────────────────────────────────────

class FlowState(str, Enum):
    """Flow state from Phase 4."""
    BUYING = "buying"
    SELLING = "selling"
    ABSORPTION = "absorption"
    EXHAUSTION = "exhaustion"
    CONTINUATION = "continuation"
    NEUTRAL = "neutral"


class VolumeSource(str, Enum):
    """Volume data source."""
    EXCHANGE = "exchange"
    BROKER_REAL = "broker_real"
    COMPOSITE = "composite"
    TICK_PROXY = "tick_proxy"
    NONE = "none"


# ─────────────────────────────────────────────
# DECISION
# ─────────────────────────────────────────────

class DecisionType(str, Enum):
    """Final decision from Phase 15."""
    LONG = "long"
    SHORT = "short"
    NO_TRADE = "no_trade"


class SetupType(str, Enum):
    """Entry trigger type from Phase 11."""
    BOS = "bos"
    RETEST = "retest"
    MSS = "mss"
    CANDLE = "candle"


class ExitReason(str, Enum):
    """Trade exit reason from Phase 13."""
    TP1 = "tp1"
    TP2 = "tp2"
    TP3 = "tp3"
    SL = "sl"
    TRAILING = "trailing"
    BREAK_EVEN = "break_even"
    EMERGENCY = "emergency"
    MANUAL = "manual"
    TIMEOUT = "timeout"


# ─────────────────────────────────────────────
# NO-TRADE SEVERITY
# ─────────────────────────────────────────────

class NoTradeSeverity(IntEnum):
    """No-trade severity levels from Phase 14."""
    GREEN = 0       # All normal
    YELLOW = 1      # Warning
    ORANGE = 2      # Significant risk
    RED = 3         # High risk — block
    CRITICAL = 4    # Extreme risk — halt


# ─────────────────────────────────────────────
# EXECUTION
# ─────────────────────────────────────────────

class OrderType(str, Enum):
    """Order type."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(str, Enum):
    """Order side."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Order status."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PositionStatus(str, Enum):
    """Position status."""
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


# ─────────────────────────────────────────────
# NEWS
# ─────────────────────────────────────────────

class NewsCategory(str, Enum):
    """News event category from Phase 7."""
    CPI = "cpi"
    NFP = "nfp"
    FOMC = "fomc"
    RATES = "rates"
    GDP = "gdp"
    PMI = "pmi"
    RETAIL = "retail"
    CLAIMS = "claims"
    YIELDS = "yields"
    OTHER = "other"


class NewsImpact(IntEnum):
    """News event importance level."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# ─────────────────────────────────────────────
# SESSION
# ─────────────────────────────────────────────

class SessionType(str, Enum):
    """Trading session type."""
    ASIAN = "asian"
    LONDON = "london"
    OVERLAP = "overlap"
    NEW_YORK = "newyork"
    OFF_SESSION = "off_session"


# ─────────────────────────────────────────────
# TIMEFRAME
# ─────────────────────────────────────────────

class Timeframe(str, Enum):
    """Supported timeframes."""
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"


# ─────────────────────────────────────────────
# EVIDENCE FAMILIES
# ─────────────────────────────────────────────

class EvidenceFamily(str, Enum):
    """Evidence family identifiers from Phase 10."""
    STRUCTURE = "structure"
    LIQUIDITY = "liquidity"
    FLOW = "flow"
    TREND_MOMENTUM = "trend_momentum"
    MACRO = "macro"
    HISTORICAL = "historical"
    VOLATILITY = "volatility"
    CONTEXT = "context"
