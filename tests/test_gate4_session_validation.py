"""Credential-free, deterministic tests for the Gate 4 approved change.

Scope (per approval):
1.  Existing UTC-midnight fallback preserved (schedule=None) — via BOTH
    src/validation/validators.py and the Gate 4 smoke-test layer.
2.  IC-style session schedule (17:00 America/New_York daily roll, supplied
    as plain schedule metadata — no broker names inside production code).
3.  EDT regime anchor; 4. EST regime anchor.
5.  Real DST transitions (2026 spring-forward / fall-back).
6.  Valid H4/D1 bars accepted on the session-derived grid.
7.  Deliberately shifted bars rejected.
8.  Session gaps classified as gaps — never as misalignment.
9.  Raw timestamps preserved verbatim (never shifted/re-stamped).
10. ONE shared alignment algorithm: TemporalValidator delegates to
    src/validation/session_alignment.py (the same model used by
    analyze_series) — two independent implementations are forbidden.
11. Schedule metadata is the sole source of the alignment policy: the
    smoke-test layer contains no broker names, offsets or DST constants.

No credentials, no network, no clock reads in assertions (fixed dates).
"""

from __future__ import annotations

import copy
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.canonical.raw import RawBar
from src.validation.session_alignment import (
    TIMEFRAME_MINUTES,
    SessionSchedule,
    TemporalAlignmentValidator,
)
from src.validation.validators import TemporalValidator
from tools.ctrader_smoke_test.historical_data import (
    TIMEFRAME_MINUTES as SMOKE_TIMEFRAME_MINUTES,
    BarRecord,
    analyze_series,
    build_session_schedule,
    schedule_from_proto_symbol,
    summarize_timeframe,
)

UTC = timezone.utc
SEC_PER_DAY = 86_400


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures: provider-reported schedule metadata as PLAIN DATA
# (week-anchored seconds, 0 = Sunday 00:00 schedule-TZ; start inclusive,
#  end exclusive — per the provider Open API proto semantics)
# ─────────────────────────────────────────────────────────────────────────────

def ic_style_schedule() -> SessionSchedule:
    """Session schedule mirroring the reconciled metadata shape: intervals
    Sun–Thu 18:02 → next day 16:59 in America/New_York (daily roll 17:00
    local). Plain data — the validators know nothing about any broker."""
    return SessionSchedule(
        schedule_tz_name="America/New_York",
        intervals_week_seconds=(
            (64920, 147540),      # Sun 18:02 → Mon 16:59
            (151320, 233940),     # Mon 18:02 → Tue 16:59
            (237720, 320340),     # Tue 18:02 → Wed 16:59
            (324120, 406740),     # Wed 18:02 → Thu 16:59
            (410520, 493020),     # Thu 18:02 → Fri 16:57
        ),
    )


@pytest.fixture(scope="module")
def sched() -> SessionSchedule:
    return ic_style_schedule()


@pytest.fixture(scope="module")
def session_validator(sched: SessionSchedule) -> TemporalValidator:
    v = TemporalValidator(schedule=sched)
    assert v.alignment_mode == "session"
    return v


