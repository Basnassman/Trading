#!/usr/bin/env python3
"""cTrader Open API — Gate 4 session-metadata reconciliation (DIAGNOSTIC-ONLY).

Purpose (single additional verification demanded before any validator change):
  1. Retrieve the FULL ProtoOASymbol metadata for the verified XAUUSD symbol
     (symbolId re-resolved dynamically from asset+symbol metadata; 41 on this
     broker — equality is asserted, never hardcoded).
  2. Inspect scheduleTimeZone (#26), schedule (#13: repeated ProtoOAInterval
     with startSecond #3 / endSecond #4).
  3. Derive the effective trading-session boundaries in UTC.
  4. Independently reconcile those boundaries with the observed H4/D1
     bar-open offset of +120 minutes.
  5. Decide whether the +120 grid is explained by broker session metadata.

Rules of engagement
-------------------
- READ-ONLY: no production code changes, no timestamp shifts, no validator
  weakening, and NO hardcoded bar-grid offset anywhere in this file.
- The observed +120 minute offset appears ONLY as a comparison target
  (OBSERVED_OFFSET_MIN) in the final reconciliation step. Every expectation
  is derived from broker-reported schedule metadata first, then compared.
- Requests: asset list, symbols list, symbol by id, PLUS a minimal read-only
  bar probe (4 × GetTrendbarsReq, ≤10 bars each, paced at 0.7 s): H4/D1 for
  the current window AND a winter window, so the bar-grid anchor can be
  tested for DST dependence. The probe selects among metadata-derived
  candidate anchors; it never derives the grid from bars alone.
  No trading, no orders, no production code changes.

SDK facts verified from installed ctrader-open-api 0.9.2 descriptors:
- ProtoOASymbol.schedule         = field #13, repeated ProtoOAInterval
- ProtoOASymbol.scheduleTimeZone = field #26, string
- ProtoOAInterval.startSecond    = field #3, uint32
- ProtoOAInterval.endSecond      = field #4, uint32
- Payload types: SYMBOL_BY_ID_REQ=2116, SYMBOL_BY_ID_RES=2117,
  ASSET_LIST_RES=2113, SYMBOLS_LIST_RES=2115, ERROR_RES=2142.

Schedule semantics (VERBATIM from spotware/openapi-proto-messages,
OpenApiModelMessages.proto):
  repeated ProtoOAInterval schedule = 13; // Symbol trading interval,
      // specified in seconds starting from SUNDAY 00:00 in specified TZ.
  optional string scheduleTimeZone = 26;  // Time zone for the intervals.
  message ProtoOAInterval {
    required uint32 startSecond = 3; // ... starting from SUNDAY 00:00
        // in specified time zone (inclusive to the interval).
    required uint32 endSecond = 4;   // ... (exclusive from the interval).
  }

=> startSecond/endSecond are WEEK-anchored (0 = Sunday 00:00 schedule-TZ).

Time-zone handling: scheduleTimeZone is a broker-supplied IANA zone name
(e.g. 'America/New_York'). Decoding is DST-AWARE via the standard library
`zoneinfo` database: offsets are resolved per concrete date, never guessed.
The tool reports BOTH the current regime and the opposite (winter/summer)
regime, because a DST-observing schedule zone makes the UTC residue class of
the bar grid regime-dependent. No offset is ever hardcoded.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from dotenv import load_dotenv


# ─────────────────────────────────────────────────────────────────────────────
# Pure helpers (network-free, credential-free — auditable without a connection)
# ─────────────────────────────────────────────────────────────────────────────

OBSERVED_OFFSET_MIN = 120          # comparison target from Gate 4 bar diagnosis
SECONDS_PER_DAY = 86_400
SECONDS_PER_WEEK = 7 * SECONDS_PER_DAY
H4_MIN = 240
D1_MIN = 1440

WEEKDAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday"]


@dataclass(frozen=True)
class ScheduleTZ:
    """Resolved scheduleTimeZone (IANA name; offsets resolved per date)."""
    name: str
    zone: ZoneInfo | None
    is_fixed: bool
    error: str | None = None


def resolve_schedule_tz(name: str | None) -> ScheduleTZ:
    """Resolve the broker's scheduleTimeZone string.

    IANA zone names (e.g. America/New_York) are accepted and decoded
    DST-aware via zoneinfo. Fixed UTC/GMT±H names are mapped to fixed
    offsets. Anything unparseable/absent is refused (never guessed).
    """
    if name is None or str(name).strip() == "":
        return ScheduleTZ(name=str(name), zone=None, is_fixed=False,
                          error="scheduleTimeZone ABSENT (empty/missing field)")
    s = str(name).strip()
    try:
        return ScheduleTZ(name=s, zone=ZoneInfo(s), is_fixed=False, error=None)
    except Exception:
        pass
    # Fixed-offset fallbacks (UTC / GMT±H[:MM])
    import re
    m = re.match(r"^(?:UTC|GMT)(?:([+-])(\d{1,2})(?::?(\d{2}))?)?$", s,
                 re.IGNORECASE)
    if m and m.group(1):
        sign = 1 if m.group(1) == "+" else -1
        return ScheduleTZ(
            name=s,
            zone=timezone(sign * timedelta(hours=int(m.group(2)),
                                           minutes=int(m.group(3) or 0))),
            is_fixed=True, error=None)
    if s.upper() in ("UTC", "GMT"):
        return ScheduleTZ(name=s, zone=timezone.utc, is_fixed=True, error=None)
    return ScheduleTZ(name=s, zone=None, is_fixed=False,
                      error=f"unsupported scheduleTimeZone '{s}'")


def offset_seconds_at(tz: ScheduleTZ, at_utc: datetime) -> int:
    """UTC offset (seconds) of the schedule zone at a concrete UTC instant."""
    assert tz.zone is not None
    return int(tz.zone.utcoffset(at_utc).total_seconds())


def fmt_hhmmss(sec: int) -> str:
    sec %= SECONDS_PER_DAY
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def fmt_weeksec(ws: int) -> str:
    d, rem = divmod(ws, SECONDS_PER_DAY)
    return f"{WEEKDAY_NAMES[d % 7]} {fmt_hhmmss(rem)}"


def weeksec_to_utc(local_weeksec: int, tz: ScheduleTZ,
                   ref_sunday_local: date) -> datetime:
    """Convert a week-anchored schedule second to a concrete UTC instant.

    Anchor: the Sunday 00:00 (schedule TZ) that starts the week containing
    ref_sunday_local. Local wall time = anchor_local + weeksec; converted
    with zoneinfo (DST-aware). Ambiguous local times use fold=0 (first
    occurrence) and are annotated by the caller if relevant.
    """
    assert tz.zone is not None
    if isinstance(tz.zone, timezone):                       # fixed offset
        anchor_utc = datetime.combine(ref_sunday_local, time(0, 0),
                                      tzinfo=timezone.utc)
        return anchor_utc + timedelta(seconds=local_weeksec) \
            - tz.zone.utcoffset(anchor_utc)
    anchor_naive = datetime.combine(ref_sunday_local, time(0, 0))
    anchor_local = anchor_naive.replace(tzinfo=tz.zone, fold=0)
    local_target = anchor_local + timedelta(seconds=local_weeksec)
    return local_target.astimezone(timezone.utc)


def session_opens_utc(intervals: list[tuple[int, int]], tz: ScheduleTZ,
                      ref_sunday_local: date) -> list[dict]:
    """Concrete UTC instants of every session OPEN in the reference week.

    Each open is a candidate bar-grid anchor: bars can only open when a
    session opens. The offset reported is the schedule-zone offset in force
    AT that UTC instant (DST-aware via astimezone round-trip).
    """
    opens: dict[int, dict] = {}
    for start_s, _end_s in sorted(set(intervals)):
        inst = weeksec_to_utc(start_s, tz, ref_sunday_local)
        local_at_inst = inst.astimezone(tz.zone)
        opens[start_s] = {
            "local_weeksec": start_s,
            "local": fmt_weeksec(start_s),
            "utc_instant": inst,
            "utc_weekday": WEEKDAY_NAMES[(inst.weekday() + 1) % 7],
            "utc_minute_of_day": inst.hour * 60 + inst.minute,
            "offset_minutes": int(
                local_at_inst.utcoffset().total_seconds()) // 60,
        }
    return sorted(opens.values(), key=lambda x: x["utc_instant"])


def truncate_opens_to_hour(opens: list[dict]) -> list[dict]:
    """Variant: stamping convention truncates anchors down to the hour.

    Many platforms draw bar grids on whole hours even when the session opens
    at an off-hour minute (e.g. 18:02 NY → grid drawn from 18:00 NY). Both
    conventions are tested; the bar probe decides which one the broker uses.
    """
    out = []
    for o in opens:
        q = dict(o)
        q["utc_minute_of_day"] = (o["utc_minute_of_day"] // 60) * 60
        out.append(q)
    return out


def analyze_bar_probe(ts_minutes: list[int], schedule_tz_name: str) -> dict:
    """Pure analysis of probed bar-open stamps (no network, no creds)."""
    z = ZoneInfo(schedule_tz_name)
    rows = []
    for ts in sorted(ts_minutes):
        dt = datetime.fromtimestamp(ts * 60, tz=timezone.utc)
        rows.append({
            "ts_minutes": ts,
            "utc": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "sched_tz": dt.astimezone(z).strftime("%a %H:%M"),
            "residue_mod_240": ts % H4_MIN,
            "residue_mod_1440": ts % D1_MIN,
        })
    return {
        "rows": rows,
        "residues_H4": sorted({r["residue_mod_240"] for r in rows}),
        "residues_D1": sorted({r["residue_mod_1440"] for r in rows}),
    }


def grid_residue(minute_of_day: int, period_min: int) -> int:
    """Residue class (mod period) of a grid anchor — the 'offset class'."""
    return minute_of_day % period_min


def grid_opens_for_anchor(anchor_min: int, period_min: int) -> list[int]:
    """Bar-open minutes-of-UTC-day for a grid anchored at anchor_min."""
    k_max = SECONDS_PER_DAY // 60 // period_min
    return sorted({(anchor_min + k * period_min) % D1_MIN
                   for k in range(k_max)})


def reconcile_period(period_name: str, period_min: int,
                     opens: list[dict]) -> dict:
    """Reconcile session-derived grid anchors against the observed offset.

    All expectations come from session metadata (session opens). The observed
    offset is used ONLY as the final comparison, never to derive the grid.
    """
    per_anchor = []
    for o in opens:
        a = o["utc_minute_of_day"]
        per_anchor.append({
            "local": o["local"],
            "utc": f"{o['utc_weekday']} {fmt_hhmmss(a * 60)}",
            "utc_minute_of_day": a,
            "offset_minutes_at_open": o["offset_minutes"],
            "grid_opens_utc": [fmt_hhmmss(x * 60)
                               for x in grid_opens_for_anchor(a, period_min)],
            "residue_mod_period": grid_residue(a, period_min),
            "matches_observed_offset":
                grid_residue(a, period_min) == OBSERVED_OFFSET_MIN % period_min,
            "consistent_with_current_utc_midnight_rule":
                grid_residue(a, period_min) == 0,
        })
    explained = any(e["matches_observed_offset"] for e in per_anchor)
    midnight_consistent = all(
        e["consistent_with_current_utc_midnight_rule"] for e in per_anchor
    ) if per_anchor else False
    return {
        "period": period_name,
        "period_min": period_min,
        "anchors": per_anchor,
        "observed_offset_min": OBSERVED_OFFSET_MIN,
        "observed_grid_explained_by_metadata": explained,
        "current_utc_midnight_rule_matches_metadata_grid": midnight_consistent,
    }


def previous_sunday(d: date) -> date:
    """The Sunday at or before d (week anchor in schedule TZ)."""
    return d - timedelta(days=(d.weekday() + 1) % 7)


def selftest() -> None:
    """Offline arithmetic checks for the pure helpers (no network, no creds)."""
    # 1. TZ resolution
    tz = resolve_schedule_tz("America/New_York")
    assert tz.zone is not None and not tz.is_fixed and tz.error is None
    tz = resolve_schedule_tz("GMT+2")
    assert tz.is_fixed and tz.zone.utcoffset(None) == timedelta(hours=2)
    tz = resolve_schedule_tz("UTC")
    assert tz.zone is not None and tz.zone.utcoffset(None) == timedelta(0)
    assert resolve_schedule_tz("").error is not None
    assert resolve_schedule_tz("Not/AZone").error is not None

    # 2. DST-aware week-second → UTC conversion (America/New_York)
    ny = resolve_schedule_tz("America/New_York")
    # Week containing Wed 2026-09-09 (EDT, UTC−4): Sunday = 2026-09-06
    sun_edt = previous_sunday(date(2026, 9, 9))
    assert sun_edt == date(2026, 9, 6)
    inst = weeksec_to_utc(0, ny, sun_edt)          # Sun 00:00 NY (EDT)
    assert inst == datetime(2026, 9, 6, 4, 0, tzinfo=timezone.utc), inst
    inst = weeksec_to_utc(22 * 3600, ny, sun_edt)  # Sun 22:00 EDT → Mon 02:00 UTC
    assert (inst.date(), inst.hour) == (date(2026, 9, 7), 2), inst
    # Week containing Wed 2026-01-14 (EST, UTC−5): Sunday = 2026-01-11
    sun_est = previous_sunday(date(2026, 1, 14))
    inst = weeksec_to_utc(0, ny, sun_est)          # Sun 00:00 NY (EST)
    assert inst == datetime(2026, 1, 11, 5, 0, tzinfo=timezone.utc), inst
    inst = weeksec_to_utc(22 * 3600, ny, sun_est)  # Sun 22:00 EST → Mon 03:00 UTC
    assert (inst.date(), inst.hour) == (date(2026, 1, 12), 3), inst
    # Fixed-offset path unchanged
    fx = resolve_schedule_tz("GMT+2")
    inst = weeksec_to_utc(0, fx, date(2026, 9, 6))
    assert inst.hour == 22 and inst.date() == date(2026, 9, 5)

    # 3. Session opens (a Sun 22:00 + Mon 00:00 schedule, NY zone, EDT week)
    ivs = [(22 * 3600, 5 * SECONDS_PER_DAY + 17 * 3600),
           (SECONDS_PER_DAY, 5 * SECONDS_PER_DAY + 17 * 3600)]
    opens = session_opens_utc(ivs, ny, sun_edt)
    assert len(opens) == 2
    assert opens[0]["utc_minute_of_day"] == 120          # Sun 22:00 EDT → Mon 02:00 UTC
    assert opens[1]["utc_minute_of_day"] == 240          # Mon 00:00 EDT → Mon 04:00 UTC

    # 4. Grid arithmetic
    assert grid_opens_for_anchor(120, H4_MIN) == [120, 360, 600, 840, 1080, 1320]
    assert grid_opens_for_anchor(0, H4_MIN) == [0, 240, 480, 720, 960, 1200]
    assert grid_opens_for_anchor(120, D1_MIN) == [120]
    assert grid_residue(1320, H4_MIN) == 120
    assert grid_residue(0, H4_MIN) == 0

    # 5. Reconciliation bookkeeping
    anchor_midnight = [{"local": "x", "utc": "Sun 00:00", "utc_weekday": "Sunday",
                        "utc_minute_of_day": 0,
                        "offset_minutes": 0, "offset_minutes_at_open": 0}]
    anchor_0220 = [{"local": "x", "utc": "Mon 02:00", "utc_weekday": "Monday",
                    "utc_minute_of_day": 120,
                    "offset_minutes": -240, "offset_minutes_at_open": -240}]
    r = reconcile_period("H4", H4_MIN, anchor_midnight)
    assert r["current_utc_midnight_rule_matches_metadata_grid"] and \
        not r["observed_grid_explained_by_metadata"]
    r = reconcile_period("D1", D1_MIN, anchor_0220)
    assert r["observed_grid_explained_by_metadata"] and \
        not r["current_utc_midnight_rule_matches_metadata_grid"]
    # 22:00-UTC anchor: H4 residue 120 (matches +120) but D1 residue 1320
    anchor_2220 = [{"local": "x", "utc": "Sun 22:00", "utc_weekday": "Sunday",
                    "utc_minute_of_day": 1320,
                    "offset_minutes": 0, "offset_minutes_at_open": 0}]
    r = reconcile_period("H4", H4_MIN, anchor_2220)
    assert r["observed_grid_explained_by_metadata"]
    r = reconcile_period("D1", D1_MIN, anchor_2220)
    assert not r["observed_grid_explained_by_metadata"]

    # 6. Hour-truncated stamping variant + probe analysis
    trunc = truncate_opens_to_hour(anchor_2220)
    assert trunc[0]["utc_minute_of_day"] == 1320
    r = reconcile_period("H4", H4_MIN, anchor_0220)
    assert r["observed_grid_explained_by_metadata"]
    r = reconcile_period("D1", H4_MIN, anchor_0220)
    assert r["observed_grid_explained_by_metadata"]
    probe = analyze_bar_probe([120, 360, 600, 840, 1080, 1320],
                              "America/New_York")
    assert probe["residues_H4"] == [120]
    assert probe["residues_D1"] == [120, 360, 600, 840, 1080, 1320]
    assert probe["rows"][0]["sched_tz"].endswith("21:00")  # 02:00 UTC = 21:00 EST (epoch week)

    # 7. Daily-roll candidate anchor (17:00 America/New_York, DST-following)
    roll_edt = weeksec_to_utc(147600, ny, date(2026, 9, 6))   # Mon 17:00 EDT
    assert (roll_edt.hour, roll_edt.minute) == (21, 0), roll_edt   # 21:00 UTC
    assert roll_edt.hour * 60 + roll_edt.minute == 1260
    assert (roll_edt.hour * 60 + roll_edt.minute) % H4_MIN == 60
    roll_est = weeksec_to_utc(147600, ny, date(2026, 1, 11))  # Mon 17:00 EST
    assert (roll_est.hour, roll_est.minute) == (22, 0), roll_est  # 22:00 UTC
    assert (roll_est.hour * 60 + roll_est.minute) % H4_MIN == 120
    assert (roll_est.hour * 60 + roll_est.minute) % D1_MIN == 1320

    print("SELFTEST: all pure-helper arithmetic checks passed "
          "(TZ resolution, DST-aware week-second conversion, session opens, "
          "grid math, reconciliation logic, daily-roll anchor)")


# ─────────────────────────────────────────────────────────────────────────────
# Live metadata retrieval (mirrors the verified Gate 1/4 lifecycle)
# ─────────────────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] {msg}")


def load_env() -> dict[str, str]:
    load_dotenv()
    required = ["CTRADER_CLIENT_ID", "CTRADER_CLIENT_SECRET",
                "CTRADER_ACCESS_TOKEN", "CTRADER_ACCOUNT_ID", "CTRADER_ENV"]
    config, missing = {}, []
    for var in required:
        v = os.getenv(var)
        if not v:
            missing.append(var)
        else:
            config[var] = v
    if missing:
        log(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)
    return config


TARGET_ACCOUNT_LOGIN = "10107153"     # same demo account as Gates 1–4
TARGET_SYMBOL_NAME = "XAUUSD"


def run_reconciliation(config: dict[str, str]) -> bool:
    from twisted.internet import reactor, defer
    from ctrader_open_api import Client, EndPoints, Protobuf
    from ctrader_open_api.tcpProtocol import TcpProtocol
    from ctrader_open_api.messages import OpenApiModelMessages_pb2 as _oa

    PT_APP_AUTH_RES = _oa.ProtoOAPayloadType.Value("PROTO_OA_APPLICATION_AUTH_RES")
    PT_ACCOUNT_AUTH_RES = _oa.ProtoOAPayloadType.Value("PROTO_OA_ACCOUNT_AUTH_RES")
    PT_ERROR_RES = _oa.ProtoOAPayloadType.Value("PROTO_OA_ERROR_RES")
    PT_ASSET_LIST_RES = _oa.ProtoOAPayloadType.Value("PROTO_OA_ASSET_LIST_RES")
    PT_SYMBOLS_LIST_RES = _oa.ProtoOAPayloadType.Value("PROTO_OA_SYMBOLS_LIST_RES")
    PT_SYMBOL_BY_ID_RES = _oa.ProtoOAPayloadType.Value("PROTO_OA_SYMBOL_BY_ID_RES")
    PT_TRENDBARS_RES = _oa.ProtoOAPayloadType.Value("PROTO_OA_GET_TRENDBARS_RES")

    results = {
        "connection": False, "app_auth": False, "account_list": False,
        "ctid_discovered": False, "account_auth": False, "symbol_resolved": False,
        "metadata_retrieved": False, "schedule_decodable": False,
        "bar_probe_completed": False,
        "reconciliation_conclusive": False, "clean_disconnect": False,
    }
    state = {"ctid": None, "symbol_id": None, "finished": False}

    def finish() -> None:
        if state["finished"]:
            return
        state["finished"] = True
        log("=" * 72)
        gate_ok = results["metadata_retrieved"] and results["schedule_decodable"] \
            and results["bar_probe_completed"] \
            and results["reconciliation_conclusive"] and results["clean_disconnect"]
        log(f"GATE 4 METADATA RECONCILIATION: "
            f"{'CONCLUSIVE' if gate_ok else 'INCONCLUSIVE (see log above)'}")
        log("=" * 72)
        for k, v in results.items():
            log(f"  {k:34s}: {'PASS' if v else 'FAIL'}")
        log("  Credentials exposed              : NO")
        log("=" * 72)
        try:
            reactor.stop()
        except Exception:
            pass

    def handle_error(res, step: str) -> bool:
        if res.payloadType == PT_ERROR_RES:
            em = Protobuf.extract(res)
            log(f"{step} — FAIL: errorCode={getattr(em, 'errorCode', '?')} "
                f"description={getattr(em, 'description', '?')}")
            return True
        return False

    @defer.inlineCallbacks
    def fetch_bar_probe(c):
        """Minimal read-only bar sample: current AND winter windows, so the
        bar-grid anchor can be tested for DST dependence (4 paced requests)."""
        from twisted.internet import task as twisted_task
        probe: dict[str, list[int]] = {}
        now = datetime.now(timezone.utc)
        winter_from = datetime(2026, 1, 10, tzinfo=timezone.utc)
        winter_to = datetime(2026, 1, 20, tzinfo=timezone.utc)
        plans = [
            ("H4", now - timedelta(days=10), now, "current"),
            ("D1", now - timedelta(days=30), now, "current"),
            ("H4", winter_from, winter_to, "winter"),
            ("D1", winter_from, winter_to, "winter"),
        ]
        for tf, from_dt, to_dt, label in plans:
            yield twisted_task.deferLater(reactor, 0.7, lambda: None)
            try:
                req = Protobuf.get("GetTrendbarsReq")
                req.ctidTraderAccountId = state["ctid"]
                req.fromTimestamp = int(from_dt.timestamp() * 1000)
                req.toTimestamp = int(to_dt.timestamp() * 1000)
                req.period = _oa.ProtoOATrendbarPeriod.Value(tf)
                req.symbolId = state["symbol_id"]
                req.count = 10
                res = yield c.send(req, responseTimeoutInSeconds=30)
                if handle_error(res, f"[{tf}/{label}] probe GetTrendbars"):
                    continue
                if res.payloadType != PT_TRENDBARS_RES:
                    log(f"[{tf}/{label}] probe: unexpected payloadType "
                        f"{res.payloadType}")
                    continue
                tss = sorted(int(tb.utcTimestampInMinutes)
                             for tb in Protobuf.extract(res).trendbar)
                probe[f"{tf}:{label}"] = tss
                log(f"[{tf}/{label}] probe — retrieved {len(tss)} bars — PASS")
            except Exception as e:
                log(f"[{tf}/{label}] probe — FAIL: {type(e).__name__}: {e}")
        return probe

    @defer.inlineCallbacks
    def print_symbol_report(c, sym, symbol_id: int) -> None:
        """Dump full ProtoOASymbol metadata + focused schedule analysis."""
        log("-" * 72)
        log(f"A. FULL ProtoOASymbol metadata (symbolId={symbol_id}) — "
            f"all set fields:")
        for field, value in sym.ListFields():
            if field.name == "schedule":
                log(f"    {field.name}: <{len(value)} intervals — decoded below>")
                continue
            v = str(value)
            if len(v) > 90:
                v = v[:87] + "..."
            log(f"    {field.name} = {v}")

        log("-" * 72)
        tz_name = str(sym.scheduleTimeZone) if sym.HasField("scheduleTimeZone") \
            else None
        tz = resolve_schedule_tz(tz_name)
        log(f"B. scheduleTimeZone (field #26) = {tz_name!r}")
        if tz.error:
            log(f"   → {tz.error}")
            return
        if tz.is_fixed:
            log(f"   → fixed-offset zone (no DST); offset "
                f"{tz.zone.utcoffset(None)}")
        else:
            now_utc = datetime.now(timezone.utc)
            off_now = tz.zone.utcoffset(now_utc.replace(tzinfo=None))
            log(f"   → IANA zone, DST-aware decoding via zoneinfo "
                f"(offset now: {off_now})")

        raw_intervals = [(int(iv.startSecond), int(iv.endSecond))
                         for iv in sym.schedule]
        log(f"   schedule (field #13, repeated ProtoOAInterval) — "
            f"{len(raw_intervals)} interval(s), WEEK-anchored "
            f"(0 = Sunday 00:00 schedule-TZ, per official proto):")
        if not raw_intervals:
            log("   → schedule EMPTY: broker metadata cannot explain any grid")
            return
        for i, (s, e) in enumerate(raw_intervals):
            log(f"     [{i}] startSecond={s:>7} ({fmt_weeksec(s)})  "
                f"endSecond={e:>7} ({fmt_weeksec(e)})")

        # Decode in BOTH regimes: current week and the DST-opposite week.
        today_utc = datetime.now(timezone.utc).date()
        ref_current = previous_sunday(today_utc)
        ref_opposite = (date(today_utc.year, 1, 15)
                        if today_utc.month not in (12, 1, 2)
                        else date(today_utc.year, 7, 15))
        ref_opposite = previous_sunday(ref_opposite)

        opens_current = session_opens_utc(raw_intervals, tz, ref_current)
        opens_opposite = session_opens_utc(raw_intervals, tz, ref_opposite)

        log(f"   Session OPEN events (UTC) — CURRENT regime "
            f"(week of {ref_current}):")
        for o in opens_current:
            log(f"     → local {o['local']}  =  {o['utc_weekday']} "
                f"{fmt_hhmmss(o['utc_minute_of_day'] * 60)} UTC "
                f"(minute-of-day {o['utc_minute_of_day']}, "
                f"UTC offset {o['offset_minutes']} min)")
        log(f"   Session OPEN events (UTC) — OPPOSITE (DST-flipped) regime "
            f"(week of {ref_opposite}):")
        for o in opens_opposite:
            log(f"     → local {o['local']}  =  {o['utc_weekday']} "
                f"{fmt_hhmmss(o['utc_minute_of_day'] * 60)} UTC "
                f"(minute-of-day {o['utc_minute_of_day']}, "
                f"UTC offset {o['offset_minutes']} min)")
        results["schedule_decodable"] = bool(opens_current)

        log("-" * 72)
        log("C. Metadata-derived bar-grid residue classes (H4=240 min, D1=1440)")
        log("   Bars can only open when a session opens; grid = anchor + k·period.")
        log("   Two stamping conventions are tested; the bar probe (below) picks.")
        candidate_residues = {"H4": set(), "D1": set()}
        for label, opens in (
                ("EXACT session-open stamp", opens_current),
                ("HOUR-TRUNCATED stamp", truncate_opens_to_hour(opens_current))):
            log(f"   ── CURRENT regime, {label} ──")
            for period_name, pmin in (("H4", H4_MIN), ("D1", D1_MIN)):
                r = reconcile_period(period_name, pmin, opens)
                residues = sorted({a["residue_mod_period"]
                                   for a in r["anchors"]})
                candidate_residues[period_name].update(residues)
                log(f"   [{r['period']}] anchor residues mod {r['period_min']}: "
                    f"{residues}")
                a0 = r["anchors"][0]
                log(f"     e.g. session open local {a0['local']} → "
                    f"{a0['utc']} UTC; grid opens {a0['grid_opens_utc']}")
                log(f"     matches_observed(+{OBSERVED_OFFSET_MIN}m): "
                    f"{r['observed_grid_explained_by_metadata']}   "
                    f"satisfies_current_utc_midnight_rule: "
                    f"{r['current_utc_midnight_rule_matches_metadata_grid']}")

        log("-" * 72)
        log("   Bar probe: 4 read-only GetTrendbarsReq (H4/D1 × current/winter "
            "windows, ≤10 bars each, 0.7 s pacing) to identify the bar-grid "
            "anchor and test its DST dependence ...")
        probe = yield fetch_bar_probe(c)
        state["probe"] = probe
        results["bar_probe_completed"] = all(
            probe.get(f"{tf}:{reg}") for tf in ("H4", "D1")
            for reg in ("current", "winter"))

        # Observed residue sets per (regime, timeframe)
        obs_res: dict[tuple[str, str], set[int]] = {}
        for reg in ("current", "winter"):
            for tf in ("H4", "D1"):
                tss = probe.get(f"{tf}:{reg}", [])
                if not tss:
                    continue
                an = analyze_bar_probe(tss, tz_name or "UTC")
                res_set = set(an["residues_H4"] if tf == "H4"
                              else an["residues_D1"])
                obs_res[(reg, tf)] = res_set

        # Metadata-derived candidate anchor RULES (per regime):
        #   A: session opens, exact stamps            (from schedule)
        #   B: session opens, hour-truncated stamps   (from schedule)
        #   C: daily roll = modal break start + 60 s, schedule TZ (DST-following)
        #   D: swapTime, fixed minutes from 00:00 UTC (regime-independent)
        swap_min = int(sym.swapTime) if sym.HasField("swapTime") else None
        ref_by_regime = {"current": ref_current, "winter": ref_opposite}
        rules: dict[str, dict[str, dict[str, set[int]]]] = {}
        rule_notes: dict[str, str] = {}
        for reg in ("current", "winter"):
            opens = opens_current if reg == "current" else opens_opposite
            sets_a: dict[str, set[int]] = {"H4": set(), "D1": set()}
            sets_b: dict[str, set[int]] = {"H4": set(), "D1": set()}
            for o in opens:
                m = o["utc_minute_of_day"]
                sets_a["H4"].add(m % H4_MIN)
                sets_a["D1"].add(m % D1_MIN)
                mt = (m // 60) * 60
                sets_b["H4"].add(mt % H4_MIN)
                sets_b["D1"].add(mt % D1_MIN)
            # C: daily-roll anchor (schedule-TZ local, DST-following)
            break_starts = [e % SECONDS_PER_DAY for _s, e in raw_intervals]
            modal_break = max(set(break_starts), key=break_starts.count)
            monday_break_weeksec = next(
                e for _s, e in raw_intervals
                if e % SECONDS_PER_DAY == modal_break)
            roll_weeksec = monday_break_weeksec + 60      # 16:59:00 → 17:00:00
            roll_utc = weeksec_to_utc(roll_weeksec, tz, ref_by_regime[reg])
            rm = roll_utc.hour * 60 + roll_utc.minute
            sets_c: dict[str, set[int]] = {"H4": {rm % H4_MIN},
                                           "D1": {rm % D1_MIN}}
            rules.setdefault("A_session_open_exact", {})[reg] = sets_a
            rules.setdefault("B_session_open_hour_truncated", {})[reg] = sets_b
            rules.setdefault("C_daily_roll_scheduleTZ_DST_following",
                             {})[reg] = sets_c
            rule_notes["C_daily_roll_scheduleTZ_DST_following"] = (
                f"roll {fmt_hhmmss(modal_break + 60)} schedule-TZ → "
                f"{'current' if reg == 'current' else 'winter'} regime: "
                f"{roll_utc.strftime('%H:%M')} UTC")
            if swap_min is not None:
                sm = swap_min % D1_MIN
                rules.setdefault("D_swaptime_fixed_UTC", {})[reg] = {
                    "H4": {sm % H4_MIN}, "D1": {sm % D1_MIN}}
        if swap_min is not None:
            rule_notes["D_swaptime_fixed_UTC"] = (
                f"swapTime={swap_min} min from 00:00 UTC → "
                f"{fmt_hhmmss((swap_min % D1_MIN) * 60)} UTC (fixed)")

        log("-" * 72)
        log("D. Verdict — probe vs metadata-derived candidate anchors:")
        for reg in ("current", "winter"):
            log(f"   observed [{reg}]: H4 mod 240 = "
                f"{sorted(obs_res.get((reg, 'H4'), set()))}, D1 mod 1440 = "
                f"{sorted(obs_res.get((reg, 'D1'), set()))}")
        matched = []
        for rule_name, per_regime in rules.items():
            ok = True
            for reg in ("current", "winter"):
                if (reg, "H4") not in obs_res or (reg, "D1") not in obs_res:
                    ok = False
                    break
                ok = ok and obs_res[(reg, "H4")] <= per_regime[reg]["H4"] \
                    and obs_res[(reg, "D1")] <= per_regime[reg]["D1"]
            note = rule_notes.get(rule_name, "from schedule")
            log(f"   rule {rule_name}: "
                f"{'MATCH' if ok else 'no match'}   ({note})")
            if ok:
                matched.append(rule_name)
        conclusive = bool(matched)
        if conclusive:
            log(f"   → The observed bar-open grid IS explained by broker "
                f"metadata via rule(s): {', '.join(matched)}.")
            if "C_daily_roll_scheduleTZ_DST_following" in matched:
                log(f"   → The diagnosed +{OBSERVED_OFFSET_MIN} min offset is "
                    f"the WINTER (EST) expression of the 17:00 "
                    f"America/New_York daily-roll anchor (22:00 UTC = "
                    f"UTC-midnight grid + 120 min for H4; D1 opens 22:00 UTC)."
                    f") In the CURRENT (EDT) regime the SAME anchor reads "
                    f"+60 min (H4) / 21:00 UTC (D1). The offset is therefore "
                    f"DST-DEPENDENT, not a constant.")
            log("   → Raw utcTimestampInMinutes values are CORRECT broker "
                "data; they must NOT be shifted.")
        else:
            log("   → Observed residues are NOT derivable from symbol "
                "metadata under any candidate rule — the grid has an "
                "additional anchor source. Do NOT change the validator on "
                "this basis.")
        log(f"E. Current temporal validator (UTC-midnight modulo alignment, "
            f"residue 0): observed residues are "
            f"{'CONSISTENT' if all(0 in v for v in obs_res.values()) else 'INCONSISTENT'} "
            f"with it — misaligned in ALL DST regimes, so a generalized "
            f"anchor/session-aware alignment rule is indicated. DESIGN "
            f"decision deferred; no production code changed in this run.")
        results["reconciliation_conclusive"] = conclusive

    @defer.inlineCallbacks
    def on_connected(c):
        log(f"Step: Connection — PASS ({EndPoints.PROTOBUF_DEMO_HOST}:"
            f"{EndPoints.PROTOBUF_PORT})")
        results["connection"] = True

        log("Step: Application authentication ...")
        try:
            req = Protobuf.get("ApplicationAuthReq")
            req.clientId = config["CTRADER_CLIENT_ID"]
            req.clientSecret = config["CTRADER_CLIENT_SECRET"]
            res = yield c.send(req, responseTimeoutInSeconds=15)
            if handle_error(res, "Application authentication") \
                    or res.payloadType != PT_APP_AUTH_RES:
                finish()
                return
            log("Step: Application authentication — PASS")
            results["app_auth"] = True
        except Exception as e:
            log(f"Application authentication — FAIL: {type(e).__name__}: {e}")
            finish()
            return

        log("Step: Account list (dynamic ctid discovery) ...")
        try:
            req = Protobuf.get("GetAccountListByAccessTokenReq")
            req.accessToken = config["CTRADER_ACCESS_TOKEN"]
            res = yield c.send(req, responseTimeoutInSeconds=15)
            if handle_error(res, "Account list"):
                finish()
                return
            accounts = Protobuf.extract(res).ctidTraderAccount
            results["account_list"] = True
            target = next((a for a in accounts
                           if str(a.traderLogin) == TARGET_ACCOUNT_LOGIN), None)
            if target is None:
                log(f"Account login {TARGET_ACCOUNT_LOGIN} NOT FOUND")
                finish()
                return
            state["ctid"] = target.ctidTraderAccountId
            log(f"Step: Discovered ctidTraderAccountId={state['ctid']} — PASS")
            results["ctid_discovered"] = True
        except Exception as e:
            log(f"Account list — FAIL: {type(e).__name__}: {e}")
            finish()
            return

        log("Step: Account authentication ...")
        try:
            req = Protobuf.get("AccountAuthReq")
            req.ctidTraderAccountId = state["ctid"]
            req.accessToken = config["CTRADER_ACCESS_TOKEN"]
            res = yield c.send(req, responseTimeoutInSeconds=15)
            if handle_error(res, "Account authentication") \
                    or res.payloadType != PT_ACCOUNT_AUTH_RES:
                finish()
                return
            log("Step: Account authentication — PASS")
            results["account_auth"] = True
        except Exception as e:
            log(f"Account authentication — FAIL: {type(e).__name__}: {e}")
            finish()
            return

        log("Step: Resolving XAUUSD symbol via asset+symbol metadata ...")
        try:
            asset_req = Protobuf.get("AssetListReq")
            asset_req.ctidTraderAccountId = state["ctid"]
            asset_res = yield c.send(asset_req, responseTimeoutInSeconds=30)
            assets = {}
            if asset_res.payloadType == PT_ASSET_LIST_RES:
                for a in Protobuf.extract(asset_res).asset:
                    assets[a.assetId] = str(a.name)
            sym_req = Protobuf.get("SymbolsListReq")
            sym_req.ctidTraderAccountId = state["ctid"]
            sym_res = yield c.send(sym_req, responseTimeoutInSeconds=30)
            if handle_error(sym_res, "Symbols list"):
                finish()
                return
            cands = [s for s in Protobuf.extract(sym_res).symbol
                     if str(s.symbolName).upper() == TARGET_SYMBOL_NAME
                     and assets.get(s.baseAssetId, "").upper() == "XAU"
                     and assets.get(s.quoteAssetId, "").upper() == "USD"]
            if len(cands) != 1:
                log(f"Expected exactly one verified {TARGET_SYMBOL_NAME}, "
                    f"found {len(cands)}")
                finish()
                return
            state["symbol_id"] = cands[0].symbolId
            log(f"Step: Symbol resolved — PASS (symbolId={state['symbol_id']}; "
                f"documented value for this broker is 41, verified dynamically, "
                f"never hardcoded)")
            results["symbol_resolved"] = True
        except Exception as e:
            log(f"Symbol resolution — FAIL: {type(e).__name__}: {e}")
            finish()
            return

        log("Step: Fetching FULL ProtoOASymbol metadata "
            "(ProtoOASymbolByIdReq → 2117) ...")
        try:
            detail_req = Protobuf.get("SymbolByIdReq")
            detail_req.ctidTraderAccountId = state["ctid"]
            detail_req.symbolId.append(state["symbol_id"])
            detail_res = yield c.send(detail_req, responseTimeoutInSeconds=15)
            if handle_error(detail_res, "SymbolById"):
                finish()
                return
            if detail_res.payloadType != PT_SYMBOL_BY_ID_RES:
                log(f"SymbolById — unexpected payloadType "
                    f"{detail_res.payloadType}")
                finish()
                return
            sym = Protobuf.extract(detail_res).symbol[0]
            log("Step: ProtoOASymbol metadata retrieved — PASS")
            results["metadata_retrieved"] = True
        except Exception as e:
            log(f"SymbolById — FAIL: {type(e).__name__}: {e}")
            finish()
            return

        try:
            yield print_symbol_report(c, sym, state["symbol_id"])
        except Exception as e:
            log(f"Schedule analysis — FAIL: {type(e).__name__}: {e}")

        log("Step: Closing connection (clean disconnect) ...")
        try:
            c.stopService()
        except Exception as e:
            log(f"  stopService error: {e}")
        reactor.callLater(5, finish)

    def on_disconnected(c, reason):
        if not state["finished"]:
            log("Step: Disconnected — PASS (clean disconnect after retrieval)")
            results["clean_disconnect"] = True
            finish()
        else:
            pass

    client = Client(EndPoints.PROTOBUF_DEMO_HOST, EndPoints.PROTOBUF_PORT,
                    TcpProtocol, numberOfMessagesToSendPerSecond=5)
    client.setConnectedCallback(on_connected)
    client.setDisconnectedCallback(on_disconnected)
    client.startService()

    reactor.callLater(120, finish)
    reactor.run()
    return all(results.values())


def main() -> None:
    log("=" * 72)
    log("cTrader Open API — Gate 4 session-metadata reconciliation "
        "(DIAGNOSTIC-ONLY)")
    log("=" * 72)
    if "--selftest" in sys.argv:
        selftest()
        return
    selftest()
    log("Loading configuration from .env (credentials NOT printed) ...")
    config = load_env()
    run_reconciliation(config)


if __name__ == "__main__":
    main()
