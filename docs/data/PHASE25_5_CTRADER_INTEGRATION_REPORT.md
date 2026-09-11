# PHASE 25.5 — cTrader Open API Integration Report

**Date:** 2026-09-11 (updated)
**Phase:** 25.5 — Real Broker/API Integration
**Status:** IN PROGRESS — Gate 1 PASS, Gate 2 PASS, Gate 3 PASS, Gate 4 SDK-verified / live run BLOCKED (missing credentials)

---

## 1. Objective

Prove that the XAUUSD trading system can communicate reliably with the IC Markets cTrader DEMO environment and retrieve real market/account information.

---

## 2. Environment

| Item | Value |
|------|-------|
| Python | 3.13 |
| OS | Linux |
| cTrader SDK | ctrader-open-api 0.9.2 |
| Broker | IC Markets (cTrader) |
| Account Type | DEMO |
| Account Login | 10107153 |
| Endpoint | demo.ctraderapi.com:5035 |

---

## 3. cTrader API Configuration

| Variable | Status |
|----------|--------|
| CTRADER_CLIENT_ID | Present in .env |
| CTRADER_CLIENT_SECRET | Present in .env |
| CTRADER_ACCESS_TOKEN | Present in .env |
| CTRADER_ACCOUNT_ID | Present in .env |
| CTRADER_ENV | Present in .env |

All credentials are read from environment variables only. No credentials are stored in source code.

---

## 4. Gate 1 — Connectivity & Account Authentication: PASS

**Files:** `tools/ctrader_smoke_test/smoke_test.py`

**Result (2026-09-11):**

| Step | Result |
|------|--------|
| SDK Import | PASS |
| TLS Connection (demo.ctraderapi.com:5035) | PASS |
| Application Auth (`ProtoOAApplicationAuthReq` → 2101) | PASS |
| Account List (`ProtoOAGetAccountListByAccessTokenReq` → 2150) | PASS (1 account) |
| Target account 10107153 found | PASS (DEMO) |
| Account Auth (`ProtoOAAccountAuthReq` → 2103) | PASS |

**Discovered ctidTraderAccountId:** 48518857 (dynamic discovery from account list; login 10107153 ≠ ctidTraderAccountId). Not hardcoded anywhere in the codebase.

**Root cause of the earlier Gate 1 failure:** `ctrader-open-api` 0.9.2's `Client.send()` resolves with the raw wire envelope (`ProtoMessage`: `payloadType` + `payload` bytes). Typed field access (e.g. `.ctidTraderAccount`) requires parsing the payload first via `Protobuf.extract()`. Fixed in the smoke test; no credentials were involved.

**TLS `service_identity` warning:** fixed by installing `service_identity 23.1.0` + `cryptography 42.0.8` (26.x requires cryptography>=47, incompatible with installed pyopenssl 24.1.0 which requires <43). Full TLS hostname verification is now active.

---

## 5. Gate 2 — XAUUSD Symbol Discovery: PASS

**File:** `tools/ctrader_smoke_test/symbol_discovery.py` (isolated in `tools/ctrader_smoke_test/`; no production changes)

### API methods used (verified against installed SDK descriptors — no guessed field names)

| Step | Request | Response (payloadType) | Relevant fields |
|------|---------|------------------------|-----------------|
| Asset list | `ProtoOAAssetListReq` | `ProtoOAAssetListRes` (2144) | repeated `asset` (`ProtoOAAsset`: assetId, name, displayName, digits) |
| Symbol list | `ProtoOASymbolsListReq` | `ProtoOASymbolsListRes` (2114) | repeated `symbol` (`ProtoOALightSymbol`: symbolId, symbolName, enabled, baseAssetId, quoteAssetId, description) |
| Symbol detail | `ProtoOASymbolByIdReq` | `ProtoOASymbolByIdRes` (2116) | repeated `symbol` (`ProtoOASymbol`: digits, pipPosition, minVolume, maxVolume, stepVolume, lotSize, tradingMode, ...) |

