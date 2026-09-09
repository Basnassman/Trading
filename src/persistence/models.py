"""SQLAlchemy database models for the XAUUSD Trading System.

These models define the database schema for the data layer.
Only data-layer tables are included in this phase.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text,
    ForeignKey, UniqueConstraint, Index, Numeric,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class MarketBar(Base):
    """OHLCV bar data."""
    __tablename__ = "market_bars"
    
    bar_id = Column(String(255), primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)
    
    open = Column(Numeric(20, 8), nullable=False)
    high = Column(Numeric(20, 8), nullable=False)
    low = Column(Numeric(20, 8), nullable=False)
    close = Column(Numeric(20, 8), nullable=False)
    tick_volume = Column(Integer, nullable=False)
    real_volume = Column(Integer, nullable=True)
    
    spread_at_close = Column(Numeric(10, 4), nullable=True)
    bid_at_close = Column(Numeric(20, 8), nullable=True)
    ask_at_close = Column(Numeric(20, 8), nullable=True)
    
    bar_time = Column(DateTime(timezone=True), nullable=False, index=True)
    availability_time = Column(DateTime(timezone=True), nullable=False)
    ingestion_time = Column(DateTime(timezone=True), nullable=False)
    
    data_quality = Column(String(20), nullable=False, default="observed")
    version = Column(String(20), nullable=False, default="1.0")
    
    provider = Column(String(50), nullable=True)
    provider_symbol = Column(String(50), nullable=True)
    
    __table_args__ = (
        UniqueConstraint("symbol", "timeframe", "bar_time", name="uq_bar_symbol_tf_time"),
        Index("ix_bar_time", "bar_time"),
    )


class Tick(Base):
    """Tick data."""
    __tablename__ = "ticks"
    
    tick_id = Column(String(255), primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    
    bid = Column(Numeric(20, 8), nullable=False)
    ask = Column(Numeric(20, 8), nullable=False)
    spread = Column(Numeric(10, 4), nullable=False)
    volume = Column(Integer, nullable=True)
    
    tick_time = Column(DateTime(timezone=True), nullable=False, index=True)
    availability_time = Column(DateTime(timezone=True), nullable=False)
    ingestion_time = Column(DateTime(timezone=True), nullable=False)
    
    data_quality = Column(String(20), nullable=False, default="observed")
    version = Column(String(20), nullable=False, default="1.0")
    
    provider = Column(String(50), nullable=True)
    
    __table_args__ = (
        UniqueConstraint("symbol", "tick_time", name="uq_tick_symbol_time"),
    )


class Spread(Base):
    """Spread observations."""
    __tablename__ = "spreads"
    
    spread_id = Column(String(255), primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    
    spread_pips = Column(Numeric(10, 4), nullable=False)
    spread_absolute = Column(Numeric(20, 8), nullable=False)
    
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    ingestion_time = Column(DateTime(timezone=True), nullable=False)
    
    provider = Column(String(50), nullable=True)


class DataSource(Base):
    """Data source metadata."""
    __tablename__ = "data_sources"
    
    source_id = Column(String(255), primary_key=True)
    source_name = Column(String(100), nullable=False)
    source_type = Column(String(50), nullable=False)  # "broker", "api", "csv"
    
    instrument = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=True)
    
    date_from = Column(DateTime(timezone=True), nullable=True)
    date_to = Column(DateTime(timezone=True), nullable=True)
    
    record_count = Column(Integer, nullable=True)
    data_quality = Column(String(20), nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False)
    version = Column(String(20), nullable=False)


class DataQualityRecord(Base):
    """Data quality tracking."""
    __tablename__ = "data_quality"
    
    quality_id = Column(String(255), primary_key=True)
    source_id = Column(String(255), ForeignKey("data_sources.source_id"))
    
    total_records = Column(Integer, nullable=False)
    valid_records = Column(Integer, nullable=False)
    warning_records = Column(Integer, nullable=False)
    invalid_records = Column(Integer, nullable=False)
    
    missing_bars = Column(Integer, nullable=True)
    duplicate_records = Column(Integer, nullable=True)
    
    completeness_pct = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    
    checked_at = Column(DateTime(timezone=True), nullable=False)


class IngestionRun(Base):
    """Ingestion run tracking for reproducibility."""
    __tablename__ = "ingestion_runs"
    
    run_id = Column(String(255), primary_key=True)
    
    source = Column(String(100), nullable=False)
    instrument = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=True)
    
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    record_count = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    
    configuration_version = Column(String(20), nullable=True)
    schema_version = Column(String(20), nullable=True)
    
    status = Column(String(20), nullable=False, default="running")  # running, completed, failed
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False)
