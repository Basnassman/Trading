"""Configuration hierarchy for the XAUUSD Trading System.

Configuration is separated into categories:
- Fixed: Instrument, timeframes, timezone (immutable)
- Initial: Phase 17 optimization targets (mutable with versioning)
- Risk: Risk limits (mutable with approval)
- Execution: Execution parameters (mutable with versioning)
- Backtest: Backtest-specific settings

Secrets are NEVER stored in configuration files.
Secrets are only via environment variables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class FixedConfig:
    """Immutable system configuration."""
    instrument: str = "XAUUSD"
    primary_timeframe: str = "M5"
    analysis_timeframes: tuple[str, ...] = ("D1", "H4", "H1", "M15", "M5")
    timezone: str = "UTC"
    contract_size: int = 100  # oz per lot


@dataclass(frozen=True)
class DataConfig:
    """Data source configuration."""
    mt5_server: str = ""  # From env var
    mt5_login: str = ""  # From env var
    fred_api_key: str = ""  # From env var
    
    # Freshness thresholds (seconds)
    market_data_max_age: int = 300
    tick_data_max_age: int = 60
    dxy_max_age: int = 600
    yield_max_age: int = 86400
    
    # Volume
    volume_source_priority: tuple[str, ...] = ("exchange", "broker_real", "composite", "tick_proxy")


@dataclass(frozen=True)
class FeatureConfig:
    """Feature engineering configuration."""
    # Structure
    fractal_k: int = 3
    bos_tolerance_atr: float = 0.05
    mss_tolerance_atr: float = 0.10
    
    # Liquidity
    eqhl_tolerance_atr: float = 0.10
    cluster_distance_atr: float = 0.15
    sweep_return_bars: int = 5
    sweep_penetration_min: float = 0.02
    
    # Flow
    rvol_lookback: int = 20
    pressure_smoothing: int = 3
    acceleration_lookback: int = 5
    exhaustion_rvol_threshold: float = 2.5
    absorption_rvol_threshold: float = 1.5
    
    # Trend/Momentum/Volatility
    ema_fast: int = 20
    ema_slow: int = 50
    rsi_period: int = 14
    atr_period: int = 14
    
    # GSI
    gsi_structure_weight: float = 0.25
    gsi_flow_weight: float = 0.20
    gsi_trend_weight: float = 0.15
    gsi_momentum_weight: float = 0.15
    gsi_pa_weight: float = 0.15
    gsi_volatility_weight: float = 0.10
    gsi_smoothing: int = 3
    
    # Regime
    regime_lookback: int = 20
    regime_stability_threshold: float = 0.70
    regime_transition_bars: int = 5
    trend_adx_threshold: float = 25.0
    range_atr_threshold: float = 0.8
    breakout_atr_threshold: float = 1.5


@dataclass(frozen=True)
class ModelConfig:
    """Model and probability configuration."""
    # Evidence Families
    family_weights: dict[str, float] = field(default_factory=lambda: {
        "structure": 0.20,
        "flow": 0.18,
        "trend_momentum": 0.15,
        "macro": 0.15,
        "historical": 0.15,
        "liquidity": 0.10,
        "volatility": 0.04,
        "context": 0.03,
    })
    
    # Bayesian
    prior_p_long: float = 0.33
    prior_p_short: float = 0.33
    prior_p_no_trade: float = 0.34
    likelihood_sensitivity: float = 0.5
    
    # Calibration
    calibration_window: int = 500
    min_ece: float = 0.10
    
    # Historical
    k_neighbors: int = 250
    k_search: int = 500
    similarity_threshold: float = 0.80
    outcome_horizon: int = 15
    outcome_target_atr: float = 2.0
    outcome_stop_atr: float = 1.0


@dataclass(frozen=True)
class RiskConfig:
    """Risk management configuration."""
    risk_per_trade: float = 0.01
    max_daily_loss: float = 0.05
    max_weekly_loss: float = 0.10
    max_monthly_loss: float = 0.15
    max_drawdown: float = 0.20
    max_positions: int = 5
    max_exposure: float = 0.50
    max_single_direction: float = 0.30
    
    min_lot_size: float = 0.01
    max_lot_size: float = 5.0
    
    sl_buffer_atr: float = 0.05


@dataclass(frozen=True)
class ExecutionConfig:
    """Trade management configuration."""
    # TP levels
    tp1_multiplier: float = 1.0
    tp2_multiplier: float = 2.0
    tp3_multiplier: float = 3.0
    tp1_ratio: float = 0.50
    tp2_ratio: float = 0.30
    tp3_ratio: float = 0.20
    
    # Break-even
    be_trigger_atr: float = 1.0
    be_buffer_atr: float = 0.05
    
    # Trailing
    trail_fixed_atr: float = 1.0
    trail_step_atr: float = 0.25
    
    # Emergency
    emergency_drop_atr: float = 3.0
    emergency_time_bars: int = 3


@dataclass(frozen=True)
class SetupConfig:
    """Setup engine configuration."""
    min_p_action: float = 0.55
    min_gsi_alignment: float = 30.0
    min_rr_ratio: float = 1.5
    min_flow_score: float = 20.0
    max_spread_pips: float = 2.0
    setup_expiry_bars: int = 10


@dataclass(frozen=True)
class NoTradeConfig:
    """No-trade condition configuration."""
    spread_alert_pips: float = 1.5
    spread_halt_pips: float = 3.0
    vol_alert_threshold: float = 1.5
    vol_halt_threshold: float = 2.5
    news_block_pre_min: int = 60
    news_block_post_min: int = 30
    min_rr_ratio: float = 1.5
    min_liquidity_score: float = 30.0
    max_conflicting_families: int = 3
    uncertain_regime_threshold: float = 0.50


@dataclass(frozen=True)
class BacktestConfig:
    """Backtest-specific configuration."""
    # Data splits
    training_start: str = "2016-01-01"
    training_end: str = "2020-12-31"
    validation_start: str = "2021-01-01"
    validation_end: str = "2022-12-31"
    test_start: str = "2023-01-01"
    test_end: str = "2026-08-31"
    
    # Walk-forward
    wf_train_years: int = 3
    wf_test_years: int = 1
    wf_step_years: int = 1
    wf_purge_bars: int = 100
    
    # Execution simulation
    slippage_pips: float = 0.5
    commission_per_lot: float = 7.0
    
    # Monte Carlo
    mc_runs: int = 1000
    bootstrap_samples: int = 1000


@dataclass(frozen=True)
class SystemConfig:
    """Complete system configuration."""
    fixed: FixedConfig = field(default_factory=FixedConfig)
    data: DataConfig = field(default_factory=DataConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    setup: SetupConfig = field(default_factory=SetupConfig)
    no_trade: NoTradeConfig = field(default_factory=NoTradeConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    
    config_version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)


def load_config_from_yaml(path: str) -> SystemConfig:
    """Load configuration from YAML file.
    
    Implementation will be added in data layer phase.
    """
    raise NotImplementedError("Configuration loading not yet implemented")


def load_config_from_env() -> DataConfig:
    """Load data config from environment variables.
    
    Environment variables:
        DATABASE_URL
        MT5_LOGIN
        MT5_PASSWORD
        MT5_SERVER
        FRED_API_KEY
    """
    import os
    return DataConfig(
        mt5_server=os.getenv("MT5_SERVER", ""),
        mt5_login=os.getenv("MT5_LOGIN", ""),
        fred_api_key=os.getenv("FRED_API_KEY", ""),
    )