Note: `ProtoOASymbolByIdRes.symbol` is a **repeated** field (descriptor label=3); the first element is the requested symbol.

### Discovery evidence

- Full symbol list scanned: **352 symbols**; broker asset list: **304 assets**
- Symbols whose **name** contains "XAU": 6 (see candidates below)
- Selection rule applied: a candidate counts as XAU/USD **only if** its `baseAssetId`/`quoteAssetId` resolve (via the broker asset list) to assets named `XAU` and `USD` respectively — name match alone is insufficient

### Candidates

| symbolName | symbolId | Base | Quote | Verdict |
|------------|----------|------|-------|---------|
| XAUUSD | 41 | XAU | USD | ✅ Verified XAU/USD |
| XAUEUR | 43 | XAU | EUR | Excluded (gold cross) |
| XAUAUD | 10032 | XAU | AUD | Excluded (gold cross) |
| XAUCHF | 10047 | XAU | CHF | Excluded (gold cross) |
| XAUGBP | 10048 | XAU | GBP | Excluded (gold cross) |
| XAUJPY | 10049 | XAU | JPY | Excluded (gold cross) |

### Selected symbol (unambiguous)

| Property | Value |
|----------|-------|
| symbolName | **XAUUSD** |
| symbolId | **41** |
| Description | "Gold vs US Dollar" |
| Base / Quote asset | XAU / USD (verified via broker asset list) |
| Digits | 2 |
| Pip position | 2 (1 pip = 0.01) |
| Min volume | 100 (in cents-of-lot units; ~1.00 lot) |
| Max volume | 1,000,000 (~10,000 lots) |
| Volume step | 100 (~1.00 lot) |
| Lot size | 10,000 (1 lot = 10,000 units of base → 100 oz) |
| Trading mode | ENABLED (`ProtoOATradingMode.ENABLED`) |
| Enabled | True |

Exactly **one** candidate verified as XAU/USD, enabled, and in `ENABLED` trading mode → no ambiguity; no arbitrary selection was needed.

### Validation evidence

1. `ProtoOALightSymbol` for symbolId 41 reports `symbolName="XAUUSD"`, `enabled=True`, base/quote asset IDs.
2. The broker asset list maps those IDs to assets named exactly `XAU` and `USD`.
3. `ProtoOASymbol` detail for symbolId 41 reports `tradingMode=ENABLED`, `digits=2`, `pipPosition=2`, `lotSize=10000` — consistent with spot gold quoted in USD with 2 decimals.
4. All five other XAU* symbols resolve to non-USD quote assets and were excluded.

### Test result

```
GATE 2 STATUS: PASS
Selected symbol : XAUUSD
symbolId        : 41
Credentials exposed: NO
```

### Limitations

1. Symbol metadata (volumes, lotSize) is broker-reported and subject to change; the pipeline must refresh it rather than hardcode it.
2. symbolId 41 is specific to this IC Markets DEMO broker configuration — other brokers/environments may use different IDs. Per architecture, broker-specific symbol IDs must not enter core code; the existing canonical/provider abstraction maps canonical XAUUSD ↔ broker symbol at the provider layer.
3. Gate 2 covers discovery only: no quotes, bars, orders, or strategy logic were exercised.

---

## 6. Gate 3 — Real-Time Market Data: PASS

**File:** `tools/ctrader_smoke_test/spot_stream.py` (isolated in `tools/ctrader_smoke_test/`; data-only — no orders, no trading, no strategy, no signals, no risk engine)

### 6.1 Authentication

Full Gate 1 chain re-executed live (no hardcoded IDs):
1. Connection to demo.ctraderapi.com:5035 — PASS
2. `ProtoOAApplicationAuthReq` → `PROTO_OA_APPLICATION_AUTH_RES` (2101) — PASS
3. `ProtoOAGetAccountListByAccessTokenReq` → 2150 — PASS (1 account)
4. Dynamic discovery: traderLogin 10107153 → ctidTraderAccountId 48518857 — PASS
5. `ProtoOAAccountAuthReq` → `PROTO_OA_ACCOUNT_AUTH_RES` (2103) — PASS

