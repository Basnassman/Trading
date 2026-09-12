"""PROPOSED session-aware temporal alignment model (Gate 4 pre-implementation).

Status: PROPOSED — NOT wired into the production validation path. No
production module imports this file. It exists so the minimal production
change can be proven with credential-free, deterministic tests BEFORE
approval. All inputs are plain data (timezone name + week-anchored interval
seconds); no network, no credentials, no provider SDK dependency.

Model (derived exclusively from provider-reported symbol schedule metadata;
fully provider-agnostic — no broker names, no broker-specific constants):

- Schedule intervals are week-anchored seconds: 0 = Sunday 00:00 in the
  symbol's schedule time zone, per the provider's Open API proto semantics
  (interval start inclusive, end exclusive).
- The daily roll (the bar-grid anchor) is the modal interval END
  time-of-day plus 60 seconds, in the schedule time zone. It is resolved
  per date through the IANA tz database (zoneinfo), so the UTC anchor
  moves with DST automatically — no offset constants anywhere.
- A bar with open time t (tz-aware UTC) is ALIGNED iff
  (t - roll_instant(trading_day(t))) is a non-negative integer multiple of
  the bar period, where trading_day(t) is the local schedule-TZ date of the
  most recent daily roll at or before t.
- Without schedule metadata (unknown or non-session-aware provider) the
  validator falls back to the EXISTING rule: UTC-midnight modulo alignment
  (minutes-since-epoch % period == 0). Fallback is also used when the
  supplied timezone name cannot be resolved.

The validator NEVER mutates timestamps: it only classifies and reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

TIMEFRAME_MINUTES: dict[str, int] = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}

SECONDS_PER_DAY = 86_400


@dataclass(frozen=True)
class SessionSchedule:
    """Provider symbol schedule metadata (plain data, provider-agnostic).

    intervals_week_seconds: (start, end) week-anchored seconds in the
    schedule time zone (0 = Sunday 00:00; start inclusive, end exclusive).
    """

    schedule_tz_name: str
    intervals_week_seconds: tuple[tuple[int, int], ...]

    def resolved_tz(self) -> ZoneInfo:
        """Resolve the schedule time zone; raises ZoneInfoNotFoundError."""
        return ZoneInfo(self.schedule_tz_name)

    @property
    def is_resolvable(self) -> bool:
        try:
            self.resolved_tz()
            return True
        except (ZoneInfoNotFoundError, ValueError):
            return False

    def daily_roll_local_second_of_day(self) -> int:
        """Daily roll as second-of-day in the schedule time zone.

        Roll = modal interval END second-of-day + 60 s (the end boundary is
        the last minute edge with trading; the roll happens on the next
        minute edge). Raises ValueError if there are no intervals.
        """
        if not self.intervals_week_seconds:
            raise ValueError("schedule has no intervals")
        end_seconds = [end % SECONDS_PER_DAY
                       for _s, end in self.intervals_week_seconds]
        modal_end = max(set(end_seconds), key=end_seconds.count)
        return (modal_end + 60) % SECONDS_PER_DAY


def roll_instant_utc(schedule: SessionSchedule, t_utc: datetime) -> datetime:
    """UTC instant of the daily roll that anchors the trading day of t_utc.

    DST-aware: the roll is a fixed LOCAL wall-clock time in the schedule
    zone; its UTC expression is resolved per date via zoneinfo.
    """
    if t_utc.tzinfo is None:
        raise ValueError("bar_time must be timezone-aware")
    tz = schedule.resolved_tz()
    roll_sec = schedule.daily_roll_local_second_of_day()
    roll_time = time(roll_sec // 3600, (roll_sec % 3600) // 60, roll_sec % 60)
    local = t_utc.astimezone(tz)
    local_sec = local.hour * 3600 + local.minute * 60 + local.second
    roll_date = local.date() if local_sec >= roll_sec \
        else local.date() - timedelta(days=1)
    return datetime.combine(roll_date, roll_time, tzinfo=tz) \
        .astimezone(timezone.utc)


@dataclass(frozen=True)
class AlignmentFinding:
    """Classification of one bar-open timestamp. Never mutates the input."""

    bar_time: datetime
    timeframe: str
    aligned: bool
    mode: str                     # "session" | "utc_midnight_fallback"
    detail: str


class TemporalAlignmentValidator:
    """Anchor-based temporal alignment validation.

    With a resolvable SessionSchedule: session-aware, DST-following anchor
    validation. Without one (schedule=None, or unresolvable tz): the
    existing UTC-midnight modulo fallback.
    """

    def __init__(self, schedule: SessionSchedule | None = None) -> None:
        self._schedule = schedule
        self._session_mode = schedule is not None and schedule.is_resolvable

    @property
    def mode(self) -> str:
        return "session" if self._session_mode else "utc_midnight_fallback"

    @property
    def schedule(self) -> SessionSchedule | None:
        return self._schedule

    # ── single bar ────────────────────────────────────────────────────────
    def validate_bar_time(self, bar_time: datetime,
                          timeframe: str) -> AlignmentFinding:
        period_min = TIMEFRAME_MINUTES.get(timeframe)
        if period_min is None:
            return AlignmentFinding(bar_time, timeframe, False, self.mode,
                                    f"unknown timeframe {timeframe!r}")
        if bar_time.tzinfo is None:
            return AlignmentFinding(bar_time, timeframe, False, self.mode,
                                    "naive timestamp (no timezone)")
        if not self._session_mode:
            minutes = int(bar_time.astimezone(timezone.utc).timestamp()) // 60
            aligned = minutes % period_min == 0
            return AlignmentFinding(
                bar_time, timeframe, aligned, "utc_midnight_fallback",
                f"minutes-since-epoch {minutes} % {period_min} "
                f"{'== 0' if aligned else '!= 0'}")
        try:
            roll = roll_instant_utc(self._schedule, bar_time)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            return AlignmentFinding(bar_time, timeframe, False,
                                    "utc_midnight_fallback",
                                    f"schedule unresolved: {exc}")
        delta = bar_time - roll
        delta_sec = delta.total_seconds()
        aligned = delta_sec >= 0 and delta_sec % (period_min * 60) == 0
        return AlignmentFinding(
            bar_time, timeframe, aligned, "session",
            f"delta from roll {roll.isoformat()} = "
            f"{int(delta_sec // 60)} min "
            f"({'multiple of' if aligned else 'NOT a multiple of'} "
            f"{period_min})")

    # ── series classification ─────────────────────────────────────────────
    def classify_series(self, bar_times: list[datetime],
                        timeframe: str) -> dict:
        """Ordering / duplicates / gaps / alignment for one timeframe.

        Gap semantics match the existing validator: a jump that is an
        integer multiple of the period is a SESSION GAP (legitimate missing
        bars — sessions close); a non-multiple jump is an anomaly. Bar-open
        misalignment is reported per bar. Inputs are never modified.
        """
        period_min = TIMEFRAME_MINUTES.get(timeframe)
        findings = [self.validate_bar_time(t, timeframe)
                    for t in bar_times]
        report: dict = {
            "mode": self.mode,
            "count": len(bar_times),
            "aligned_count": sum(1 for f in findings if f.aligned),
            "misaligned": [f for f in findings if not f.aligned],
            "session_gaps": [],
            "anomalies": [],
            "ordered": True,
        }
        if period_min is None or len(bar_times) < 2:
            return report

        interval = timedelta(minutes=period_min)
        for i in range(1, len(bar_times)):
            t_prev, t_i = bar_times[i - 1], bar_times[i]
            if t_prev.tzinfo is None or t_i.tzinfo is None:
                report["anomalies"].append({
                    "index": i, "kind": "naive_timestamp",
                    "detail": "series timestamps must be tz-aware"})
                continue
            diff_min = (t_i - t_prev).total_seconds() / 60.0
            if diff_min == 0:
                report["anomalies"].append({
                    "index": i, "kind": "duplicate",
                    "detail": f"duplicate timestamp {t_i.isoformat()}"})
            elif diff_min < 0:
                report["anomalies"].append({
                    "index": i, "kind": "reversed",
                    "detail": f"reversed: {t_prev.isoformat()} -> "
                              f"{t_i.isoformat()}"})
            elif diff_min < period_min:
                report["anomalies"].append({
                    "index": i, "kind": "overlap",
                    "detail": f"sub-interval spacing {diff_min} min"})
            elif diff_min % period_min != 0:
                report["anomalies"].append({
                    "index": i, "kind": "non_multiple_jump",
                    "detail": f"jump {diff_min} min is not a multiple of "
                              f"{period_min}"})
            elif diff_min > period_min:
                report["session_gaps"].append({
                    "start": t_prev, "end": t_i,
                    "gap_minutes": int(diff_min),
                    "multiples": int(diff_min // period_min)})
        report["ordered"] = not any(
            a["kind"] in ("duplicate", "reversed", "overlap")
            for a in report["anomalies"])
        return report


def from_schedule_metadata(schedule_tz_name: str,
                           intervals_week_seconds: list[tuple[int, int]],
                           ) -> TemporalAlignmentValidator:
    """Build the validator from raw provider schedule metadata fields."""
    return TemporalAlignmentValidator(SessionSchedule(
        schedule_tz_name=schedule_tz_name,
        intervals_week_seconds=tuple(intervals_week_seconds)))
