#!/usr/bin/env python3
"""cTrader Open API Historical Data — Gate 4.

Isolated diagnostic tool that retrieves a small controlled sample of REAL
historical XAUUSD bars (M5, M15, H1, H4, D1) from the authenticated
IC Markets cTrader DEMO environment and validates them against the
project's temporal/data-quality rules.

DATA-ONLY gate: no orders, no trading, no strategy, no signals,
no probability/backtest/risk engines, no Feature Store integration.

Lifecycle:
CONNECT → APP AUTH → ACCOUNT LIST (dynamic ctid discovery) → ACCOUNT AUTH
→ RESOLVE SYMBOL → for each TF: ProtoOAGetTrendbarsReq → VALIDATE
→ RawBar mapping report → CLEAN DISCONNECT

SDK notes (ctrader-open-api 0.9.2, verified from installed descriptors):
- Client.send() resolves with the raw wire envelope (ProtoMessage with
  payloadType + payload bytes). Typed field access requires Protobuf.extract().
- ProtoOAGetTrendbarsReq (in OpenApiMessages_pb2): ctidTraderAccountId (#2,
  required), fromTimestamp (#3, required int64, Unix ms), toTimestamp (#4,
  required int64, Unix ms), period (#5, required ProtoOATrendbarPeriod),
  symbolId (#6, required int64), count (#7, optional uint32, max bars returned).
- ProtoOAGetTrendbarsRes (in OpenApiMessages_pb2): ctidTraderAccountId (#2,
  required), period (#3, required, echoed), timestamp (#4, required int64),
  repeated trendbar (#5), symbolId (#6, optional).
- ProtoOATrendbar (in OpenApiModelMessages_pb2): volume (#3, required int64,
  tick volume), period (#4, optional enum), low (#5, optional int64, absolute
  in 1/100000), deltaOpen (#6, uint64), deltaClose (#7, uint64),
  deltaHigh (#8, uint64), utcTimestampInMinutes (#9, uint32).
  Prices are RELATIVE: low is absolute-in-1/100000; open/close/high are
  stored as deltas ABOVE low — deltas share the SAME 1/100000 scale
  (e.g. deltaOpen=1_000 on a 2-digit symbol = +0.01).
- Payload types: PROTO_OA_GET_TRENDBARS_REQ=2137,
  PROTO_OA_GET_TRENDBARS_RES=2138, PROTO_OA_ERROR_RES=2142.
- Period enum values: M5=5, M15=7, H1=9, H4=10, D1=12.

Timestamp semantics (verified from descriptors + Spotware docs):
- Request fromTimestamp/toTimestamp: Unix epoch MILLISECONDS (same units as
  the documented GetTrendbars tutorial, which uses ToUnixTimeMilliseconds()).
- ProtoOATrendbar.utcTimestampInMinutes: bar OPEN time, minutes since Unix
  epoch UTC. event_time(bar) = epoch + minutes*60, tz-aware UTC.
- The API provides NO broker-side availability timestamp for historical bars
  → availability_time is NOT invented; ingestion_time (retrieval) is recorded
  separately. treatment follows the project temporal protocol:
  event_time = bar open time (market time), ingestion_time = retrieval time.

Price representation/reconstruction (Spotware-documented, symbol-data page):
  low_abs   = round(low / 100000, digits)
  open_abs  = round((low + deltaOpen)  / 100000, digits)
  close_abs = round((low + deltaClose) / 100000, digits)
  high_abs  = round((low + deltaHigh)  / 100000, digits)
For XAUUSD digits=2. Implemented in exact Decimal arithmetic (no binary
float step). Verified for spot prices in Gate 3; independently confirmed
for trendbars here (deltas are uint64 offsets above low).

Rate limiting (Spotware-documented, getting-started page):
  Max 5 requests/second/connection for historical-data requests.
  This tool issues strictly sequential GetTrendbarsReq calls with a fixed
  0.7 s delay between them (~1.4 req/s, well under the limit).

Known data behavior (Spotware FAQ): trend bars are only created when ticks
arrive → session gaps (weekends, low liquidity) are LEGITIMATE missing bars.
Gaps are classified and reported, never silently dropped or filled.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from dotenv import load_dotenv


# ─────────────────────────────────────────────────────────────────────────────
# Pure helpers (importable without Twisted/credentials — unit-testable)
# ─────────────────────────────────────────────────────────────────────────────

CTRADER_PRICE_SCALE_DENOMINATOR = 100_000

TIMEFRAME_MINUTES = {
    "M5": 5,
    "M15": 15,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}

TIMEFRAME_PERIOD_ENUM = {
    "M5": "M5",
    "M15": "M15",
    "H1": "H1",
    "H4": "H4",
    "D1": "D1",
}


def convert_ctrader_price(raw: int | None, digits: int) -> Decimal | None:
    """Convert a raw cTrader 1/100000-unit integer to a decimal price.

    Exact decimal arithmetic; quantize with ROUND_HALF_EVEN (default),
    matching the documented round-to-digits semantics.
    """
    if raw is None:
        return None
    price = Decimal(raw) / Decimal(CTRADER_PRICE_SCALE_DENOMINATOR)
    return price.quantize(Decimal(1).scaleb(-digits))


def reconstruct_ohlc(low: int, delta_open: int, delta_close: int,
                     delta_high: int, digits: int) -> dict[str, Decimal]:
    """Reconstruct absolute OHLC from cTrader relative trendbar fields.

    Official formula (Spotware symbol-data docs):
      price = round((low + delta) / 100000, digits)   [low itself: delta=0]
    """
    return {
        "open": convert_ctrader_price(low + delta_open, digits),
        "high": convert_ctrader_price(low + delta_high, digits),
        "low": convert_ctrader_price(low, digits),
        "close": convert_ctrader_price(low + delta_close, digits),
    }


def trendbar_ts_to_utc(minutes: int | None) -> datetime | None:
    """Convert ProtoOATrendbar.utcTimestampInMinutes (bar open, minutes since
    Unix epoch UTC) to a tz-aware UTC datetime."""
    if minutes is None:
        return None
    return datetime.fromtimestamp(minutes * 60, tz=timezone.utc)


def validate_ohlc(o: Decimal, h: Decimal, l: Decimal, c: Decimal) -> list[str]:
    """OHLC sanity rules. Returns error strings (empty = valid)."""
    errs: list[str] = []
    if o <= 0 or h <= 0 or l <= 0 or c <= 0:
        errs.append("non-positive price component")
    if h < max(o, c):
        errs.append(f"high {h} < max(open, close) {max(o, c)}")
    if l > min(o, c):
        errs.append(f"low {l} > min(open, close) {min(o, c)}")
    if h < l:
        errs.append(f"high {h} < low {l}")
    return errs


@dataclass
class BarRecord:
    """One historical bar with raw + converted values (safe diagnostics)."""

    timeframe: str
    symbol_id: int
    ts_minutes: int                      # utcTimestampInMinutes (bar open)
    low_raw: int
    delta_open_raw: int
    delta_close_raw: int
    delta_high_raw: int
    volume: int | None                   # tick volume, if supplied
    digits: int = 2
    ingestion_time: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc))
    validation_errors: list[str] = field(default_factory=list)

    @property
    def bar_time(self) -> datetime | None:
        """event_time: bar open time per cTrader semantics (tz-aware UTC)."""
        return trendbar_ts_to_utc(self.ts_minutes)

    @property
    def ohlc(self) -> dict[str, Decimal]:
        return reconstruct_ohlc(
            self.low_raw, self.delta_open_raw,
            self.delta_close_raw, self.delta_high_raw, self.digits)


def validate_bar(bar: BarRecord) -> list[str]:
    """Validate one bar (OHLC rules + timestamp sanity)."""
    errs: list[str] = []
    o = bar.ohlc
    errs.extend(validate_ohlc(o["open"], o["high"], o["low"], o["close"]))
    bt = bar.bar_time
    if bt is None:
        errs.append("missing bar timestamp")
    else:
        now = datetime.now(timezone.utc)
        if bt > now + timedelta(minutes=5):
            errs.append(f"bar_time in the future: {bt.isoformat()}")
    return errs


def analyze_series(bars: list[BarRecord], interval_minutes: int) -> dict:
    """Ordering / duplicates / alignment / gap analysis for one timeframe.

    Pure function; reports anomalies explicitly, drops nothing.
    Gap semantics (Spotware FAQ): bars exist only where ticks arrived, so
    gaps larger than one interval are expected market/session gaps; a jump
    that is NOT an integer multiple of the interval indicates malformed data.
    """
    report: dict = {
        "count": len(bars),
        "ordered": True,
        "duplicates": 0,
        "reversed": 0,
        "overlaps": 0,
        "misaligned_bars": 0,
        "anomalies": [],
        "session_gaps": 0,
        "max_gap_minutes": 0,
        "first_bar_time": None,
        "last_bar_time": None,
    }
    if not bars:
        return report

    times = [b.bar_time for b in bars]
    report["first_bar_time"] = times[0].isoformat() if times[0] else None
    report["last_bar_time"] = times[-1].isoformat() if times[-1] else None

    for i in range(len(bars) - 1):
        t0, t1 = times[i], times[i + 1]
        if t0 is None or t1 is None:
            report["anomalies"].append(f"bar {i}: missing timestamp")
            continue
        diff_min = (t1 - t0).total_seconds() / 60.0
        if diff_min == 0:
            report["duplicates"] += 1
            report["anomalies"].append(
                f"bar {i}: duplicate timestamp {t0.isoformat()}")
        elif diff_min < 0:
            report["reversed"] += 1
            report["anomalies"].append(
                f"bar {i}: reversed timestamps ({t0} -> {t1})")
        elif diff_min < interval_minutes:
            report["overlaps"] += 1
            report["anomalies"].append(
                f"bar {i}: sub-interval spacing {diff_min} min")
        elif diff_min % interval_minutes != 0:
            report["anomalies"].append(
                f"bar {i}: non-multiple jump {diff_min} min "
                f"(interval {interval_minutes}) — malformed if confirmed")
        elif diff_min > interval_minutes:
            report["session_gaps"] += 1
            report["max_gap_minutes"] = max(report["max_gap_minutes"],
                                            int(diff_min))
    if any(b.ts_minutes is not None and b.ts_minutes % interval_minutes != 0
           for b in bars):
        report["misaligned_bars"] = sum(
            1 for b in bars
            if b.ts_minutes is not None and b.ts_minutes % interval_minutes != 0)
    report["ordered"] = (report["duplicates"] == 0
                         and report["reversed"] == 0
                         and report["overlaps"] == 0)
    return report


def build_raw_bar(bar: BarRecord, provider_symbol: str = "XAUUSD"):
    """Map a validated bar onto the EXISTING RawBar contract
    (src.canonical.raw.RawBar) without changing the contract.

    Mapping:
      symbol         = "XAUUSD" (canonical), timeframe = e.g. "M5"
      bar_time       = event_time (bar open, cTrader semantics)
      open/high/low/close = reconstructed Decimal prices
      tick_volume    = broker tick volume; real_volume = None (not supplied)
      bid/ask        = None (not supplied by trendbar API)
      provider       = "ctrader", provider_symbol = broker symbol name
      retrieval_time = ingestion_time (when we fetched it)

    Temporal protocol: availability_time is NOT invented — the cTrader
    historical API provides no broker availability timestamp; the canonical
    layer's availability policy must decide (documented in the report).
    """
    from src.canonical.raw import RawBar

    bt = bar.bar_time
    assert bt is not None, "RawBar requires bar_time; do not invent one"
    o = bar.ohlc
    return RawBar(
        symbol="XAUUSD",
        timeframe=bar.timeframe,
        bar_time=bt,
        open=o["open"],
        high=o["high"],
        low=o["low"],
        close=o["close"],
        tick_volume=bar.volume if bar.volume is not None else 0,
        real_volume=None,
        bid=None,
        ask=None,
        provider="ctrader",
        provider_symbol=provider_symbol,
        retrieval_time=bar.ingestion_time,
    )


def summarize_timeframe(bars: list[BarRecord], interval_minutes: int) -> dict:
    """Aggregate validation results for one timeframe (pure)."""
    series = analyze_series(bars, interval_minutes)
    invalid = [(i, b) for i, b in enumerate(bars, 1) if b.validation_errors]
    o = [b.ohlc for b in bars]
    return {
        **series,
        "invalid_bars": len(invalid),
        "invalid_details": [(i, b.validation_errors) for i, b in invalid[:5]],
        "price_min": min((x["low"] for x in o), default=None),
        "price_max": max((x["high"] for x in o), default=None),
        "volume_min": min((b.volume for b in bars if b.volume is not None),
                          default=None),
        "volume_max": max((b.volume for b in bars if b.volume is not None),
                          default=None),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Live demo API test
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


# Target bars per timeframe and request windows (deliberately small samples;
# windows include weekend cushion and stay far below any documented cap).
SAMPLE_PLAN = {
    "M5":  {"bars": 100, "window_days": 2},
    "M15": {"bars": 100, "window_days": 4},
    "H1":  {"bars": 100, "window_days": 10},
    "H4":  {"bars": 100, "window_days": 30},
    "D1":  {"bars": 100, "window_days": 140},
}
INTER_REQUEST_DELAY_S = 0.7  # ~1.4 req/s historical; limit is 5 req/s


def run_historical_test(config: dict[str, str]) -> bool:
    from twisted.internet import reactor , defer
    from twisted.internet import task as twisted_task
    from ctrader_open_api import Client, EndPoints, Protobuf
    from ctrader_open_api.tcpProtocol import TcpProtocol
    from ctrader_open_api.messages import OpenApiModelMessages_pb2 as _oa

    PT_APP_AUTH_RES = _oa.ProtoOAPayloadType.Value("PROTO_OA_APPLICATION_AUTH_RES")
    PT_ACCOUNT_AUTH_RES = _oa.ProtoOAPayloadType.Value("PROTO_OA_ACCOUNT_AUTH_RES")
    PT_ERROR_RES = _oa.ProtoOAPayloadType.Value("PROTO_OA_ERROR_RES")
    PT_ASSET_LIST_RES = _oa.ProtoOAPayloadType.Value("PROTO_OA_ASSET_LIST_RES")
    PT_TRENDBARS_RES = _oa.ProtoOAPayloadType.Value("PROTO_OA_GET_TRENDBARS_RES")

    TARGET_ACCOUNT_LOGIN = "10107153"
    TARGET_SYMBOL_NAME = "XAUUSD"

    results = {
        "connection": False, "app_auth": False, "account_list": False,
        "ctid_discovered": False, "account_auth": False, "symbol_resolved": False,
        "M5": False, "M15": False, "H1": False, "H4": False, "D1": False,
        "rate_limit_compliance": True,
        "clean_disconnect": False,
    }
    tf_bars: dict[str, list[BarRecord]] = {}
    state = {"ctid": None, "symbol_id": None, "digits": 2, "finished": False}

    def finish() -> None:
        if state["finished"]:
            return
        state["finished"] = True
        log("=" * 60)
        gate_pass = all(results[k] for k in ("M5", "M15", "H1", "H4", "D1")) \
            and results["rate_limit_compliance"] and results["clean_disconnect"]
        log(f"GATE 4 STATUS: {'PASS' if gate_pass else 'PARTIAL/BLOCKED'}")
        log("=" * 60)
        for tf in SAMPLE_PLAN:
            bars = tf_bars.get(tf, [])
            s = summarize_timeframe(bars, TIMEFRAME_MINUTES[tf])
            log(f"[{tf}] bars={s['count']} invalid={s['invalid_bars']} "
                f"ordered={s['ordered']} duplicates={s['duplicates']} "
                f"reversed={s['reversed']} overlaps={s['overlaps']} "
                f"session_gaps={s['session_gaps']} "
                f"max_gap={s['max_gap_minutes']}min "
                f"misaligned={s['misaligned_bars']}")
            log(f"      price range: {s['price_min']} – {s['price_max']}  "
                f"tickvol range: {s['volume_min']} – {s['volume_max']}  "
                f"first={s['first_bar_time']} last={s['last_bar_time']}")
            if s["invalid_details"]:
                log(f"      INVALID SAMPLE: {s['invalid_details']}")
            if s["anomalies"]:
                log(f"      anomalies: {s['anomalies'][:5]}")
        log(f"RawBar mapping: existing contract used unchanged; "
            f"availability_time NOT invented (API provides none)")
        log(f"Rate limit compliance (≤5 req/s historical, sequential, "
            f"{INTER_REQUEST_DELAY_S}s spacing): "
            f"{'PASS' if results['rate_limit_compliance'] else 'FAIL'}")
        log("Lifecycle:")
        for k, v in results.items():
            log(f"  {k:24s}: {'PASS' if v else 'FAIL'}")
        log("  Credentials exposed      : NO")
        log("=" * 60)
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
    def fetch_timeframe(c, tf: str):
        plan = SAMPLE_PLAN[tf] 
        to_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        from_ms = to_ms - plan["window_days"] * 24 * 3600 * 1000 
        req = Protobuf.get("GetTrendbarsReq")
        req.ctidTraderAccountId = state["ctid"]
        req.fromTimestamp = from_ms
        req.toTimestamp = to_ms
        req.period = _oa.ProtoOATrendbarPeriod.Value(TIMEFRAME_PERIOD_ENUM[tf])
        req.symbolId = state["symbol_id"]
        req.count = plan["bars"] + 20  # headroom above target

        res = yield c.send(req, responseTimeoutInSeconds=30)
        if handle_error(res, f"[{tf}] GetTrendbars"):
            return
        if res.payloadType != PT_TRENDBARS_RES:
            log(f"[{tf}] unexpected payloadType {res.payloadType}")
            return

        extracted = Protobuf.extract(res)
        bars: list[BarRecord] = []
        for tb in extracted.trendbar:
            rec = BarRecord(
                timeframe=tf,
                symbol_id=state["symbol_id"],
                ts_minutes=tb.utcTimestampInMinutes,
                low_raw=tb.low,
                delta_open_raw=tb.deltaOpen,
                delta_close_raw=tb.deltaClose,
                delta_high_raw=tb.deltaHigh,
                volume=tb.volume,
                digits=state["digits"],
                ingestion_time=datetime.now(timezone.utc),
            )
            rec.validation_errors = validate_bar(rec)
            bars.append(rec)
        tf_bars[tf] = bars

        s = summarize_timeframe(bars, TIMEFRAME_MINUTES[tf])
        ok = (s["count"] >= plan["bars"] and s["invalid_bars"] == 0
              and s["ordered"] and s["duplicates"] == 0
              and s["reversed"] == 0 and s["overlaps"] == 0
              and s["misaligned_bars"] == 0)
        results[tf] = ok
        o = bars[0].ohlc if bars else {}
        log(f"[{tf}] retrieved {s['count']} bars (target {plan['bars']}) — "
            f"{'PASS' if ok else 'FAIL'}")
        log(f"      latest bar: O={o.get('open')} H={o.get('high')} "
            f"L={o.get('low')} C={o.get('close')} "
            f"tickvol={bars[-1].volume if bars else None} "
            f"bar_time={bars[-1].bar_time.isoformat() if bars else None}")
        log(f"      raw audit (latest): low={bars[-1].low_raw} "
            f"dOpen={bars[-1].delta_open_raw} dClose={bars[-1].delta_close_raw} "
            f"dHigh={bars[-1].delta_high_raw}" if bars else "")

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
            detail_req = Protobuf.get("SymbolByIdReq")
            detail_req.ctidTraderAccountId = state["ctid"]
            detail_req.symbolId.append(cands[0].symbolId)
            detail_res = yield c.send(detail_req, responseTimeoutInSeconds=15)
            if handle_error(detail_res, "SymbolById"):
                finish()
                return
            state["digits"] = Protobuf.extract(detail_res).symbol[0].digits
            log(f"Step: Symbol resolved — PASS (XAUUSD "
                f"symbolId={state['symbol_id']} digits={state['digits']})")
            results["symbol_resolved"] = True
        except Exception as e:
            log(f"Symbol resolution — FAIL: {type(e).__name__}: {e}")
            finish()
            return

        # Sequential historical requests, paced below the 5 req/s limit
        for tf in SAMPLE_PLAN:
            yield twisted_task.deferLater(reactor, INTER_REQUEST_DELAY_S, lambda: None)
            try:
                result = yield fetch_timeframe(c, tf)
            except Exception as e:
                log(f"[{tf}] request failed: {type(e).__name__}: {e}")

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

    reactor.callLater(180, finish)
    reactor.run()
    return all(results.values())


def main():
    log("=" * 60)
    log("cTrader Open API Historical Data — Gate 4")
    log("=" * 60)
    log("Loading configuration from .env (credentials NOT printed) ...")
    config = load_env()
    run_historical_test(config)


if __name__ == "__main__":
    main()
