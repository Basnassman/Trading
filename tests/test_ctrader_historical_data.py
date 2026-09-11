"""Unit tests for the cTrader Gate 4 historical data pure helpers.

Credential-free and network-free: they exercise only the pure conversion,
reconstruction, validation, ordering, and mapping helpers in
tools/ctrader_smoke_test/historical_data.py. No private credentials appear
in fixtures.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from tools.ctrader_smoke_test.historical_data import (
    TIMEFRAME_MINUTES,
    BarRecord,
    analyze_series,
    build_raw_bar,
    convert_ctrader_price,
    reconstruct_ohlc,
    trendbar_ts_to_utc,
    validate_bar,
    validate_ohlc,
)


# ── Timestamp conversion ─────────────────────────────────────────────────────

def test_trendbar_timestamp_minutes_to_utc():
    """utcTimestampInMinutes = minutes since Unix epoch UTC (bar open time)."""
    dt = trendbar_ts_to_utc(29_803_875)  # 2026-09-11T05:25:00Z (minutes)
    assert dt is not None
    assert dt.tzinfo is not None
    assert dt.utcoffset() == timedelta(0)
    assert int(dt.timestamp() // 60) == 29_803_875


def test_trendbar_timestamp_none_maps_to_none():
    assert trendbar_ts_to_utc(None) is None


def test_bar_open_time_aligns_to_interval():
    """Bar open times must align to the timeframe interval grid."""
    minutes = 29_803_875  # divisible by 5
    rec = _make_bar(ts_minutes=minutes, timeframe="M5")
    bt = rec.bar_time
    assert bt.minute % 5 == 0
    assert bt.second == 0 and bt.microsecond == 0


# ── Price conversion & trendbar reconstruction ───────────────────────────────

def test_convert_price_exact_decimal():
    assert convert_ctrader_price(433_755_000, 2) == Decimal("4337.55")
    assert convert_ctrader_price(None, 2) is None


def test_reconstruct_ohlc_official_formula():
    """Official Spotware formula: round((low + delta)/100000, digits).

    Deltas share the SAME 1/100000 scale as low (verified from installed
    SDK 0.9.2 descriptors): delta 1_000 = +0.01 on a 2-digit symbol.
    """
    o = reconstruct_ohlc(low=433_755_000, delta_open=1_000,
                         delta_close=3_000, delta_high=5_000, digits=2)
    assert o["low"] == Decimal("4337.55")
    assert o["open"] == Decimal("4337.56")
    assert o["close"] == Decimal("4337.58")
    assert o["high"] == Decimal("4337.60")


def test_reconstruct_ohlc_zero_deltas():
    """Flat bar: all deltas zero → O=H=L=C=low."""
    o = reconstruct_ohlc(433_755_000, 0, 0, 0, 2)
    assert o["open"] == o["high"] == o["low"] == o["close"] == Decimal("4337.55")


# ── OHLC validation ──────────────────────────────────────────────────────────

def test_validate_ohlc_valid_bar():
    o, h, l, c = Decimal("4337.56"), Decimal("4337.60"), Decimal("4337.55"), Decimal("4337.58")
    assert validate_ohlc(o, h, l, c) == []


def test_validate_ohlc_high_below_open():
    errs = validate_ohlc(Decimal("4337.60"), Decimal("4337.55"),
                         Decimal("4337.50"), Decimal("4337.58"))
    assert any("high" in e for e in errs)


def test_validate_ohlc_low_above_close():
    errs = validate_ohlc(Decimal("4337.56"), Decimal("4337.60"),
                         Decimal("4337.57"), Decimal("4337.58"))
    assert any("low" in e for e in errs)


def test_validate_ohlc_non_positive():
    errs = validate_ohlc(Decimal("0"), Decimal("4337.60"),
                         Decimal("4337.55"), Decimal("4337.58"))
    assert any("non-positive" in e for e in errs)


# ── BarRecord + full bar validation ──────────────────────────────────────────

def _make_bar(ts_minutes=None, timeframe="M5", **overrides) -> BarRecord:
    if ts_minutes is None:
        ts_minutes = int(datetime.now(timezone.utc).timestamp() // 60) - 30
        ts_minutes -= ts_minutes % TIMEFRAME_MINUTES[timeframe]
    defaults = dict(
        timeframe=timeframe,
        symbol_id=41,
        ts_minutes=ts_minutes,
        low_raw=433_755_000,
        delta_open_raw=1_000,    # +0.01 at 1/100000 scale
        delta_close_raw=3_000,   # +0.03
        delta_high_raw=5_000,    # +0.05
        volume=123,
        digits=2,
    )
    defaults.update(overrides)
    return BarRecord(**defaults)


def test_valid_bar_passes_validation():
    rec = _make_bar()
    errs = validate_bar(rec)
    assert errs == []
    assert rec.ohlc["open"] == Decimal("4337.56")


def test_future_bar_time_is_invalid():
    future_minutes = int((datetime.now(timezone.utc) + timedelta(days=2)).timestamp() // 60)
    rec = _make_bar(ts_minutes=future_minutes)
    errs = validate_bar(rec)
    assert any("future" in e for e in errs)


def test_bar_keeps_raw_values_for_audit():
    rec = _make_bar()
    assert rec.low_raw == 433_755_000
    assert rec.delta_high_raw == 5_000
    assert rec.ohlc["high"] == Decimal("4337.60")


# ── Series analysis: ordering / duplicates / gaps ────────────────────────────

def _minutes(n_bars: int, interval: int, start_minutes=None) -> list[int]:
    if start_minutes is None:
        start_minutes = int(datetime.now(timezone.utc).timestamp() // 60) - n_bars * interval
        start_minutes -= start_minutes % interval
    return [start_minutes + i * interval for i in range(n_bars)]


def _series(minutes_list, timeframe="M5") -> list[BarRecord]:
    return [_make_bar(ts_minutes=m, timeframe=timeframe) for m in minutes_list]


def test_timeframe_interval_table():
    assert TIMEFRAME_MINUTES == {"M5": 5, "M15": 15, "H1": 60, "H4": 240, "D1": 1440}


def test_perfectly_continuous_series_no_anomalies():
    bars = _series(_minutes(20, 5))
    r = analyze_series(bars, 5)
    assert r["count"] == 20
    assert r["ordered"] is True
    assert r["duplicates"] == 0 and r["reversed"] == 0 and r["overlaps"] == 0
    assert r["session_gaps"] == 0


def test_duplicate_detection():
    ms = _minutes(10, 5)
    ms[5] = ms[4]  # duplicate timestamp
    r = analyze_series(_series(ms), 5)
    assert r["duplicates"] == 1
    assert r["ordered"] is False
    assert any("duplicate" in a for a in r["anomalies"])


def test_reversed_timestamp_detection():
    ms = _minutes(10, 5)
    ms[5], ms[6] = ms[6], ms[5]  # swap → local descent
    r = analyze_series(_series(ms), 5)
    assert r["reversed"] >= 1
    assert any("reversed" in a for a in r["anomalies"])


def test_session_gap_classified_not_malformed():
    """A weekend in D1 bars = 1 legitimate session gap.

    Friday bar → Monday bar spans 3 daily spacings (Fri→Sat→Sun→Mon);
    bars from the weekend onward are shifted by 2 days.
    """
    ms = _minutes(10, 1440, start_minutes=29_000_000)
    for i in range(5, len(ms)):
        ms[i] += 2 * 1440  # weekend: shift tail by 2 days
    r = analyze_series(_series(ms, timeframe="D1"), 1440)
    assert r["session_gaps"] == 1
    assert r["max_gap_minutes"] == 3 * 1440
    assert r["ordered"] is True  # gaps are NOT ordering violations


def test_non_multiple_jump_flagged_as_anomaly():
    """Jump of 7 min on M5 grid is not an integer multiple → anomaly."""
    ms = _minutes(10, 5)
    ms[5] += 7
    r = analyze_series(_series(ms), 5)
    assert any("non-multiple jump" in a for a in r["anomalies"])


def test_misaligned_bars_detected():
    ms = _minutes(10, 5)
    ms[3] += 2  # off-grid open time
    r = analyze_series(_series(ms), 5)
    assert r["misaligned_bars"] == 1


def test_empty_series():
    r = analyze_series([], 5)
    assert r["count"] == 0 and r["ordered"] is True


# ── RawBar mapping (existing contract, unchanged) ────────────────────────────

def test_build_raw_bar_uses_existing_contract_unchanged():
    from src.canonical.raw import RawBar

    rec = _make_bar(timeframe="M15")
    raw = build_raw_bar(rec)
    assert isinstance(raw, RawBar)
    assert raw.symbol == "XAUUSD"
    assert raw.timeframe == "M15"
    assert raw.open == Decimal("4337.56")
    assert raw.high == Decimal("4337.60")
    assert raw.low == Decimal("4337.55")
    assert raw.close == Decimal("4337.58")
    assert raw.tick_volume == 123
    assert raw.real_volume is None
    assert raw.provider == "ctrader"
    assert raw.provider_symbol == "XAUUSD"


def test_raw_bar_temporal_semantics_preserved():
    """bar_time=event_time (market), retrieval_time=ingestion (fetch) — and
    retrieval must be >= event_time for a historical fetch (no look-ahead)."""
    rec = _make_bar()
    raw = build_raw_bar(rec)
    assert raw.bar_time == rec.bar_time
    assert raw.retrieval_time >= raw.bar_time
    assert raw.bar_time.tzinfo is not None
    assert raw.retrieval_time.tzinfo is not None


def test_raw_bar_mapping_requires_bar_time():
    rec = _make_bar(ts_minutes=None)
    rec.ts_minutes = None  # force missing
    with pytest.raises(AssertionError):
        build_raw_bar(rec)
