"""Credential-free, deterministic tests for the PROPOSED DST-aware
session-alignment validator (Gate 4 pre-implementation validation).

Scope:
1–2. EDT/EST regimes: 17:00 America/New_York anchor and its H4/D1 residues
     (documented acceptance values from the Gate 4 metadata reconciliation).
3.   Real DST transitions (2026 spring forward / fall back): expected anchors
     are derived through zoneinfo ONLY — no hardcoded offset literals.
4–5. Aligned H4/D1 bars accepted; deliberately shifted bars rejected.
6.   Session gaps classified as gap findings, never as misalignment.
7.   Raw timestamps are never changed.
8.   Unknown/non-session-aware providers retain the UTC-midnight fallback.
9.   The generic validator contains no broker names or broker-specific
     conditions (source scan + functional genericity proof).
10.  Deterministic: fixed dates, no clock reads, no environment access,
     repeated runs produce identical results.

The schedule fixture below is plain data mirroring the broker-reported
symbol schedule (tz + week-anchored interval seconds). The VALIDATOR under
test receives schedule metadata as constructor arguments only.
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
    roll_instant_utc,
)

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures: provider-reported schedule metadata as PLAIN DATA
# (week-anchored seconds, 0 = Sunday 00:00 schedule-TZ; start inclusive,
#  end exclusive — per the provider Open API proto semantics)
# ─────────────────────────────────────────────────────────────────────────────

SEC_PER_DAY = 86_400


def gold_schedule() -> SessionSchedule:
    """Reconciled XAUUSD schedule metadata (plain data; provider-agnostic
    constructor — the validator knows nothing about the symbol)."""
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
    return gold_schedule()


@pytest.fixture(scope="module")
def validator(sched: SessionSchedule) -> TemporalAlignmentValidator:
    v = TemporalAlignmentValidator(sched)
    assert v.mode == "session"
    return v


def zoneinfo_roll_utc(schedule: SessionSchedule, local_date: date) -> datetime:
    """Expected UTC roll instant for local_date, derived ONLY via zoneinfo
    from the schedule's own local roll time (no offset literals)."""
    roll_sec = schedule.daily_roll_local_second_of_day()
    t = time(roll_sec // 3600, (roll_sec % 3600) // 60, roll_sec % 60)
    return datetime.combine(local_date, t,
                            tzinfo=ZoneInfo(schedule.schedule_tz_name)) \
        .astimezone(timezone.utc)


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


def make_raw_bars(times: list[datetime], timeframe: str,
                  provider: str = "provider-a") -> list[RawBar]:
    bars = []
    for t in times:
        bars.append(RawBar(
            symbol="SYNTH",
            timeframe=timeframe,
            bar_time=t,
            open=Decimal("2400.00"),
            high=Decimal("2401.00"),
            low=Decimal("2399.00"),
            close=Decimal("2400.50"),
            tick_volume=100,
            provider=provider,
            provider_symbol="SYNTH",
            retrieval_time=datetime(2026, 9, 12, tzinfo=timezone.utc),
        ))
    return bars


# ─────────────────────────────────────────────────────────────────────────────
# 1–2. Documented regime acceptance values (EDT / EST)
# ─────────────────────────────────────────────────────────────────────────────

def test_edt_regime_anchor_and_residues(sched, validator):
    """EDT: 17:00 America/New_York = 21:00 UTC; H4 residue 60; D1 1260."""
    roll = zoneinfo_roll_utc(sched, date(2026, 7, 15))          # EDT week
    assert roll == roll_instant_utc(sched, roll)                # module agrees
    assert (roll.hour, roll.minute) == (21, 0)                  # 21:00 UTC
    ny = roll.astimezone(ZoneInfo(sched.schedule_tz_name))
    assert (ny.hour, ny.minute) == (17, 0)                      # 17:00 local
    assert ny.utcoffset() == timedelta(hours=-4)                # EDT
    mod = roll.hour * 60 + roll.minute                          # 1260, derived
    assert mod % TIMEFRAME_MINUTES["H4"] == 60                  # H4 residue 60
    assert mod % TIMEFRAME_MINUTES["D1"] == 1260                # D1 residue 1260
    # A bar exactly on the anchor is aligned in both timeframes
    assert validator.validate_bar_time(roll, "H4").aligned
    assert validator.validate_bar_time(roll, "D1").aligned


def test_est_regime_anchor_and_residues(sched, validator):
    """EST: 17:00 America/New_York = 22:00 UTC; H4 residue 120; D1 1320."""
    roll = zoneinfo_roll_utc(sched, date(2026, 1, 14))          # EST week
    assert roll == roll_instant_utc(sched, roll)
    assert (roll.hour, roll.minute) == (22, 0)                  # 22:00 UTC
    ny = roll.astimezone(ZoneInfo(sched.schedule_tz_name))
    assert (ny.hour, ny.minute) == (17, 0)                      # 17:00 local
    assert ny.utcoffset() == timedelta(hours=-5)                # EST
    mod = roll.hour * 60 + roll.minute                          # 1320, derived
    assert mod % TIMEFRAME_MINUTES["H4"] == 120                 # H4 residue 120
    assert mod % TIMEFRAME_MINUTES["D1"] == 1320                # D1 residue 1320
    assert validator.validate_bar_time(roll, "H4").aligned
    assert validator.validate_bar_time(roll, "D1").aligned


# ─────────────────────────────────────────────────────────────────────────────
# 3. Real DST transitions — anchors derived through zoneinfo, automatically
# ─────────────────────────────────────────────────────────────────────────────

def test_spring_forward_2026_anchor_changes_automatically(sched, validator):
    """2026-03-08 02:00 local: EST → EDT. Anchor must move 22:00 → 21:00 UTC
    through zoneinfo alone (no offset constants anywhere)."""
    fri_est = zoneinfo_roll_utc(sched, date(2026, 3, 6))        # before
    mon_edt = zoneinfo_roll_utc(sched, date(2026, 3, 9))        # after
    assert fri_est != mon_edt
    off_fri = fri_est.astimezone(ZoneInfo(sched.schedule_tz_name)).utcoffset()
    off_mon = mon_edt.astimezone(ZoneInfo(sched.schedule_tz_name)).utcoffset()
    assert off_fri != off_mon                                   # offset flipped
    assert off_fri == timedelta(hours=-5) and off_mon == timedelta(hours=-4)
    assert fri_est.time() != mon_edt.time()                     # UTC TOD moved
    # Module output equals the zoneinfo-derived anchor on both sides
    assert roll_instant_utc(sched, fri_est) == fri_est
    assert roll_instant_utc(sched, mon_edt) == mon_edt
    # A bar on each side of the transition is aligned to ITS OWN regime
    assert validator.validate_bar_time(fri_est, "H4").aligned
    assert validator.validate_bar_time(mon_edt, "H4").aligned
    assert validator.validate_bar_time(fri_est, "D1").aligned
    assert validator.validate_bar_time(mon_edt, "D1").aligned


def test_fall_back_2026_anchor_changes_automatically(sched, validator):
    """2026-11-01 02:00 local: EDT → EST. Anchor must move 21:00 → 22:00 UTC."""
    fri_edt = zoneinfo_roll_utc(sched, date(2026, 10, 30))      # before
    mon_est = zoneinfo_roll_utc(sched, date(2026, 11, 2))       # after
    assert fri_edt != mon_est
    off_fri = fri_edt.astimezone(ZoneInfo(sched.schedule_tz_name)).utcoffset()
    off_mon = mon_est.astimezone(ZoneInfo(sched.schedule_tz_name)).utcoffset()
    assert off_fri != off_mon
    assert off_fri == timedelta(hours=-4) and off_mon == timedelta(hours=-5)
    assert fri_edt.time() != mon_est.time()
    assert roll_instant_utc(sched, fri_edt) == fri_edt
    assert roll_instant_utc(sched, mon_est) == mon_est
    assert validator.validate_bar_time(fri_edt, "D1").aligned
    assert validator.validate_bar_time(mon_est, "D1").aligned


def test_stale_anchor_rejected_after_transition(sched, validator):
    """A bar stamped with the PRE-transition anchor time-of-day after the
    transition is rejected — proving the anchor follows zoneinfo, not a
    stored constant."""
    fri_est = zoneinfo_roll_utc(sched, date(2026, 3, 6))        # 22:00 UTC
    mon_edt = zoneinfo_roll_utc(sched, date(2026, 3, 9))        # 21:00 UTC
    stale = mon_edt.replace(hour=fri_est.hour)                  # Mon 22:00 UTC
    assert validator.validate_bar_time(stale, "H4").aligned is False
    assert validator.validate_bar_time(stale, "D1").aligned is False
    assert validator.validate_bar_time(mon_edt, "H4").aligned   # fresh OK
    # Winter direction: post-transition bar at the OLD (EDT) time-of-day
    fri_edt = zoneinfo_roll_utc(sched, date(2026, 10, 30))      # 21:00 UTC
    mon_est = zoneinfo_roll_utc(sched, date(2026, 11, 2))       # 22:00 UTC
    stale_w = mon_est.replace(hour=fri_edt.hour)                # Mon 21:00 UTC
    assert validator.validate_bar_time(stale_w, "H4").aligned is False
    assert validator.validate_bar_time(stale_w, "D1").aligned is False
    assert validator.validate_bar_time(mon_est, "D1").aligned   # fresh OK


# ─────────────────────────────────────────────────────────────────────────────
# 4–5. Grid acceptance / shift rejection
# ─────────────────────────────────────────────────────────────────────────────

def test_aligned_h4_and_d1_bars_accepted(sched, validator):
    """H4/D1 bars on the session-derived grid are accepted."""
    week = [date(2026, 7, 13), date(2026, 7, 14),
            date(2026, 7, 15), date(2026, 7, 16)]               # Mon–Thu
    for tf, ks in (("H4", [0, 1, 2, 3, 4, 5]), ("D1", [0])):
        times = aligned_times(sched, tf, week, ks)
        assert times
        for t in times:
            f = validator.validate_bar_time(t, tf)
            assert f.aligned, (tf, t, f.detail)
            assert f.mode == "session"


def test_shifted_bars_rejected(sched, validator):
    """Deliberately off-grid bars are rejected (session mode)."""
    roll = zoneinfo_roll_utc(sched, date(2026, 7, 15))          # Wed 21:00 UTC
    for tf, shift in (("H4", timedelta(minutes=100)),
                      ("H4", timedelta(minutes=120)),
                      ("H4", timedelta(minutes=60)),
                      ("D1", timedelta(minutes=60)),
                      ("D1", timedelta(minutes=100))):
        t = roll + shift
        f = validator.validate_bar_time(t, tf)
        assert not f.aligned, (tf, shift, f.detail)
    # UTC-midnight-anchored bars (the OLD rule's grid) must NOT pass
    midnight = datetime(2026, 7, 16, 0, 0, tzinfo=timezone.utc)
    assert not validator.validate_bar_time(midnight, "H4").aligned
    assert not validator.validate_bar_time(midnight, "D1").aligned


def test_bars_before_daily_roll_rejected(sched, validator):
    """Negative offsets from the roll (pre-roll stamps) are rejected."""
    roll = zoneinfo_roll_utc(sched, date(2026, 7, 15))
    t = roll - timedelta(minutes=120)
    assert not validator.validate_bar_time(t, "H4").aligned
    assert not validator.validate_bar_time(t, "D1").aligned


# ─────────────────────────────────────────────────────────────────────────────
# 6. Session gaps stay gap findings — never misalignment
# ─────────────────────────────────────────────────────────────────────────────

def test_h4_weekend_gap_is_gap_not_misalignment(sched, validator):
    """Aligned bars straddling the weekend produce a session-gap finding and
    zero misalignment/anomalies."""
    fri = zoneinfo_roll_utc(sched, date(2026, 7, 10))           # Fri roll
    sat = fri + timedelta(hours=4)                              # on-grid
    mon = zoneinfo_roll_utc(sched, date(2026, 7, 13))           # Mon roll
    tue = mon + timedelta(hours=4)
    times = [fri, sat, mon, tue]
    rep = validator.classify_series(times, "H4")
    assert rep["mode"] == "session"
    assert rep["aligned_count"] == len(times)
    assert rep["misaligned"] == []
    assert rep["anomalies"] == []
    assert len(rep["session_gaps"]) == 1
    gap = rep["session_gaps"][0]
    assert gap["start"] == sat and gap["end"] == mon
    assert gap["gap_minutes"] % TIMEFRAME_MINUTES["H4"] == 0    # multiple → gap


def test_d1_weekend_gap_is_gap_not_misalignment(sched, validator):
    thu = zoneinfo_roll_utc(sched, date(2026, 7, 9))
    fri = zoneinfo_roll_utc(sched, date(2026, 7, 10))
    mon = zoneinfo_roll_utc(sched, date(2026, 7, 13))
    rep = validator.classify_series([thu, fri, mon], "D1")
    assert rep["aligned_count"] == 3
    assert rep["misaligned"] == []
    assert rep["anomalies"] == []
    # Thu→Fri is exactly one interval (no gap); Fri→Mon (3 days) is the gap.
    assert len(rep["session_gaps"]) == 1
    gap = rep["session_gaps"][0]
    assert gap["start"] == fri and gap["end"] == mon
    assert gap["gap_minutes"] == 3 * TIMEFRAME_MINUTES["D1"]


# ─────────────────────────────────────────────────────────────────────────────
# 7. Raw timestamps are never changed
# ─────────────────────────────────────────────────────────────────────────────

def test_raw_timestamps_never_mutated(sched, validator):
    week = [date(2026, 7, 13), date(2026, 7, 14), date(2026, 7, 15)]
    times = aligned_times(sched, "H4", week, [0, 1, 2])
    times_snapshot = copy.deepcopy(times)
    bars = make_raw_bars(times, "H4")
    bars_snapshot = copy.deepcopy(bars)

    for bar in bars:
        f = validator.validate_bar_time(bar.bar_time, bar.timeframe)
        assert f.bar_time == bar.bar_time
        assert f.bar_time is bar.bar_time            # same object, no re-stamp
    rep = validator.classify_series([b.bar_time for b in bars], "H4")

    assert times == times_snapshot                  # values unchanged
    assert [t.isoformat() for t in times] == \
        [t.isoformat() for t in times_snapshot]
    assert bars == bars_snapshot                     # frozen RawBars unchanged
    assert all(b.bar_time == s.bar_time
               for b, s in zip(bars, bars_snapshot))
    # Findings echo the input instants verbatim (no rounding/shifting)
    for f, t in zip(rep["misaligned"] or
                    [validator.validate_bar_time(t, "H4") for t in times],
                    times):
        assert f.bar_time == t


# ─────────────────────────────────────────────────────────────────────────────
# 8. Unknown / non-session-aware providers → UTC-midnight fallback
# ─────────────────────────────────────────────────────────────────────────────

def test_fallback_utc_midnight_for_unknown_provider():
    v = TemporalAlignmentValidator(None)
    assert v.mode == "utc_midnight_fallback"
    # Existing UTC-midnight modulo rule retained
    assert v.validate_bar_time(
        datetime(2026, 9, 7, 0, 0, tzinfo=timezone.utc), "H4").aligned
    assert v.validate_bar_time(
        datetime(2026, 9, 7, 4, 0, tzinfo=timezone.utc), "H4").aligned
    assert v.validate_bar_time(
        datetime(2026, 9, 7, 0, 0, tzinfo=timezone.utc), "D1").aligned
    # Session-grid stamps (21:00 UTC) are NOT valid under the fallback —
    # the two modes genuinely disagree, no silent cross-contamination.
    f = v.validate_bar_time(
        datetime(2026, 9, 7, 21, 0, tzinfo=timezone.utc), "H4")
    assert not f.aligned and f.mode == "utc_midnight_fallback"
    f = v.validate_bar_time(
        datetime(2026, 9, 7, 21, 0, tzinfo=timezone.utc), "D1")
    assert not f.aligned and f.mode == "utc_midnight_fallback"


def test_fallback_for_unresolvable_timezone():
    v = TemporalAlignmentValidator(SessionSchedule(
        schedule_tz_name="Mars/Olympus_Mons",
        intervals_week_seconds=((64920, 147540),),
    ))
    assert v.mode == "utc_midnight_fallback"
    assert v.validate_bar_time(
        datetime(2026, 9, 7, 0, 0, tzinfo=timezone.utc), "H4").aligned
    assert not v.validate_bar_time(
        datetime(2026, 9, 7, 21, 0, tzinfo=timezone.utc), "H4").aligned


def test_naive_timestamps_rejected_in_both_modes(sched):
    naive = datetime(2026, 7, 15, 21, 0)             # no tzinfo
    assert not TemporalAlignmentValidator(sched) \
        .validate_bar_time(naive, "H4").aligned
    assert not TemporalAlignmentValidator(None) \
        .validate_bar_time(naive, "H4").aligned


# ─────────────────────────────────────────────────────────────────────────────
# 9. Generic validator: no broker names / broker-specific conditions
# ─────────────────────────────────────────────────────────────────────────────

def test_validator_source_has_no_broker_specifics():
    import src.validation.session_alignment as sa
    src = Path(sa.__file__).read_text(encoding="utf-8")
    forbidden = [
        "IC Markets", "icmarkets", "ICMarkets", "IC_MARKETS",
        "cTrader", "ctrader", "CTRADER",
        "XAUUSD", "XAU", "gold", "Gold",
        "10107153", "48518857", "demo.ctraderapi",
        "+120", "+60", "1260", "1320", "120 %", "60 %",
    ]
    for token in forbidden:
        assert token not in src, f"broker-specific token in validator: {token!r}"


def test_alternative_synthetic_schedule_validated_generically():
    """The SAME generic validator handles a completely different session
    definition (UTC roll at 00:00) — no symbol/broker logic baked in."""
    v = TemporalAlignmentValidator(SessionSchedule(
        schedule_tz_name="UTC",
        intervals_week_seconds=((SEC_PER_DAY, 5 * SEC_PER_DAY + 86340),),
    ))                                               # Mon 00:00 → Fri 23:59
    assert v.mode == "session"
    roll = zoneinfo_roll_utc(v.schedule, date(2026, 7, 15))
    assert (roll.hour, roll.minute) == (0, 0)        # UTC-midnight anchor
    for k in range(6):
        assert v.validate_bar_time(roll + k * timedelta(hours=4),
                                   "H4").aligned
    assert v.validate_bar_time(roll, "D1").aligned
    assert not v.validate_bar_time(roll + timedelta(minutes=100),
                                   "H4").aligned
    assert not v.validate_bar_time(roll + timedelta(minutes=60),
                                   "D1").aligned


# ─────────────────────────────────────────────────────────────────────────────
# 10. Determinism
# ─────────────────────────────────────────────────────────────────────────────

def test_deterministic_repeated_runs(sched):
    v1 = TemporalAlignmentValidator(sched)
    v2 = TemporalAlignmentValidator(gold_schedule())
    week = [date(2026, 3, 6), date(2026, 3, 9), date(2026, 7, 15),
            date(2026, 11, 2)]
    probes = aligned_times(sched, "H4", week, [0, 1, 2])
    probes += [t + timedelta(minutes=100) for t in probes[:2]]
    for t in probes:
        assert v1.validate_bar_time(t, "H4") == v2.validate_bar_time(t, "H4")
        r1 = v1.classify_series(probes, "H4")
        r2 = v2.classify_series(probes, "H4")
        assert r1["aligned_count"] == r2["aligned_count"]
        assert r1["session_gaps"] == r2["session_gaps"]
        assert r1["anomalies"] == r2["anomalies"]


def test_module_has_no_clock_or_environment_reads():
    import src.validation.session_alignment as sa
    src = Path(sa.__file__).read_text(encoding="utf-8")
    for token in ("datetime.now", "utcnow", "time.time(", "os.environ",
                  "getenv", "random", "socket", "requests.", "urllib"):
        assert token not in src, \
            f"non-deterministic or environment read in validator: {token!r}"