### 6.2 Subscription request

`ProtoOASubscribeSpotsReq` (fields verified from installed descriptors):
- `ctidTraderAccountId` = 48518857 (discovered dynamically)
- `symbolId` = [41] (re-resolved live from asset+symbol metadata: symbolName=XAUUSD, base=XAU, quote=USD — not hardcoded)
- `subscribeToSpotTimestamp` = True (optional field #4; requests the server event timestamp on each spot event)

### 6.3 Subscription response

`ProtoOASubscribeSpotsRes` — payloadType 2128 (`PROTO_OA_SUBSCRIBE_SPOTS_RES`) — PASS.

### 6.4 Spot event response type

`ProtoOASpotEvent` — payloadType 2131 (`PROTO_OA_SPOT_EVENT`). Descriptor fields used:
`symbolId` (#2), `bid` (#4, optional uint64), `ask` (#5, optional uint64),
`timestamp` (#8, optional int64) — present on every received event because
`subscribeToSpotTimestamp=True` was set.

### 6.5 Price representation

Spotware-documented and verified against descriptors: spot bid/ask are integers
expressed in **1/100000 of a price unit** (same convention as trendbar/tick prices,
per help.ctrader.com/open-api/symbol-data). They are NOT decimal prices.

### 6.6 Price conversion formula

```
price = round(raw / 100000, symbol.digits)
```

For XAUUSD (digits = 2): `price = round(raw / 100000, 2)`
e.g. raw 433900000 → 4339.00.

Implementation note: the tool computes this in **exact decimal arithmetic**
(`Decimal(raw) / Decimal(100000)` then `quantize` with `ROUND_HALF_EVEN`),
avoiding binary-float artifacts (e.g. `4337.5500000000001`) that a naive
`round(raw / 100000.0, 2)` float implementation produces. The Decimal result
matches the documented formula exactly and feeds cleanly into the `RawTick`
contract, which uses `Decimal` prices.

### 6.7 Sample validated events (run 2, exact-decimal conversion)

| # | Bid | Ask | Spread | raw (bid, ask) | event_time (UTC, server) | ingestion (UTC, local) |
|---|-----|-----|--------|----------------|--------------------------|------------------------|
| 1 | 4339.00 | 4339.05 | 0.05 | 433900000, 433905000 | 05:35:43.688 | 05:35:45.509 |
| 2 | 4339.09 | 4339.21 | 0.12 | 433909000, 433921000 | 05:35:44.038 | 05:35:45.567 |
| 5 | 4339.14 | 4339.26 | 0.12 | 433914000, 433926000 | 05:35:45.160 | 05:35:46.741 |
| 10 | 4339.15 | 4339.27 | 0.12 | 433915000, 433927000 | 05:35:47.020 | 05:35:48.548 |

### 6.8 Bid / 6.9 Ask / 6.10 Spread (12 events received, 12 valid, 0 invalid)

| Metric | Verified range |
|--------|----------------|
| Bid | 4339.00 – 4339.39 |
| Ask | 4339.05 – 4339.51 |
| Spread (ask − bid) | 0.05 – 0.12 USD (price units; pipPosition=2 so 0.10 = 10 pips) |

Spread was computed as `ask − bid` on converted prices and cross-checked against
raw integers (`(ask_raw − bid_raw) / 100000`). Spread here is the bid/ask quote
spread only — it is NOT tick volume and NOT institutional flow.

### 6.11 Timestamp semantics

- `ProtoOASpotEvent.timestamp` is the **server-side market data timestamp** in
  Unix epoch **milliseconds** (same representation as all cTrader timestamps,
  e.g. `GetTrendbarsReq.fromTimestamp/toTimestamp`). It is an optional proto2
  field, delivered only when `subscribeToSpotTimestamp=True`.
- `event_time` = SpotEvent.timestamp → tz-aware UTC (`datetime.fromtimestamp(ms/1000, tz=utc)`).
- `ingestion_time` = local UTC receipt time, recorded at push-handler entry —
  never substituted for event_time.
- `availability_time` ≈ `ingestion_time` for a live push stream (cTrader does
  not provide a separate availability marker for spot events; documented as an
  approximation, not invented).
- Event #1 first-delivery note: the first event can arrive immediately after the
  subscribe response with a slightly older server timestamp — it is still a
  real server event_time, ordered correctly relative to other events.

### 6.12 Temporal validation — PASS

- 12/12 valid events carried a server event_time (no invented timestamps).
- event_time ordering: strictly non-decreasing across the sample.
- No future event_time: every event satisfied
  `event_time <= ingestion_time + clock-skew tolerance (5s)` — consistent with
  the project rule `Available_i(t) = 1[AvailabilityTimestamp_i <= t]`
  (no future timestamps introduced).
- Receipt lag (ingestion − event_time): **1525–1821 ms**. This includes broker
  push latency + twisted client queueing (`numberOfMessagesToSendPerSecond=5`)
  and is expected for a demo feed; it is recorded per event, never collapsed
  into event_time.

### 6.13 Data quality validation — PASS

Per-event checks implemented (invalid events are reported, never silently
discarded): symbolId == 41 (only symbolId seen: [41]); bid > 0; ask > 0;
ask >= bid; spread >= 0; timestamp present and positive; tz-aware UTC;
no impossible future timestamps; no malformed prices. Result: **12 received /
12 valid / 0 invalid**. Missing-server-timestamp events would be downgraded to
warnings (usable but incomplete) and counted explicitly.

### 6.14 Subscription lifecycle — PASS

```
CONNECT → APPLICATION AUTH → ACCOUNT LIST → ACCOUNT AUTH → RESOLVE SYMBOL
→ SUBSCRIBE (2128) → RECEIVE 12 × SPOT_EVENT (2131) → UNSUBSCRIBE (2130)
→ CLEAN DISCONNECT
```

`ProtoOAUnsubscribeSpotsReq` → `PROTO_OA_UNSUBSCRIBE_SPOTS_RES` (2130) — PASS.
Disconnect callback fired cleanly after `stopService()` — PASS.

### 6.15 Disconnect behavior

`setDisconnectedCallback` distinguishes a clean post-unsubscribe close from an
unexpected closure (logs reason, finishes with failure instead of crashing).
A global reactor timeout (150s) bounds the run. Production-grade reconnect
logic is intentionally NOT implemented here (out of scope for this gate).

### 6.16 Test results

- Live demo run: **GATE 3 STATUS: PASS** — 12 received / 12 valid / 0 invalid;
  all lifecycle steps PASS; no credentials exposed.
- New unit tests `tests/test_ctrader_spot_stream.py`: **19 passed** —
  credential-free and network-free (pure helpers only: price conversion,
  ms→UTC conversion, data-quality validation, RawTick mapping, summarization).
- Full repository suite: `1038 passed, 16 failed, 1 skipped` — the 16 failures
  are the same pre-existing set as before this gate (unrelated to cTrader).

### 6.17 RawTick contract assessment

The existing `src.canonical.raw.RawTick` (frozen dataclass: `symbol`, `bid`,
`ask`, `timestamp`, `volume`, `provider`, `provider_symbol`, `retrieval_time`)
**represents cTrader spot events without any contract change**. Mapping used:
`symbol="XAUUSD"`, `bid/ask`=converted Decimals, `timestamp`=event_time (server),
`retrieval_time`=ingestion_time, `provider="ctrader"`, `provider_symbol="XAUUSD"`.
`volume` is left None (spot events carry no volume — a documented limitation,
not a contract gap). Events lacking a server timestamp cannot be mapped
(RawTick requires `timestamp`); the helper refuses rather than inventing one.
No CanonicalTick/CanonicalBar was created (per gate instructions).

### 6.18 Limitations

1. Demo feed characteristics: ~1.6–1.8 s receipt lag and throttled delivery;
   production sizing must not assume demo latencies.
2. Spot events carry no tick volume; volume-based features need trendbar/tick
   history (Gate 4) or reconcile data.
3. The 1/100000 scale is the documented universal protocol unit; symbol digits
   only control display rounding. The conversion helper keeps both raw and
   converted values for audit.
4. Spot events may omit bid or ask individually (one-sided quotes); the
   validator flags them explicitly instead of discarding.
5. `availability_time` is approximated by `ingestion_time` for push events;
   a stricter availability marker would need server-side queue metadata,
   which cTrader spot events do not expose.

### 6.19 Final Gate 3 status

```
GATE 3 — Real-Time Market Data: PASS
```

---

## 7. Historical Data Test (Gate 4)

**Status:** IN PROGRESS — SDK structures verified from installed package; unit tests 24/24 PASS; live run BLOCKED (see 7.6)

**File:** `tools/ctrader_smoke_test/historical_data.py` (isolated in `tools/ctrader_smoke_test/`; data-only — no orders, no trading, no strategy, no signals, no risk engine)

### 7.1 SDK inspection failure root cause (resolved)

An earlier inspection attempt imported `ctrader_open_api.messages.OpenApiModelEnums_pb2`, which **does not exist** in ctrader-open-api 0.9.2. Actual package contents (verified by filesystem + `.venv/bin/python`):

```
ctrader_open_api/messages/
├── OpenApiCommonMessages_pb2.py       (ProtoMessage, ProtoErrorRes, ProtoHeartbeatEvent)
├── OpenApiCommonModelMessages_pb2.py  (ProtoOAPayloadType shared model enums live here)
├── OpenApiMessages_pb2.py             (request/response messages incl. GetTrendbarsReq/Res, GetTickDataReq/Res)
├── OpenApiModelMessages_pb2.py        (model messages incl. ProtoOATrendbar + enums incl. ProtoOATrendbarPeriod)
```

There is NO separate `*_Enums_pb2` module; enums are defined inside the two model/message modules. `OpenApiModelMessages_pb2` imports correctly and is used for enums only; requests are built via the SDK factory `Protobuf.get("GetTrendbarsReq")`, which resolves to `ProtoOAGetTrendbarsReq` (in `OpenApiMessages_pb2`).

### 7.2 Trendbar message descriptors (verified from installed SDK 0.9.2)

| Message (module) | # | Field | Type | Label |
|---|---|---|---|---|
| `ProtoOAGetTrendbarsReq` (Messages) | 1 | payloadType | enum ProtoOAPayloadType | optional |
| | 2 | ctidTraderAccountId | int64 | **required** |
| | 3 | fromTimestamp | int64 | **required** (Unix **ms**) |
| | 4 | toTimestamp | int64 | **required** (Unix **ms**) |
| | 5 | period | enum ProtoOATrendbarPeriod | **required** |
| | 6 | symbolId | int64 | **required** |
| | 7 | count | uint32 | optional (max bars returned) |
| `ProtoOAGetTrendbarsRes` (Messages) | 1 | payloadType | enum | optional |
| | 2 | ctidTraderAccountId | int64 | required |
| | 3 | period | enum ProtoOATrendbarPeriod | required (echoed) |
| | 4 | timestamp | int64 | required |
| | 5 | trendbar | message → ProtoOATrendbar | **repeated** |
| | 6 | symbolId | int64 | optional |
| `ProtoOATrendbar` (ModelMessages) | 3 | volume | int64 | **required** (tick volume) |
| | 4 | period | enum ProtoOATrendbarPeriod | optional |
| | 5 | low | int64 | optional (absolute, 1/100000) |
| | 6 | deltaOpen | uint64 | optional |
| | 7 | deltaClose | uint64 | optional |
| | 8 | deltaHigh | uint64 | optional |
| | 9 | utcTimestampInMinutes | uint32 | optional (bar OPEN time, min since Unix epoch UTC) |

Key semantics: `low` is absolute in 1/100000; open/close/high are stored as deltas ABOVE low on the **same 1/100000 scale** (delta 1_000 = +0.01 on a 2-digit symbol). Reconstruction formula: `price = round((low + delta) / 100000, digits)` in exact Decimal arithmetic.

### 7.3 Period enum + payload types (verified)

- `ProtoOATrendbarPeriod`: M1=1, M2=2, M3=3, M4=4, **M5=5**, M10=6, **M15=7**, M30=8, **H1=9**, **H4=10**, H12=11, **D1=12**, W1=13, MN1=14
- Payload types: `PROTO_OA_GET_TRENDBARS_REQ`=**2137**, `PROTO_OA_GET_TRENDBARS_RES`=**2138**, `PROTO_OA_ERROR_RES`=**2142**

### 7.4 Tick-data messages (verified, NOT implemented — deferred)

`ProtoOAGetTickDataReq` (#2 ctidTraderAccountId, #3 symbolId, #4 `type` enum `ProtoOAQuoteType`, #5/#6 from/to ms) → `ProtoOAGetTickDataRes` (#3 `tickData` repeated → `ProtoOATickData`, #4 `hasMore` bool). There is **no `ProtoOATick` message** in SDK 0.9.2. Tick history is NOT implemented (per gate instructions).

### 7.5 Verification performed (no live connection)

- Full code path exercised offline against SDK 0.9.2 with `.venv/bin/python`: import, enum `Value()` lookups, `Protobuf.get("GetTrendbarsReq")` construction, serialization, `ProtoMessage` wire-envelope round-trip, `Protobuf.extract` — all OK.
- Unit tests `tests/test_ctrader_historical_data.py`: **24 passed** — credential-free, network-free. Two fixture corrections were required (delta scale 1/100000, D1 weekend-gap arithmetic); helper logic itself was already correct.
- `tools/ctrader_smoke_test/historical_data.py`: docstring-only corrections (Res field numbers: period #3, ctid #2; module placement). **No functional changes needed.**

### 7.6 Live run BLOCKED — credentials absent from environment

The live Gate 4 run (`M5 ≈100 bars` first, then M15/H1/H4/D1, 0.7 s spacing ≤ 5 req/s) was attempted and stopped at configuration load:

```
ERROR: Missing environment variables: CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET,
       CTRADER_ACCESS_TOKEN, CTRADER_ACCOUNT_ID, CTRADER_ENV
```

Environment facts (names inspected only; values never read or printed):
- `.env` (project root, mode 600) was modified on 2026-09-11 and now defines only MT-*/SYMBOL/TIMEFRAME/MODE keys — **no `CTRADER_*` keys remain**.
- No `CTRADER_*` variables are exported in the shell; no other `.env*` file exists in the repo.
- Per gate instructions, credentials were NOT changed, regenerated, moved, or recovered. The tool correctly refused to run and exposed nothing.

**Unblock action (user):** restore the five `CTRADER_*` variables to `.env` (same values used for Gates 1–3), then re-run `.venv/bin/python tools/ctrader_smoke_test/historical_data.py` from the project root. No code changes are required.

---

## 8. Pipeline Test (Gate 5)

**Status:** NOT REACHED

---

## 9. Test Results (current)

| Step | Result | Details |
|------|--------|---------|
| SDK Import | PASS | `ctrader-open-api` 0.9.2 imported successfully |
| TLS Connection | PASS | demo.ctraderapi.com:5035 |
| Application Auth | PASS | payloadType 2101 |
| Account List | PASS | payloadType 2150, 1 account |
| Account Found (10107153) | PASS | DEMO |
| Account Auth | PASS | payloadType 2103 |
| Asset List | PASS | 304 assets |
| Symbol List | PASS | 352 symbols |
| XAU/USD verification | PASS | 1 verified candidate (XAUUSD, symbolId 41) |
| Spot subscription (Gate 3) | PASS | `ProtoOASubscribeSpotsRes` 2128 |
| Spot events received | PASS | 12 × `ProtoOASpotEvent` 2131, 12 valid / 0 invalid |
| Temporal validation | PASS | ordered, no future timestamps, 1.5–1.8 s receipt lag |
| Unsubscribe + clean disconnect | PASS | 2130 + clean close |

**Overall:** 12 passed, 0 failed (gates 1–3). Gates 4–5 not reached.

**Unit tests added (Gate 3):** `tests/test_ctrader_spot_stream.py` — 19 passed,
credential-free, network-free.

**Repository test suite:** `1038 passed, 16 failed, 1 skipped`. The 16 failures
are pre-existing and unrelated to cTrader (dependency-harmonization checks,
file-permission mocks, `utcnow` deprecation checks, risk-manager API drift).
No credentials appear in any test.

---

## 10. Security Considerations

- ✅ No credentials were printed in output
- ✅ No credentials were stored in source code
- ✅ `.env` is protected by `.gitignore`
- ✅ Smoke test and discovery tool output only safe diagnostic information
- ✅ Account login (10107153) and ctidTraderAccountId (48518857) are not secrets
- ✅ No credentials in unit tests

---

## 11. Known Limitations (SDK)

1. `ctrader-open-api` SDK (v0.9.2) uses Twisted for async networking
2. `Client.send()` returns the raw wire envelope; `Protobuf.extract()` must be called before typed field access (several responses carry repeated fields, e.g. `ProtoOASymbolByIdRes.symbol`)
3. `service_identity` must be pinned compatible with the installed `pyopenssl`/`cryptography` stack
4. `clientId` field is a string type (not integer) in the protobuf definition

---

## 12. Blockers

Gate 4 live run: the five `CTRADER_*` environment variables are no longer present
(`.env` was modified on 2026-09-11 and now contains only MT-*/SYMBOL/TIMEFRAME/MODE
keys). Credentials must be restored by the user; per instructions none were changed,
regenerated, or recovered. See section 7.6.

---

## 13. Final Status

```
PHASE 25.5 STATUS: IN PROGRESS

GATES:
Gate 1 — cTrader connectivity/account authentication: PASS
Gate 2 — XAUUSD symbol discovery:                     PASS
Gate 3 — Real-time market data:                       PASS
Gate 4 — Historical bars:                             SDK-VERIFIED / live run BLOCKED (missing CTRADER_* credentials)
Gate 5 — Existing pipeline integration:               NOT REACHED

FILES CREATED:
- tools/ctrader_smoke_test/smoke_test.py          (Gate 1; fixed envelope parsing)
- tools/ctrader_smoke_test/symbol_discovery.py    (Gate 2)
- tools/ctrader_smoke_test/spot_stream.py         (Gate 3)
- tools/ctrader_smoke_test/historical_data.py     (Gate 4; SDK-verified)
- tests/test_ctrader_spot_stream.py               (Gate 3 unit tests, credential-free)
- tests/test_ctrader_historical_data.py           (Gate 4 unit tests, credential-free)
- tools/ctrader_smoke_test/README.md
- docs/data/PHASE25_5_CTRADER_INTEGRATION_REPORT.md

FILES MODIFIED (production):
- (none) — all work isolated in tools/ctrader_smoke_test/ and tests/

SECURITY:
Confirmed that no credentials were printed or committed.

ARCHITECTURAL CHANGES:
- None. RawTick contract used UNCHANGED for spot-event representation; RawBar
  contract used UNCHANGED for trendbar representation (Gate 4 mapping verified
  by unit tests).
- Broker symbolId 41 is NOT hardcoded into core code; Gates 3–4 re-resolve the
  symbol from asset+symbol metadata at runtime. Mapping belongs in the
  existing canonical/provider abstraction when Gate 5 integration begins.

NEXT APPROVED STEP:
Gate 4 live run (user restores CTRADER_* env vars first):
  .venv/bin/python tools/ctrader_smoke_test/historical_data.py
Order: M5 ~100 bars first, then M15, H1, H4, D1. Sequential requests paced at
0.7 s (≤ 5 req/s historical limit). No code changes required — SDK structures
were verified against installed 0.9.2 descriptors (section 7).
```
