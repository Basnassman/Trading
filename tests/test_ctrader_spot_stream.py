"""Unit tests for the cTrader Gate 3 spot stream pure helpers.

These tests are credential-free and network-free: they exercise only the
pure conversion/validation/mapping helpers in
tools/ctrader_smoke_test/spot_stream.py, which import without Twisted and
never touch the network. No private credentials appear in fixtures.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from tools.ctrader_smoke_test.spot_stream import (
    CTRADER_PRICE_SCALE_DENOMINATOR,
    SpotEventRecord,
    build_raw_tick,
    convert_ctrader_price,
    spot_timestamp_to_utc,
    summarize,
)


# ── Price conversion ─────────────────────────────────────────────────────────

def test_price_scale_denominator_matches_spotware_documentation():
    """cTrader represents prices in 1/100000 units (Spotware docs)."""
    assert CTRADER_PRICE_SCALE_DENOMINATOR == 100_000


def test_convert_price_xauusd_digits2():
    """round(raw / 100000, digits) for XAUUSD (digits=2)."""
    assert convert_ctrader_price(433_755_000, 2) == Decimal("4337.55")
    assert convert_ctrader_price(433_751_000, 2) == Decimal("4337.51")
    assert convert_ctrader_price(433_765_000, 2) == Decimal("4337.65")


def test_convert_price_returns_none_for_missing_field():
    """bid/ask are optional proto2 fields; None must map to None."""
    assert convert_ctrader_price(None, 2) is None


def test_convert_price_is_exact_decimal_no_binary_float_artifacts():
    """Exact decimal arithmetic: no 4337.5500000000001-style artifacts."""
    result = convert_ctrader_price(433_755_000, 2)
    assert isinstance(result, Decimal)
    assert str(result) == "4337.55"
    assert result.as_tuple().exponent == -2


# ── Timestamp conversion ─────────────────────────────────────────────────────

def test_spot_timestamp_ms_converts_to_utc():
    """cTrader SpotEvent timestamps are Unix epoch MILLISECONDS."""
    dt = spot_timestamp_to_utc(1_788_182_000_000)
    assert dt is not None
    assert dt.tzinfo is not None  # timezone-aware
    assert dt.utcoffset() == timedelta(0)  # normalized to UTC
    assert int(dt.timestamp() * 1000) == 1_788_182_000_000


def test_spot_timestamp_none_maps_to_none():
    assert spot_timestamp_to_utc(None) is None


# ── Event validation (data quality) ──────────────────────────────────────────

def _make_record(**overrides) -> SpotEventRecord:
    now = datetime.now(timezone.utc)
    defaults = dict(
        symbol_id=41,
        bid_raw=433_755_000,
        ask_raw=433_765_000,
        timestamp_ms=int(now.timestamp() * 1000) - 1_500,
        ingestion_time=now,
        digits=2,
    )
    defaults.update(overrides)
    rec = SpotEventRecord(**defaults)
    rec.validate()
    return rec


def test_valid_event_passes_all_quality_checks():
    rec = _make_record()
    assert rec.validation_errors == []
    assert rec.validation_warnings == []
    assert rec.bid == Decimal("4337.55")
    assert rec.ask == Decimal("4337.65")
    assert rec.spread == Decimal("0.10")
    assert rec.event_time is not None


def test_ask_below_bid_is_invalid():
    rec = _make_record(bid_raw=433_765_000, ask_raw=433_755_000)
    assert any("ask < bid" in e for e in rec.validation_errors)


def test_missing_bid_and_ask_reported_not_discarded():
    rec = _make_record(bid_raw=None, ask_raw=None)
    assert any("missing bid" in e for e in rec.validation_errors)
    assert any("missing ask" in e for e in rec.validation_errors)
    # spread must be None, not crash
    assert rec.spread is None


def test_non_positive_prices_are_invalid():
    rec = _make_record(bid_raw=0, ask_raw=-5)
    assert any("non-positive bid" in e for e in rec.validation_errors)
    assert any("non-positive ask" in e for e in rec.validation_errors)


def test_missing_server_timestamp_is_warning_not_silent():
    rec = _make_record(timestamp_ms=None)
    assert rec.validation_errors == []
    assert any("missing server event timestamp" in w
               for w in rec.validation_warnings)


def test_future_event_time_is_invalid():
    now = datetime.now(timezone.utc)
    future_ms = int((now + timedelta(hours=1)).timestamp() * 1000)
    rec = _make_record(timestamp_ms=future_ms, ingestion_time=now)
    assert any("impossible future event_time" in e for e in rec.validation_errors)


def test_stale_event_time_is_invalid():
    now = datetime.now(timezone.utc)
    stale_ms = int((now - timedelta(hours=25)).timestamp() * 1000)
    rec = _make_record(timestamp_ms=stale_ms, ingestion_time=now)
    assert any("stale event_time" in e for e in rec.validation_errors)


# ── RawTick mapping (existing contract, unchanged) ───────────────────────────

def test_build_raw_tick_uses_existing_contract_unchanged():
    from src.canonical.raw import RawTick

    rec = _make_record()
    tick = build_raw_tick(rec)
    assert isinstance(tick, RawTick)
    assert tick.symbol == "XAUUSD"
    assert tick.bid == Decimal("4337.55")
    assert tick.ask == Decimal("4337.65")
    assert tick.provider == "ctrader"
    assert tick.provider_symbol == "XAUUSD"


def test_raw_tick_temporal_semantics_preserved():
    """timestamp=event_time, retrieval_time=ingestion_time — never swapped."""
    rec = _make_record()
    tick = build_raw_tick(rec)
    assert tick.timestamp == rec.event_time
    assert tick.retrieval_time == rec.ingestion_time
    assert tick.timestamp.tzinfo is not None
    assert tick.retrieval_time.tzinfo is not None
    # event_time must not be in the future (temporal rule)
    assert tick.timestamp <= datetime.now(timezone.utc) + timedelta(seconds=2)


def test_raw_tick_mapping_requires_event_time():
    """RawTick.timestamp is required; events without event_time are NOT
    silently mapped — the helper refuses instead of inventing a timestamp."""
    rec = _make_record(timestamp_ms=None)
    with pytest.raises(AssertionError):
        build_raw_tick(rec)


# ── Summarization ────────────────────────────────────────────────────────────

def test_summarize_ranges_and_counts():
    events = [
        _make_record(bid_raw=433_751_000, ask_raw=433_761_000),
        _make_record(bid_raw=433_755_000, ask_raw=433_765_000),
    ]
    s = summarize(events)
    assert s["received"] == 2
    assert s["valid"] == 2
    assert s["invalid"] == 0
    assert s["symbol_ids"] == [41]
    assert s["bid_range"] == (Decimal("4337.51"), Decimal("4337.55"))
    assert s["ask_range"] == (Decimal("4337.61"), Decimal("4337.65"))
    assert s["spread_range"] == (Decimal("0.10"), Decimal("0.10"))
    assert s["event_times_ordered"] is True
    assert s["no_future_event_time"] is True


def test_summarize_counts_invalid_events_explicitly():
    good = _make_record()
    bad = _make_record(bid_raw=None, ask_raw=None)
    s = summarize([good, bad])
    assert s["received"] == 2
    assert s["valid"] == 1
    assert s["invalid"] == 1
    assert s["invalid_reasons"]


def test_summarize_empty_sample():
    s = summarize([])
    assert s["received"] == 0
    assert s["valid"] == 0
    assert s["event_times_ordered"] is False
