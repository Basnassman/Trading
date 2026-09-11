#!/usr/bin/env python3
"""cTrader Open API Real-Time Spot Stream — Gate 3.

Isolated diagnostic tool that verifies real-time XAUUSD market data delivery
from the authenticated IC Markets cTrader DEMO environment.
DATA-ONLY gate: no orders, no trading, no strategy, no signals, no risk.

Lifecycle:
CONNECT → APPLICATION AUTH → ACCOUNT LIST (dynamic ctid discovery)
→ ACCOUNT AUTH → RESOLVE SYMBOL → SUBSCRIBE SPOTS → RECEIVE ProtoOASpotEvent
→ VALIDATE → UNSUBSCRIBE → CLEAN DISCONNECT

SDK notes (ctrader-open-api 0.9.2, verified from installed descriptors):
- Client.send() resolves with the raw wire envelope (ProtoMessage with
  payloadType + payload bytes). Typed field access requires Protobuf.extract().
- ProtoOASubscribeSpotsReq: ctidTraderAccountId (#2), repeated symbolId (#3),
  optional subscribeToSpotTimestamp (#4, bool). Setting it True requests that
  ProtoOASpotEvent carries the optional 'timestamp' field (#8, int64, ms).
- ProtoOASpotEvent: symbolId (#2), optional bid (#4, uint64),
  optional ask (#5, uint64), optional timestamp (#8, int64 ms).
- Payload types: PROTO_OA_SUBSCRIBE_SPOTS_RES=2128,
  PROTO_OA_UNSUBSCRIBE_SPOTS_RES=2130, PROTO_OA_SPOT_EVENT=2131.

Price representation (Spotware-documented, verified against descriptors):
SpotEvent bid/ask are integers expressed in 1/100000 of a price unit.
Conversion:  price = round(raw / 100000, symbol.digits)
For XAUUSD digits=2 → price = round(raw / 100000, 2).

Timestamp semantics (temporal protocol):
- SpotEvent.timestamp (when present) is the server-side market data timestamp,
  Unix epoch MILLISECONDS — the same representation as all cTrader timestamps
  (e.g. GetTrendbarsReq fromTimestamp/toTimestamp).
- event_time       = SpotEvent.timestamp converted to tz-aware UTC.
- ingestion_time   = local UTC receipt time (never used as event_time).
- availability_time ≈ ingestion_time for a live push stream (the broker does
  not provide a separate availability marker for spot events).
- event_time is NEVER invented: if an event carries no server timestamp the
  fact is reported explicitly as a warning, not silently papered over.
- Rule enforced: event_time must not be in the future relative to local clock
  (Available_i(t) = 1[AvailabilityTimestamp_i <= t] — no future timestamps).

Security:
- NEVER prints Client Secret, Access Token, Refresh Token
- Only outputs safe diagnostic information
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


def convert_ctrader_price(raw: int | None, digits: int) -> Decimal | None:
    """Convert a raw cTrader price integer to a decimal price.

    Formula (Spotware-documented): price = round(raw / 100000, digits).
    Implemented in exact decimal arithmetic (no binary-float step) so the
    resulting Decimal is the clean rounded value, e.g. 433755000 → 4337.55.
    Uses ROUND_HALF_EVEN, matching the SDK examples' rounding semantics.
    Returns None for None input (bid/ask are optional proto2 fields).
    """
    if raw is None:
        return None
    price = Decimal(raw) / Decimal(CTRADER_PRICE_SCALE_DENOMINATOR)
    return price.quantize(Decimal(1).scaleb(-digits))


def spot_timestamp_to_utc(ms: int | None) -> datetime | None:
    """Convert a cTrader SpotEvent timestamp (Unix epoch MILLISECONDS) to a
    timezone-aware UTC datetime. Returns None for None input."""
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)


@dataclass
class SpotEventRecord:
    """Validated record of one received spot event (safe diagnostic data)."""

    symbol_id: int
    bid_raw: int | None
    ask_raw: int | None
    timestamp_ms: int | None          # server event_time, ms (may be None)
    ingestion_time: datetime          # local UTC receipt time
    digits: int = 2
    validation_errors: list[str] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)

    @property
    def bid(self) -> Decimal | None:
        return convert_ctrader_price(self.bid_raw, self.digits)

    @property
    def ask(self) -> Decimal | None:
        return convert_ctrader_price(self.ask_raw, self.digits)

    @property
    def event_time(self) -> datetime | None:
        return spot_timestamp_to_utc(self.timestamp_ms)

    @property
    def spread(self) -> Decimal | None:
        b, a = self.bid, self.ask
        if b is None or a is None:
            return None
        return a - b

    def validate(self) -> None:
        """Data-quality validation. Populates errors (event invalid) and
        warnings (event usable but incomplete, e.g. missing server timestamp).
        """
        errs: list[str] = []
        warns: list[str] = []
        b, a = self.bid, self.ask
        if b is None:
            errs.append("missing bid")
        elif b <= 0:
            errs.append(f"non-positive bid {b}")
        if a is None:
            errs.append("missing ask")
        elif a <= 0:
            errs.append(f"non-positive ask {a}")
        if b is not None and a is not None and a < b:
            errs.append(f"ask < bid ({a} < {b})")
        spread = self.spread
        if spread is not None and spread < 0:
            errs.append(f"negative spread {spread}")

        if self.timestamp_ms is None:
            warns.append("missing server event timestamp")
        elif self.timestamp_ms <= 0:
            errs.append(f"non-positive timestamp {self.timestamp_ms}")
        else:
            et = self.event_time
            assert et is not None
            now = datetime.now(timezone.utc)
            if et > now + timedelta(minutes=5):
                errs.append(f"impossible future event_time {et.isoformat()}")
            elif et > now + timedelta(seconds=2):
                warns.append(f"event_time slightly ahead of local clock "
                             f"(possible clock skew): {et.isoformat()}")
            elif (now - et).total_seconds() > 24 * 3600:
                errs.append(f"stale event_time {et.isoformat()}")

        self.validation_errors = errs
        self.validation_warnings = warns


def summarize(events: list[SpotEventRecord]) -> dict:
    """Summarize a sample of spot events (pure, unit-testable)."""
    valid = [e for e in events if not e.validation_errors]
    invalid = [e for e in events if e.validation_errors]
    with_ts = [e for e in valid if e.timestamp_ms is not None]

    bids = [e.bid for e in valid if e.bid is not None]
    asks = [e.ask for e in valid if e.ask is not None]
    spreads = [e.spread for e in valid if e.spread is not None]
    ets = [e.event_time for e in with_ts if e.event_time is not None]
    lags_ms = [round((e.ingestion_time - e.event_time).total_seconds() * 1000)
               for e in with_ts if e.event_time is not None]

    def rng(vals):
        return (min(vals), max(vals)) if vals else (None, None)

    ordered = all(ets[i] <= ets[i + 1] for i in range(len(ets) - 1))
    no_future = all(lag >= -5000 for lag in lags_ms)  # allow ≤5s clock skew

    return {
        "received": len(events),
        "valid": len(valid),
        "invalid": len(invalid),
        "invalid_reasons": sorted({r for e in invalid for r in e.validation_errors}),
        "warnings": sorted({w for e in valid for w in e.validation_warnings}),
        "symbol_ids": sorted({e.symbol_id for e in events}),
        "bid_range": rng(bids),
        "ask_range": rng(asks),
        "spread_range": rng(spreads),
        "with_server_timestamp": len(with_ts),
        "event_time_range": rng(ets),
        "event_times_ordered": ordered if len(ets) >= 2 else (True if ets else False),
        "no_future_event_time": no_future if lags_ms else False,
        "receipt_lag_ms_range": rng(lags_ms),
    }


def build_raw_tick(record: SpotEventRecord, provider_symbol: str = "XAUUSD"):
    """Map a validated spot event onto the EXISTING RawTick contract
    (src.canonical.raw.RawTick) without changing the contract.

    Field mapping:
      symbol          = "XAUUSD"                (canonical symbol)
      bid/ask         = converted Decimal prices
      timestamp       = event_time (server timestamp; RawTick requires a
                        datetime, so events without one cannot be mapped —
                        reported, never invented)
      retrieval_time  = ingestion_time (local UTC receipt)
      provider        = "ctrader"
      provider_symbol = broker symbol name
    """
    from src.canonical.raw import RawTick

    et = record.event_time
    assert et is not None, "RawTick requires event_time; do not invent one"
    return RawTick(
        symbol="XAUUSD",
        bid=record.bid,
        ask=record.ask,
        timestamp=et,
        provider="ctrader",
        provider_symbol=provider_symbol,
        retrieval_time=record.ingestion_time,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Live demo API test
# ─────────────────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    """Print timestamped log message."""
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] {msg}")


def load_env() -> dict[str, str]:
    """Load cTrader credentials from .env. NEVER prints the values."""
    load_dotenv()
    required_vars = [
        "CTRADER_CLIENT_ID",
        "CTRADER_CLIENT_SECRET",
        "CTRADER_ACCESS_TOKEN",
        "CTRADER_ACCOUNT_ID",
        "CTRADER_ENV",
    ]
    config, missing = {}, []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            config[var] = value
    if missing:
        log(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)
    return config


def run_spot_stream(config: dict[str, str]) -> bool:
    """Run the Gate 3 real-time spot stream test."""
    from twisted.internet import reactor, defer
    from ctrader_open_api import Client, EndPoints, Protobuf
    from ctrader_open_api.tcpProtocol import TcpProtocol
    from ctrader_open_api.messages import OpenApiModelMessages_pb2 as _oa_model

    PT_APP_AUTH_RES = _oa_model.ProtoOAPayloadType.Value("PROTO_OA_APPLICATION_AUTH_RES")
    PT_ACCOUNT_AUTH_RES = _oa_model.ProtoOAPayloadType.Value("PROTO_OA_ACCOUNT_AUTH_RES")
    PT_ERROR_RES = _oa_model.ProtoOAPayloadType.Value("PROTO_OA_ERROR_RES")
    PT_ASSET_LIST_RES = _oa_model.ProtoOAPayloadType.Value("PROTO_OA_ASSET_LIST_RES")
    PT_SUB_SPOTS_RES = _oa_model.ProtoOAPayloadType.Value("PROTO_OA_SUBSCRIBE_SPOTS_RES")
    PT_UNSUB_SPOTS_RES = _oa_model.ProtoOAPayloadType.Value("PROTO_OA_UNSUBSCRIBE_SPOTS_RES")
    PT_SPOT_EVENT = _oa_model.ProtoOAPayloadType.Value("PROTO_OA_SPOT_EVENT")

    TARGET_ACCOUNT_LOGIN = "10107153"
    TARGET_SYMBOL_NAME = "XAUUSD"
    MIN_EVENTS = 10
    OBSERVATION_WINDOW_S = 25
    SPARSE_EXTENSION_S = 35

    results = {
        "connection": False,
        "app_auth": False,
        "account_list": False,
        "ctid_discovered": False,
        "account_auth": False,
        "subscription": False,
        "spot_events_received": False,
        "data_quality": False,
        "temporal_validation": False,
        "unsubscribe": False,
        "clean_disconnect": False,
    }

    events: list[SpotEventRecord] = []
    state = {
        "ctid": None, "symbol_id": None, "digits": 2,
        "subscribed": False, "unsub_started": False,
        "window_extended": False, "finished": False,
    }

    def finish() -> None:
        if state["finished"]:
            return
        state["finished"] = True

        s = summarize(events)
        if s["valid"] > 0:
            results["data_quality"] = (s["valid"] == s["received"])
            results["temporal_validation"] = (
                s["with_server_timestamp"] == s["valid"]
                and s["event_times_ordered"]
                and s["no_future_event_time"]
            )

        if all(results.values()) and s["valid"] >= MIN_EVENTS:
            status = "PASS"
        elif s["received"] == 0 and not (
                results["subscription"] and results["account_auth"]):
            status = "BLOCKED"
        else:
            status = "PARTIAL"

        log("=" * 60)
        log(f"GATE 3 STATUS: {status}")
        log("=" * 60)
        log("Sample summary (safe diagnostics only):")
        log(f"  events received         : {s['received']}")
        log(f"  valid                   : {s['valid']}")
        log(f"  invalid                 : {s['invalid']} "
            f"reasons={s['invalid_reasons'] or 'none'}")
        log(f"  warnings                : {s['warnings'] or 'none'}")
        log(f"  symbolIds seen          : {s['symbol_ids']}")
        log(f"  bid range               : {s['bid_range']}")
        log(f"  ask range               : {s['ask_range']}")
        log(f"  spread range            : {s['spread_range']}")
        log(f"  events w/ server ts     : {s['with_server_timestamp']}/{s['valid']}")
        log(f"  event_time range (UTC)  : {s['event_time_range']}")
        log(f"  event_time ordering     : "
            f"{'OK' if s['event_times_ordered'] else 'OUT OF ORDER'}")
        log(f"  no future event_time    : "
            f"{'OK' if s['no_future_event_time'] else 'VIOLATED/N-A'}")
        log(f"  receipt lag ms range    : {s['receipt_lag_ms_range']}")
        log("Lifecycle results:")
        for k, v in results.items():
            log(f"  {k:22s}: {'PASS' if v else 'FAIL'}")
        log("  Credentials exposed     : NO")
        log("=" * 60)
        try:
            reactor.stop()
        except Exception:
            pass

    def handle_error(res, step: str) -> bool:
        if res.payloadType == PT_ERROR_RES:
            error_msg = Protobuf.extract(res)
            log(f"{step} — FAIL: errorCode={getattr(error_msg, 'errorCode', '?')} "
                f"description={getattr(error_msg, 'description', '?')}")
            return True
        return False

    def start_clean_disconnect(c) -> None:
        """Initiate graceful close after unsubscribe."""
        log("Step: Closing connection (clean disconnect) ...")
        try:
            c.stopService()
        except Exception as e:
            log(f"  stopService error: {e}")
        reactor.callLater(8, finish)  # safety in case disconnect event lags

    @defer.inlineCallbacks
    def unsubscribe(c) -> None:
        state["unsub_started"] = True
        try:
            unsub_req = Protobuf.get("UnsubscribeSpotsReq")
            unsub_req.ctidTraderAccountId = state["ctid"]
            unsub_req.symbolId.append(state["symbol_id"])
            unsub_res = yield c.send(unsub_req, responseTimeoutInSeconds=10)
            if unsub_res.payloadType == PT_UNSUB_SPOTS_RES:
                log("Step: Unsubscribe — PASS (PROTO_OA_UNSUBSCRIBE_SPOTS_RES)")
                results["unsubscribe"] = True
            elif not handle_error(unsub_res, "Unsubscribe"):
                log(f"Unsubscribe: unexpected payloadType {unsub_res.payloadType}")
        except Exception as e:
            log(f"Unsubscribe — FAIL: {type(e).__name__}: {e}")
        start_clean_disconnect(c)

    @defer.inlineCallbacks
    def on_message(c, message):
        """Push handler for spot events (push events carry no clientMsgId)."""
        if state["finished"] or message.payloadType != PT_SPOT_EVENT:
            return
        ev = Protobuf.extract(message)
        rec = SpotEventRecord(
            symbol_id=ev.symbolId,
            bid_raw=ev.bid if ev.HasField("bid") else None,
            ask_raw=ev.ask if ev.HasField("ask") else None,
            timestamp_ms=ev.timestamp if ev.HasField("timestamp") else None,
            ingestion_time=datetime.now(timezone.utc),
            digits=state["digits"],
        )
        rec.validate()
        events.append(rec)
        results["spot_events_received"] = True

        log(f"  EVENT #{len(events)}: symbolId={rec.symbol_id} "
            f"Bid={rec.bid} Ask={rec.ask} Spread={rec.spread} "
            f"raw=({rec.bid_raw},{rec.ask_raw}) "
            f"event_time={rec.event_time.isoformat() if rec.event_time else 'MISSING'} "
            f"ingestion={rec.ingestion_time.isoformat()}")
        if rec.validation_errors:
            log(f"    VALIDATION ERRORS: {rec.validation_errors}")
        if rec.validation_warnings:
            log(f"    warnings: {rec.validation_warnings}")

        valid_count = sum(1 for e in events if not e.validation_errors)
        if (state["subscribed"] and not state["unsub_started"]
                and valid_count >= MIN_EVENTS):
            log(f"  Collected {valid_count} valid events (target {MIN_EVENTS}) — "
                f"unsubscribing ...")
            yield unsubscribe(c)

    @defer.inlineCallbacks
    def on_connected(c):
        log(f"Step: Connection — PASS ({EndPoints.PROTOBUF_DEMO_HOST}:"
            f"{EndPoints.PROTOBUF_PORT})")
        results["connection"] = True

        # ── Application auth ─────────────────────────────
        log("Step: Application authentication ...")
        try:
            req = Protobuf.get("ApplicationAuthReq")
            req.clientId = config["CTRADER_CLIENT_ID"]
            req.clientSecret = config["CTRADER_CLIENT_SECRET"]
            res = yield c.send(req, responseTimeoutInSeconds=15)
            if handle_error(res, "Application authentication"):
                finish()
                return
            if res.payloadType != PT_APP_AUTH_RES:
                log(f"Unexpected payloadType {res.payloadType}")
                finish()
                return
            log("Step: Application authentication — PASS")
            results["app_auth"] = True
        except Exception as e:
            log(f"Application authentication — FAIL: {type(e).__name__}: {e}")
            finish()
            return

        # ── Account list / dynamic discovery ─────────────
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
            log(f"Step: Discovered ctidTraderAccountId={state['ctid']} "
                f"(dynamic, not hardcoded) — PASS")
            results["ctid_discovered"] = True
        except Exception as e:
            log(f"Account list — FAIL: {type(e).__name__}: {e}")
            finish()
            return

        # ── Account auth ─────────────────────────────────
        log("Step: Account authentication ...")
        try:
            req = Protobuf.get("AccountAuthReq")
            req.ctidTraderAccountId = state["ctid"]
            req.accessToken = config["CTRADER_ACCESS_TOKEN"]
            res = yield c.send(req, responseTimeoutInSeconds=15)
            if handle_error(res, "Account authentication"):
                finish()
                return
            if res.payloadType != PT_ACCOUNT_AUTH_RES:
                log(f"Unexpected payloadType {res.payloadType}")
                finish()
                return
            log("Step: Account authentication — PASS")
            results["account_auth"] = True
        except Exception as e:
            log(f"Account authentication — FAIL: {type(e).__name__}: {e}")
            finish()
            return

        # ── Symbol re-resolution (no hardcoded symbolId) ──
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
            candidates = [
                s for s in Protobuf.extract(sym_res).symbol
                if str(s.symbolName).upper() == TARGET_SYMBOL_NAME
                and assets.get(s.baseAssetId, "").upper() == "XAU"
                and assets.get(s.quoteAssetId, "").upper() == "USD"
            ]
            if len(candidates) != 1:
                log(f"Expected exactly one verified {TARGET_SYMBOL_NAME}, "
                    f"found {len(candidates)}")
                finish()
                return
            sym = candidates[0]
            state["symbol_id"] = sym.symbolId

            detail_req = Protobuf.get("SymbolByIdReq")
            detail_req.ctidTraderAccountId = state["ctid"]
            detail_req.symbolId.append(sym.symbolId)
            detail_res = yield c.send(detail_req, responseTimeoutInSeconds=15)
            if handle_error(detail_res, "SymbolById"):
                finish()
                return
            detail = Protobuf.extract(detail_res).symbol[0]
            state["digits"] = detail.digits
            log(f"Step: Symbol resolved — PASS (symbolName=XAUUSD "
                f"symbolId={state['symbol_id']} base=XAU quote=USD "
                f"digits={state['digits']} tradingMode={detail.tradingMode})")
        except Exception as e:
            log(f"Symbol resolution — FAIL: {type(e).__name__}: {e}")
            finish()
            return

        # ── Subscribe to spots ───────────────────────────
        log(f"Step: Subscribing to spots (symbolId={state['symbol_id']}, "
            f"subscribeToSpotTimestamp=True) ...")
        try:
            sub_req = Protobuf.get("SubscribeSpotsReq")
            sub_req.ctidTraderAccountId = state["ctid"]
            sub_req.symbolId.append(state["symbol_id"])
            sub_req.subscribeToSpotTimestamp = True
            sub_res = yield c.send(sub_req, responseTimeoutInSeconds=15)
            if handle_error(sub_res, "Subscribe spots"):
                finish()
                return
            if sub_res.payloadType == PT_SUB_SPOTS_RES:
                state["subscribed"] = True
                results["subscription"] = True
                log(f"Step: Subscription — PASS (PROTO_OA_SUBSCRIBE_SPOTS_RES); "
                    f"waiting for ProtoOASpotEvent "
                    f"(target ≥ {MIN_EVENTS} valid, window "
                    f"{OBSERVATION_WINDOW_S}s) ...")
            else:
                log(f"Unexpected payloadType {sub_res.payloadType}")
                finish()
                return
        except Exception as e:
            log(f"Subscribe spots — FAIL: {type(e).__name__}: {e}")
            finish()
            return

        def window_elapsed() -> None:
            """End of observation window (extends once if events are sparse)."""
            if state["finished"] or state["unsub_started"]:
                return
            if not events and not state["window_extended"]:
                state["window_extended"] = True
                log("  No events yet — market may be sparse; extending "
                    f"observation window by {SPARSE_EXTENSION_S}s ...")
                reactor.callLater(SPARSE_EXTENSION_S, window_elapsed)
                return
            finish()

        reactor.callLater(OBSERVATION_WINDOW_S, window_elapsed)

    def on_disconnected(c, reason):
        if state["unsub_started"] and not state["finished"]:
            log("Step: Disconnected — PASS (clean disconnect after unsubscribe)")
            results["clean_disconnect"] = True
            finish()
        elif not state["finished"]:
            log(f"Unexpected disconnect: {reason}")
            finish()

    client = Client(
        EndPoints.PROTOBUF_DEMO_HOST,
        EndPoints.PROTOBUF_PORT,
        TcpProtocol,
        numberOfMessagesToSendPerSecond=5,
    )
    client.setConnectedCallback(on_connected)
    client.setDisconnectedCallback(on_disconnected)
    client.setMessageReceivedCallback(on_message)
    client.startService()

    reactor.callLater(150, finish)  # global safety timeout
    reactor.run()

    return all(results.values())


def main():
    """Main entry point."""
    log("=" * 60)
    log("cTrader Open API Real-Time Spot Stream — Gate 3")
    log("=" * 60)
    log("Loading configuration from .env (credentials NOT printed) ...")
    config = load_env()
    run_spot_stream(config)


if __name__ == "__main__":
    main()