def zoneinfo_roll_utc(schedule: SessionSchedule, local_date: date) -> datetime:
    """Expected UTC roll instant for local_date, derived ONLY via zoneinfo
    from the schedule's own local roll time (no offset literals)."""
    roll_sec = schedule.daily_roll_local_second_of_day()
    t = time(roll_sec // 3600, (roll_sec % 3600) // 60, roll_sec % 60)
    return datetime.combine(local_date, t,
                            tzinfo=ZoneInfo(schedule.schedule_tz_name)) \
        .astimezone(UTC)


def aligned_times(schedule: SessionSchedule, timeframe: str,
                  local_dates: list[date], ks: list[int]) -> list[datetime]:
    """Bar-open times ON the session-derived grid: roll(date) + k·period."""
    period = timedelta(minutes=TIMEFRAME_MINUTES[timeframe])
    out = []
    for d in local_dates:
        roll = zoneinfo_roll_utc(schedule, d)
        for k in ks:
            out.append(roll + k * period)
    return sorted(out)


def make_raw_bars(times: list[datetime], timeframe: str) -> list[RawBar]:
    return [RawBar(
        symbol="SYNTH",
        timeframe=timeframe,
        bar_time=t,
        open=Decimal("2400.00"),
        high=Decimal("2401.00"),
        low=Decimal("2399.00"),
        close=Decimal("2400.50"),
        tick_volume=100,
        provider="provider-a",
        provider_symbol="SYNTH",
        retrieval_time=datetime(2026, 9, 12, tzinfo=UTC),
    ) for t in times]


def make_bar_records(times: list[datetime], timeframe: str,
                     shift_last_by_minutes: int = 0) -> list[BarRecord]:
    """BarRecords carrying the given bar-open instants as RAW
    utcTimestampInMinutes values (the smoke-test layer's raw audit field)."""
    records = []
    for i, t in enumerate(times):
        ts_minutes = int(t.timestamp() // 60)
        if i == len(times) - 1:
            ts_minutes += shift_last_by_minutes
        records.append(BarRecord(
            timeframe=timeframe,
            symbol_id=41,
            ts_minutes=ts_minutes,
            low_raw=433_755_000,
            delta_open_raw=1_000,
            delta_close_raw=3_000,
            delta_high_raw=5_000,
            volume=123,
            digits=2,
        ))
    return records


# ─────────────────────────────────────────────────────────────────────────────
# 1. Existing UTC-midnight fallback preserved (schedule=None)
# ─────────────────────────────────────────────────────────────────────────────

class TestFallbackPreserved:
    def test_default_constructor_uses_fallback(self):
        assert TemporalValidator().alignment_mode == "utc_midnight_fallback"

    def test_utc_midnight_grid_aligned_via_validators(self):
        """The pre-existing rule: minutes-since-epoch % period == 0."""
        v = TemporalValidator()
        assert v.alignment_finding(
            datetime(2026, 9, 7, 0, 0, tzinfo=UTC), "H4").aligned
        assert v.alignment_finding(
            datetime(2026, 9, 7, 4, 0, tzinfo=UTC), "H4").aligned
        assert v.alignment_finding(
            datetime(2026, 9, 7, 0, 0, tzinfo=UTC), "D1").aligned
        assert v.alignment_finding(
            datetime(2026, 9, 7, 21, 0, tzinfo=UTC), "H4").aligned is False

    def test_classify_alignment_fallback_matches_legacy_rule(self):
        v = TemporalValidator()
        bars = make_raw_bars([
            datetime(2026, 9, 7, 0, 0, tzinfo=UTC),
            datetime(2026, 9, 7, 4, 0, tzinfo=UTC),
            datetime(2026, 9, 7, 4, 37, tzinfo=UTC),      # off-grid
        ], "H4")
        rep = v.classify_alignment(bars, "H4")
        assert rep["mode"] == "utc_midnight_fallback"
        assert rep["aligned_count"] == 2
        assert len(rep["misaligned"]) == 1

    def test_legacy_ordering_and_gap_methods_unchanged(self):
        """No existing validation was weakened or reinterpreted."""
        v = TemporalValidator()
        bars = make_raw_bars([
            datetime(2026, 9, 4, 20, 0, tzinfo=UTC),      # Fri
            datetime(2026, 9, 7, 0, 0, tzinfo=UTC),       # Mon (weekend gap)
        ], "H4")
        assert v.validate_ordering(bars, "H4").is_valid
        gaps = v.detect_gaps(bars, "H4")
        assert len(gaps) == 1
        assert gaps[0]["type"] == "expected_weekend"

    def test_unresolvable_tz_falls_back(self):
        v = TemporalValidator(schedule=SessionSchedule(
            schedule_tz_name="Mars/Olympus_Mons",
            intervals_week_seconds=((64920, 147540),)))
        assert v.alignment_mode == "utc_midnight_fallback"
        assert v.alignment_finding(
            datetime(2026, 9, 7, 0, 0, tzinfo=UTC), "H4").aligned

    def test_naive_timestamp_rejected_in_both_modes(self, sched):
        naive = datetime(2026, 7, 15, 21, 0)
        assert not TemporalValidator(schedule=sched) \
            .alignment_finding(naive, "H4").aligned
        assert not TemporalValidator() \
            .alignment_finding(naive, "H4").aligned


# ─────────────────────────────────────────────────────────────────────────────
# 2–4. IC-style schedule: EDT / EST anchors
# ─────────────────────────────────────────────────────────────────────────────

class TestSessionAnchors:
    def test_edt_regime_anchor(self, session_validator, sched):
        roll = zoneinfo_roll_utc(sched, date(2026, 7, 15))     # EDT week
        ny = roll.astimezone(ZoneInfo(sched.schedule_tz_name))
        assert (ny.hour, ny.minute) == (17, 0)                 # 17:00 local
        assert ny.utcoffset() == timedelta(hours=-4)           # EDT
        assert (roll.hour, roll.minute) == (21, 0)             # 21:00 UTC
        f = session_validator.alignment_finding(roll, "H4")
        assert f.aligned and f.mode == "session"

    def test_est_regime_anchor(self, session_validator, sched):
        roll = zoneinfo_roll_utc(sched, date(2026, 1, 14))     # EST week
        ny = roll.astimezone(ZoneInfo(sched.schedule_tz_name))
        assert (ny.hour, ny.minute) == (17, 0)                 # 17:00 local
        assert ny.utcoffset() == timedelta(hours=-5)           # EST
        assert (roll.hour, roll.minute) == (22, 0)             # 22:00 UTC
        f = session_validator.alignment_finding(roll, "H4")
        assert f.aligned and f.mode == "session"


# ─────────────────────────────────────────────────────────────────────────────
# 5. Real DST transitions — anchors derived through zoneinfo only
# ─────────────────────────────────────────────────────────────────────────────

class TestDSTTransitions:
    def test_spring_forward_2026(self, session_validator, sched):
        """EST → EDT on 2026-03-08: anchor moves 22:00 → 21:00 UTC through
        zoneinfo alone; each regime's own bars are aligned."""
        fri_est = zoneinfo_roll_utc(sched, date(2026, 3, 6))
        mon_edt = zoneinfo_roll_utc(sched, date(2026, 3, 9))
        assert fri_est.astimezone(ZoneInfo(sched.schedule_tz_name)) \
            .utcoffset() == timedelta(hours=-5)
        assert mon_edt.astimezone(ZoneInfo(sched.schedule_tz_name)) \
            .utcoffset() == timedelta(hours=-4)
        for t in (fri_est, mon_edt):
            assert session_validator.alignment_finding(t, "H4").aligned
            assert session_validator.alignment_finding(t, "D1").aligned
        # Stale (pre-transition) anchor time-of-day after the transition:
        stale = mon_edt.replace(hour=fri_est.hour)             # Mon 22:00 UTC
        assert not session_validator.alignment_finding(stale, "H4").aligned
        assert not session_validator.alignment_finding(stale, "D1").aligned

    def test_fall_back_2026(self, session_validator, sched):
        """EDT → EST on 2026-11-01: anchor moves 21:00 → 22:00 UTC."""
        fri_edt = zoneinfo_roll_utc(sched, date(2026, 10, 30))
        mon_est = zoneinfo_roll_utc(sched, date(2026, 11, 2))
        for t in (fri_edt, mon_est):
            assert session_validator.alignment_finding(t, "D1").aligned
        stale_w = mon_est.replace(hour=fri_edt.hour)           # Mon 21:00 UTC
        assert not session_validator.alignment_finding(stale_w, "H4").aligned
        assert not session_validator.alignment_finding(stale_w, "D1").aligned


# ─────────────────────────────────────────────────────────────────────────────
# 6–8. Valid H4/D1 bars accepted; shifted bars rejected; session gaps
# ─────────────────────────────────────────────────────────────────────────────

class TestSessionModeClassification:
    def test_valid_h4_and_d1_bars_accepted(self, session_validator, sched):
        week = [date(2026, 7, 13), date(2026, 7, 14),
                date(2026, 7, 15), date(2026, 7, 16)]          # Mon–Thu
        for tf, ks in (("H4", [0, 1, 2, 3, 4, 5]), ("D1", [0])):
            for t in aligned_times(sched, tf, week, ks):
                f = session_validator.alignment_finding(t, tf)
                assert f.aligned, (tf, t, f.detail)
                assert f.mode == "session"

    def test_shifted_bars_rejected(self, session_validator, sched):
        roll = zoneinfo_roll_utc(sched, date(2026, 7, 15))     # Wed 21:00 UTC
        for tf, shift in (("H4", timedelta(minutes=100)),
                          ("H4", timedelta(minutes=120)),
                          ("H4", timedelta(minutes=60)),
                          ("D1", timedelta(minutes=60)),
                          ("D1", timedelta(minutes=100))):
            f = session_validator.alignment_finding(roll + shift, tf)
            assert not f.aligned, (tf, shift, f.detail)
        # UTC-midnight grid (the FALLBACK rule's grid) must not pass in
        # session mode — the modes genuinely disagree, no cross-talk.
        midnight = datetime(2026, 7, 16, 0, 0, tzinfo=UTC)
        assert not session_validator.alignment_finding(midnight, "H4").aligned
        assert not session_validator.alignment_finding(midnight, "D1").aligned

    def test_session_gaps_are_gaps_not_misalignment(
            self, session_validator, sched):
        """Aligned bars straddling the weekend → session gap, zero
        misalignment, zero anomalies."""
        times = [zoneinfo_roll_utc(sched, date(2026, 7, 10)),   # Fri roll
                 zoneinfo_roll_utc(sched, date(2026, 7, 10))
                 + timedelta(hours=4),                          # on-grid
                 zoneinfo_roll_utc(sched, date(2026, 7, 13)),   # Mon roll
                 zoneinfo_roll_utc(sched, date(2026, 7, 13))
                 + timedelta(hours=4)]
        bars = make_raw_bars(times, "H4")
        rep = session_validator.classify_alignment(bars, "H4")
        assert rep["mode"] == "session"
        assert rep["aligned_count"] == len(times)
        assert rep["misaligned"] == []
        assert rep["anomalies"] == []
        assert len(rep["session_gaps"]) == 1
        assert rep["session_gaps"][0]["gap_minutes"] \
            % TIMEFRAME_MINUTES["H4"] == 0

    def test_pre_roll_bars_rejected(self, session_validator, sched):
        roll = zoneinfo_roll_utc(sched, date(2026, 7, 15))
        assert not session_validator.alignment_finding(
            roll - timedelta(minutes=120), "H4").aligned


# ─────────────────────────────────────────────────────────────────────────────
# 9. Raw timestamps preserved verbatim
# ─────────────────────────────────────────────────────────────────────────────

class TestRawTimestampsPreserved:
    def test_temporal_validator_never_mutates_bars(
            self, session_validator, sched):
        times = aligned_times(sched, "H4",
                              [date(2026, 7, 13), date(2026, 7, 14)],
                              [0, 1, 2])
        bars = make_raw_bars(times, "H4")
        snapshot = copy.deepcopy(bars)
        for bar in bars:
            f = session_validator.alignment_finding(bar.bar_time, bar.timeframe)
            assert f.bar_time == bar.bar_time
            assert f.bar_time is bar.bar_time            # same object
        rep = session_validator.classify_alignment(bars, "H4")
        for f in rep["misaligned"] or []:
            assert f.bar_time in times
        assert bars == snapshot                          # frozen dataclasses

    def test_analyze_series_never_mutates_raw_records(self, sched):
        times = aligned_times(sched, "H4",
                              [date(2026, 7, 13), date(2026, 7, 14)],
                              [0, 1, 2])
        records = make_bar_records(times, "H4", shift_last_by_minutes=100)
        snapshot = copy.deepcopy(records)
        validator = build_session_schedule("America/New_York",
                                           list(sched.intervals_week_seconds))
        analyze_series(records, 240, schedule=validator, timeframe="H4")
        assert records == snapshot                       # raw ts untouched
        assert [r.ts_minutes for r in records] \
            == [r.ts_minutes for r in snapshot]

    def test_finding_echoes_input_instant_verbatim(self, session_validator):
        t = datetime(2026, 7, 15, 22, 37, tzinfo=UTC)     # deliberately odd
        f = session_validator.alignment_finding(t, "H4")
        assert f.bar_time == t and not f.aligned


# ─────────────────────────────────────────────────────────────────────────────
# 10. ONE shared alignment algorithm (no duplicate implementation)
# ─────────────────────────────────────────────────────────────────────────────

class TestSingleSharedAlgorithm:
    def test_temporal_validator_delegates_to_session_alignment(
            self, sched):
        tv = TemporalValidator(schedule=sched)
        probes = aligned_times(sched, "H4",
                               [date(2026, 3, 6), date(2026, 3, 9),
                                date(2026, 7, 15), date(2026, 11, 2)],
                               [0, 1, 2])
        probes += [t + timedelta(minutes=100) for t in probes[:2]]
        for t in probes:
            shared = TemporalAlignmentValidator(sched).validate_bar_time(t, "H4")
            assert tv.alignment_finding(t, "H4") == shared

    def test_analyze_series_uses_same_model_as_validators(self, sched):
        times = aligned_times(sched, "H4",
                              [date(2026, 7, 13), date(2026, 7, 14)],
                              [0, 1, 2, 3])
        times[-1] = times[-1] + timedelta(minutes=100)   # one shifted bar
        records = make_bar_records(times, "H4")
        validator = build_session_schedule("America/New_York",
                                           list(sched.intervals_week_seconds))
        report = analyze_series(records, 240, schedule=validator,
                                timeframe="H4")
        # Independent computation through the validators.py wrapper:
        tv = TemporalValidator(schedule=sched)
        bars = make_raw_bars(times, "H4")
        expected = tv.classify_alignment(bars, "H4")
        assert report["alignment_mode"] == "session"
        assert report["misaligned_bars"] == len(expected["misaligned"]) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Smoke-test layer: schedule construction from dynamically resolved metadata
# ─────────────────────────────────────────────────────────────────────────────

class _FakeInterval:
    def __init__(self, start: int, end: int) -> None:
        self.startSecond = start
        self.endSecond = end


class _FakeProtoSymbol:
    """Minimal stand-in for a dynamically resolved ProtoOASymbol."""

    def __init__(self, tz_name: str | None,
                 intervals: list[tuple[int, int]]) -> None:
        self._tz_name = tz_name
        self.schedule = [_FakeInterval(s, e) for s, e in intervals]

    def HasField(self, name: str) -> bool:  # noqa: N802 (proto naming)
        return name == "scheduleTimeZone" and self._tz_name is not None

    @property
    def scheduleTimeZone(self) -> str:      # noqa: N802 (proto naming)
        return self._tz_name or ""


class TestScheduleConstruction:
    def test_extracts_metadata_from_resolved_symbol(self):
        sym = _FakeProtoSymbol("America/New_York", [(64920, 147540)])
        tz, intervals = schedule_from_proto_symbol(sym)
        assert tz == "America/New_York"
        assert intervals == [(64920, 147540)]

    def test_absent_metadata_returns_none(self):
        tz, intervals = schedule_from_proto_symbol(_FakeProtoSymbol(None, []))
        assert tz is None and intervals == []
        assert build_session_schedule(tz, intervals) is None

    def test_empty_intervals_do_not_build_schedule(self):
        assert build_session_schedule("America/New_York", []) is None

    def test_builds_validator_from_metadata(self, sched):
        v = build_session_schedule("America/New_York",
                                   list(sched.intervals_week_seconds))
        assert isinstance(v, TemporalAlignmentValidator)
        assert v.mode == "session"

    def test_unresolvable_tz_still_builds_and_falls_back(self):
        v = build_session_schedule("Mars/Olympus_Mons", [(64920, 147540)])
        assert v is not None
        assert v.mode == "utc_midnight_fallback"

    def test_metadata_is_sole_policy_source_in_smoke_layer(self):
        """No broker names, no grid offsets, no DST constants may enter the
        smoke-test layer: scheduleTimeZone/schedule metadata is the ONLY
        source of the session-alignment policy."""
        src = Path("tools/ctrader_smoke_test/historical_data.py") \
            .read_text(encoding="utf-8")
        for token in ("America/New_York", "Europe/London", "Etc/GMT",
                      "1260", "1320", "OBSERVED_OFFSET",
                      "UTC+", "GMT+", "+120", "+60"):
            assert token not in src, \
                f"hardcoded schedule/offset token in smoke layer: {token!r}"

    def test_timeframe_tables_consistent(self):
        assert SMOKE_TIMEFRAME_MINUTES["H4"] == TIMEFRAME_MINUTES["H4"]
        assert SMOKE_TIMEFRAME_MINUTES["D1"] == TIMEFRAME_MINUTES["D1"]


# ─────────────────────────────────────────────────────────────────────────────
# analyze_series / summarize_timeframe with and without schedule
# ─────────────────────────────────────────────────────────────────────────────

class TestAnalyzeSeriesAlignment:
    def test_without_schedule_fallback_report_unchanged(self):
        """No schedule → legacy report shape and legacy UTC-midnight rule."""
        now_minutes = int(datetime(2026, 9, 7, 10, 0,
                                   tzinfo=UTC).timestamp() // 60)
        now_minutes -= now_minutes % 5
        records = make_bar_records(
            [datetime.fromtimestamp((now_minutes + i * 5) * 60, tz=UTC)
             for i in range(10)], "M5")
        records[3].ts_minutes += 2                      # off-grid open
        r = analyze_series(records, 5)
        assert r["alignment_mode"] == "utc_midnight_fallback"
        assert r["misaligned_bars"] == 1
        assert "aligned_count" not in r                 # legacy keys intact

    def test_with_schedule_aligned_grid_clean(self, sched):
        times = aligned_times(sched, "H4",
                              [date(2026, 7, 13), date(2026, 7, 14)],
                              [0, 1, 2, 3, 4, 5])
        records = make_bar_records(times, "H4")
        validator = build_session_schedule(
            "America/New_York", list(sched.intervals_week_seconds))
        r = analyze_series(records, 240, schedule=validator, timeframe="H4")
        assert r["alignment_mode"] == "session"
        assert r["misaligned_bars"] == 0

    def test_with_schedule_shifted_bar_detected(self, sched):
        times = aligned_times(sched, "H4",
                              [date(2026, 7, 13), date(2026, 7, 14)],
                              [0, 1, 2, 3])
        records = make_bar_records(times, "H4", shift_last_by_minutes=100)
        validator = build_session_schedule(
            "America/New_York", list(sched.intervals_week_seconds))
        r = analyze_series(records, 240, schedule=validator, timeframe="H4")
        assert r["alignment_mode"] == "session"
        assert r["misaligned_bars"] == 1
        assert r["alignment_detail"][0]["aligned"] is False

    def test_with_schedule_session_gaps_not_misaligned(self, sched):
        """Aligned H4 bars straddling the weekend: session gap reported,
        NO misalignment (the fallback rule would have flagged these)."""
        times = [zoneinfo_roll_utc(sched, date(2026, 7, 10))
                 + k * timedelta(hours=4) for k in (0, 1)]
        times += [zoneinfo_roll_utc(sched, date(2026, 7, 13))
                  + k * timedelta(hours=4) for k in (0, 1)]
        records = make_bar_records(times, "H4")
        validator = build_session_schedule(
            "America/New_York", list(sched.intervals_week_seconds))
        r = analyze_series(records, 240, schedule=validator, timeframe="H4")
        assert r["session_gaps"] == 1
        assert r["misaligned_bars"] == 0

    def test_summarize_timeframe_passes_schedule_through(self, sched):
        times = aligned_times(sched, "D1", [date(2026, 7, 13),
                                            date(2026, 7, 14)], [0])
        records = make_bar_records(times, "D1")
        validator = build_session_schedule(
            "America/New_York", list(sched.intervals_week_seconds))
        s = summarize_timeframe(records, 1440, schedule=validator,
                                timeframe="D1")
        assert s["alignment_mode"] == "session"
        assert s["misaligned_bars"] == 0

    def test_none_schedule_keeps_fallback_in_summarize(self):
        records = make_bar_records(
            [datetime(2026, 9, 7, 0, 0, tzinfo=UTC),
             datetime(2026, 9, 7, 4, 0, tzinfo=UTC)], "H4")
        s = summarize_timeframe(records, 240, schedule=None, timeframe="H4")
        assert s["alignment_mode"] == "utc_midnight_fallback"


# ─────────────────────────────────────────────────────────────────────────────
# Determinism
# ─────────────────────────────────────────────────────────────────────────────

class TestDeterminism:
    def test_repeated_runs_identical(self, sched):
        probes = aligned_times(sched, "H4",
                               [date(2026, 3, 6), date(2026, 7, 15)], [0, 1])
        probes += [probes[0] + timedelta(minutes=100)]
        v1 = TemporalValidator(schedule=ic_style_schedule())
        v2 = TemporalValidator(schedule=sched)
        for t in probes:
            assert v1.alignment_finding(t, "H4") == v2.alignment_finding(t, "H4")
