#!/usr/bin/env python3
"""cTrader Open API Symbol Discovery — Gate 2.

Isolated discovery tool for the XAUUSD/gold trading symbol exposed by the
authenticated IC Markets cTrader DEMO account.
This is a diagnostic tool, NOT part of the production trading pipeline.

Flow:
1. Load configuration from .env
2. Connect to demo.ctraderapi.com:5035
3. Authenticate the application
4. Request account list and dynamically discover ctidTraderAccountId
   (no hardcoded IDs — discovered from the live account list)
5. Authenticate the selected cTrader account
6. Retrieve the broker asset list (to verify base/quote assets by name)
7. Retrieve the full symbol list for the account
8. Filter gold candidates and fetch full symbol metadata (SymbolById)
9. Verify candidates represent XAU/USD and report a verdict

Selection rules:
- Exactly one verified, enabled, tradable XAU/USD instrument -> PASS
- Multiple possible XAU/USD instruments -> PARTIAL (all candidates reported,
  differences explained; no arbitrary choice)
- No XAU/USD instrument -> BLOCKED

Security:
- NEVER prints Client Secret
- NEVER prints Access Token
- NEVER prints Refresh Token
- Only outputs safe diagnostic information

SDK notes (ctrader-open-api 0.9.2, verified from installed descriptors):
- Client.send() resolves with the raw wire envelope (ProtoMessage with
  payloadType + payload bytes). Typed field access requires Protobuf.extract().
- ProtoOASymbolsListRes.symbol is repeated ProtoOALightSymbol:
  symbolId, symbolName, enabled, baseAssetId, quoteAssetId, description
- ProtoOASymbolByIdRes.symbol is ProtoOASymbol:
  digits, pipPosition, minVolume, maxVolume, stepVolume, tradingMode, lotSize...
- ProtoOAAssetListRes.asset is repeated ProtoOAAsset: assetId, name, displayName
- ProtoOATradingMode: ENABLED=0, DISABLED_WITHOUT_PENDINGS_EXECUTION=1,
  DISABLED_WITH_PENDINGS_EXECUTION=2, CLOSE_ONLY_MODE=3
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv


def log(msg: str) -> None:
    """Print timestamped log message."""
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def load_env() -> dict[str, str]:
    """Load cTrader credentials from .env file.

    Returns dict with credential values.
    NEVER prints the values.
    """
    load_dotenv()

    required_vars = [
        "CTRADER_CLIENT_ID",
        "CTRADER_CLIENT_SECRET",
        "CTRADER_ACCESS_TOKEN",
        "CTRADER_ACCOUNT_ID",
        "CTRADER_ENV",
    ]

    config = {}
    missing = []

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            config[var] = value

    if missing:
        log(f"ERROR: Missing environment variables: {', '.join(missing)}")
        log("Please set these in your .env file.")
        sys.exit(1)

    return config


def run_symbol_discovery(config: dict[str, str]) -> bool:
    """Run the Gate 2 symbol discovery.

    Args:
        config: Dictionary containing cTrader credentials.

    Returns:
        True if Gate 2 passes, False otherwise.
    """
    from twisted.internet import reactor, defer
    from ctrader_open_api import Client, EndPoints, Protobuf
    from ctrader_open_api.tcpProtocol import TcpProtocol
    from ctrader_open_api.messages import OpenApiModelMessages_pb2 as _oa_model

    # Payload types (verified against installed SDK's ProtoOAPayloadType enum)
    PT_APP_AUTH_RES = _oa_model.ProtoOAPayloadType.Value("PROTO_OA_APPLICATION_AUTH_RES")
    PT_ACCOUNT_AUTH_RES = _oa_model.ProtoOAPayloadType.Value("PROTO_OA_ACCOUNT_AUTH_RES")
    PT_ERROR_RES = _oa_model.ProtoOAPayloadType.Value("PROTO_OA_ERROR_RES")
    PT_ASSET_LIST_RES = _oa_model.ProtoOAPayloadType.Value("PROTO_OA_ASSET_LIST_RES")
    PT_SYMBOLS_LIST_RES = _oa_model.ProtoOAPayloadType.Value("PROTO_OA_SYMBOLS_LIST_RES")
    PT_SYMBOL_BY_ID_RES = _oa_model.ProtoOAPayloadType.Value("PROTO_OA_SYMBOL_BY_ID_RES")

    trading_mode_names = {
        0: "ENABLED",
        1: "DISABLED_WITHOUT_PENDINGS_EXECUTION",
        2: "DISABLED_WITH_PENDINGS_EXECUTION",
        3: "CLOSE_ONLY_MODE",
    }

    results = {
        "sdk_import": False,
        "connection": False,
        "app_auth": False,
        "account_list": False,
        "ctid_discovered": False,
        "account_auth": False,
        "asset_list": False,
        "symbols_list": False,
        "symbol_details": False,
        "xauusd_unambiguous": False,
    }

    account_login = config["CTRADER_ACCOUNT_ID"]

    # ── Step 1: SDK Import ──────────────────────────────
    log("Step 1: SDK import — PASS")
    results["sdk_import"] = True

    # ── Step 2: Connect to demo endpoint ─────────────────
    log(f"Step 2: Connecting to {EndPoints.PROTOBUF_DEMO_HOST}:{EndPoints.PROTOBUF_PORT} ...")

    client = Client(
        EndPoints.PROTOBUF_DEMO_HOST,
        EndPoints.PROTOBUF_PORT,
        TcpProtocol,
        numberOfMessagesToSendPerSecond=5,
    )

    def handle_error(res: object, step: str) -> bool:
        """Log an error envelope for a step. Returns True if it was an error."""
        if res.payloadType == PT_ERROR_RES:  # type: ignore[attr-defined]
            error_msg = Protobuf.extract(res)
            error_code = getattr(error_msg, "errorCode", "UNKNOWN")
            error_desc = getattr(error_msg, "description", "No description")
            log(f"{step} — FAIL")
            log(f"  Error code: {error_code}")
            log(f"  Description: {error_desc}")
            return True
        return False

    @defer.inlineCallbacks
    def on_connected(c):
        """Called when connection is established."""
        log("Step 2: Connection — PASS")
        results["connection"] = True

        # ── Step 3: Application Authentication ──────────
        log("Step 3: Sending application authentication ...")
        try:
            app_auth_req = Protobuf.get("ApplicationAuthReq")
            app_auth_req.clientId = config["CTRADER_CLIENT_ID"]
            app_auth_req.clientSecret = config["CTRADER_CLIENT_SECRET"]

            app_auth_res = yield c.send(app_auth_req, responseTimeoutInSeconds=15)

            if handle_error(app_auth_res, "Step 3: Application authentication"):
                cleanup_and_stop(c)
                return

            if app_auth_res.payloadType == PT_APP_AUTH_RES:
                log("Step 3: Application authentication — PASS")
                results["app_auth"] = True
            else:
                log(f"Step 3: Unexpected response type: {app_auth_res.payloadType}")
                cleanup_and_stop(c)
                return

        except Exception as e:
            log(f"Step 3: Application authentication — FAIL: {type(e).__name__}: {e}")
            cleanup_and_stop(c)
            return

        # ── Step 4: Account List (dynamic ctid discovery) ─
        log("Step 4: Requesting account list ...")
        try:
            get_accounts_req = Protobuf.get("GetAccountListByAccessTokenReq")
            get_accounts_req.accessToken = config["CTRADER_ACCESS_TOKEN"]

            get_accounts_res = yield c.send(get_accounts_req, responseTimeoutInSeconds=15)

            if handle_error(get_accounts_res, "Step 4: Account list retrieval"):
                cleanup_and_stop(c)
                return

            account_list_res = Protobuf.extract(get_accounts_res)
            accounts = account_list_res.ctidTraderAccount
            log(f"Step 4: Account list retrieved — PASS (found {len(accounts)} account(s))")
            results["account_list"] = True

            target_account = None
            for acc in accounts:
                acc_login = str(acc.traderLogin)
                acc_type = "LIVE" if acc.isLive else "DEMO"
                log(f"  - Found account: login={acc_login}, "
                    f"ctidTraderAccountId={acc.ctidTraderAccountId}, type={acc_type}")
                if acc_login == account_login:
                    target_account = acc

            if target_account is None:
                log(f"Step 4: Account login {account_login} NOT FOUND — FAIL")
                cleanup_and_stop(c)
                return

            ctid_trader_account_id = target_account.ctidTraderAccountId
            log(f"Step 4: Discovered ctidTraderAccountId: {ctid_trader_account_id} "
                f"(dynamic discovery, not hardcoded)")
            results["ctid_discovered"] = True

        except Exception as e:
            log(f"Step 4: Account list retrieval — FAIL: {type(e).__name__}: {e}")
            cleanup_and_stop(c)
            return

        # ── Step 5: Authenticate Account ─────────────────
        log("Step 5: Authenticating cTrader account ...")
        try:
            account_auth_req = Protobuf.get("AccountAuthReq")
            account_auth_req.ctidTraderAccountId = ctid_trader_account_id
            account_auth_req.accessToken = config["CTRADER_ACCESS_TOKEN"]

            account_auth_res = yield c.send(account_auth_req, responseTimeoutInSeconds=15)

            if handle_error(account_auth_res, "Step 5: Account authentication"):
                cleanup_and_stop(c)
                return

            if account_auth_res.payloadType == PT_ACCOUNT_AUTH_RES:
                log("Step 5: Account authentication — PASS")
                results["account_auth"] = True
            else:
                log(f"Step 5: Unexpected response type: {account_auth_res.payloadType}")
                cleanup_and_stop(c)
                return

        except Exception as e:
            log(f"Step 5: Account authentication — FAIL: {type(e).__name__}: {e}")
            cleanup_and_stop(c)
            return

        # ── Step 6: Asset List (for base/quote verification) ─
        log("Step 6: Requesting broker asset list ...")
        assets: dict[int, object] = {}
        try:
            asset_req = Protobuf.get("AssetListReq")
            asset_req.ctidTraderAccountId = ctid_trader_account_id

            asset_res = yield c.send(asset_req, responseTimeoutInSeconds=30)

            if handle_error(asset_res, "Step 6: Asset list retrieval"):
                cleanup_and_stop(c)
                return

            if asset_res.payloadType == PT_ASSET_LIST_RES:
                asset_list_res = Protobuf.extract(asset_res)
                for a in asset_list_res.asset:
                    assets[a.assetId] = a
                log(f"Step 6: Asset list retrieved — PASS ({len(assets)} assets)")
                results["asset_list"] = True
            else:
                log(f"Step 6: Unexpected response type: {asset_res.payloadType} (continuing)")

        except Exception as e:
            log(f"Step 6: Asset list retrieval — FAIL (non-fatal): {type(e).__name__}: {e}")

        def asset_name(asset_id: int) -> str:
            a = assets.get(asset_id)
            if a is None:
                return f"?{asset_id}"
            return str(a.name)

        # ── Step 7: Symbols List ─────────────────────────
        log("Step 7: Requesting symbol list ...")
        symbols = []
        try:
            symbols_req = Protobuf.get("SymbolsListReq")
            symbols_req.ctidTraderAccountId = ctid_trader_account_id

            symbols_res = yield c.send(symbols_req, responseTimeoutInSeconds=30)

            if handle_error(symbols_res, "Step 7: Symbol list retrieval"):
                cleanup_and_stop(c)
                return

            if symbols_res.payloadType == PT_SYMBOLS_LIST_RES:
                symbols_list_res = Protobuf.extract(symbols_res)
                symbols = list(symbols_list_res.symbol)
                log(f"Step 7: Symbol list retrieved — PASS ({len(symbols)} symbols)")
                results["symbols_list"] = True
            else:
                log(f"Step 7: Unexpected response type: {symbols_res.payloadType}")
                cleanup_and_stop(c)
                return

        except Exception as e:
            log(f"Step 7: Symbol list retrieval — FAIL: {type(e).__name__}: {e}")
            cleanup_and_stop(c)
            return

        # ── Step 8: Filter gold candidates by metadata ───
        log("Step 8: Filtering gold/XAU candidates by symbol metadata ...")
        candidates = [s for s in symbols if "XAU" in str(s.symbolName).upper()]

        if not candidates:
            log("Step 8: No symbol name containing 'XAU' found in the full list.")
            log("  Broker may expose gold under a different name; searching "
                "base-asset metadata for XAU ...")
            candidates = [s for s in symbols if asset_name(s.baseAssetId).upper() == "XAU"]

        verified = []  # light symbols confirmed base=XAU, quote=USD
        unverified = []

        for s in candidates:
            base = asset_name(s.baseAssetId).upper()
            quote = asset_name(s.quoteAssetId).upper()
            entry = {
                "symbolId": s.symbolId,
                "symbolName": str(s.symbolName),
                "description": str(s.description),
                "enabled": bool(s.enabled),
                "base": base,
                "quote": quote,
            }
            if base == "XAU" and quote == "USD":
                verified.append(entry)
                log(f"  Candidate (XAU/USD verified by assets): {entry['symbolName']} "
                    f"symbolId={entry['symbolId']} base={base} quote={quote} "
                    f"enabled={entry['enabled']}")
            else:
                unverified.append(entry)
                log(f"  Candidate (name-only match, assets base={base} quote={quote}): "
                    f"{entry['symbolName']} symbolId={entry['symbolId']}")

        if not verified:
            log("Step 8: No candidate verified as XAU/USD by asset metadata.")

        # ── Step 9: Full metadata for verified candidates ─
        log("Step 9: Fetching full symbol metadata for verified candidates ...")
        full_symbols = []
        try:
            for entry in verified:
                req = Protobuf.get("SymbolByIdReq")
                req.ctidTraderAccountId = ctid_trader_account_id
                req.symbolId.append(entry["symbolId"])

                res = yield c.send(req, responseTimeoutInSeconds=15)

                if handle_error(res, f"Step 9: SymbolById({entry['symbolId']})"):
                    continue

                if res.payloadType != PT_SYMBOL_BY_ID_RES:
                    log(f"  SymbolById({entry['symbolId']}): unexpected payloadType "
                        f"{res.payloadType}")
                    continue

                detail_res = Protobuf.extract(res)
                # ProtoOASymbolByIdRes.symbol is a REPEATED ProtoOASymbol
                # (descriptor label=3) — take the first element.
                if len(detail_res.symbol) < 1:
                    log(f"  SymbolById({entry['symbolId']}): empty symbol list in response")
                    continue
                detail = detail_res.symbol[0]
                mode = trading_mode_names.get(detail.tradingMode, str(detail.tradingMode))
                entry.update({
                    "digits": detail.digits,
                    "pipPosition": detail.pipPosition,
                    "minVolume": detail.minVolume,
                    "maxVolume": detail.maxVolume,
                    "stepVolume": detail.stepVolume,
                    "lotSize": detail.lotSize,
                    "tradingMode": mode,
                })
                full_symbols.append(entry)
                results["symbol_details"] = True

                log(f"  --- {entry['symbolName']} (symbolId={entry['symbolId']}) ---")
                log(f"      description : {entry['description']}")
                log(f"      base/quote  : {entry['base']} / {entry['quote']}")
                log(f"      digits      : {entry['digits']}")
                log(f"      pipPosition : {entry['pipPosition']}")
                log(f"      minVolume   : {entry['minVolume']} "
                    f"(~{entry['minVolume'] / 100.0:.4f} units)")
                log(f"      maxVolume   : {entry['maxVolume']} "
                    f"(~{entry['maxVolume'] / 100.0:.2f} units)")
                log(f"      stepVolume  : {entry['stepVolume']} "
                    f"(~{entry['stepVolume'] / 100.0:.4f} units)")
                log(f"      lotSize     : {entry['lotSize']}")
                log(f"      tradingMode : {entry['tradingMode']}")
                log(f"      enabled     : {entry['enabled']}")

        except Exception as e:
            log(f"Step 9: Symbol details — FAIL: {type(e).__name__}: {e}")

        tradable_verified = [e for e in full_symbols
                             if e["tradingMode"] == "ENABLED" and e["enabled"]]

        # ── Verdict ──────────────────────────────────────
        log("=" * 60)
        if len(tradable_verified) == 1:
            sel = tradable_verified[0]
            results["xauusd_unambiguous"] = True
            log("GATE 2 STATUS: PASS")
            log(f"Selected symbol : {sel['symbolName']}")
            log(f"symbolId        : {sel['symbolId']}")
            log("Evidence        : base asset XAU, quote asset USD (verified via "
                "broker asset list), symbol enabled, tradingMode ENABLED, "
                "exactly one verified candidate.")
        elif len(tradable_verified) > 1:
            log("GATE 2 STATUS: PARTIAL")
            log(f"{len(tradable_verified)} verified XAU/USD candidates found; "
                "no arbitrary selection. Differences:")
            for e in tradable_verified:
                log(f"  - {e['symbolName']} symbolId={e['symbolId']} "
                    f"desc={e['description']!r} digits={e['digits']} "
                    f"min={e['minVolume']} max={e['maxVolume']}")
            log("Manual confirmation required to select the instrument.")
        elif len(full_symbols) > 0:
            log("GATE 2 STATUS: PARTIAL")
            log("XAU/USD candidates exist but none is currently enabled/ENABLED "
                "for trading.")
            for e in full_symbols:
                log(f"  - {e['symbolName']} symbolId={e['symbolId']} "
                    f"enabled={e['enabled']} tradingMode={e['tradingMode']}")
        else:
            log("GATE 2 STATUS: BLOCKED")
            log("No XAU/USD instrument found for this account.")
            if unverified:
                log("Name-only candidates (NOT verified as XAU/USD):")
                for e in unverified:
                    log(f"  - {e['symbolName']} symbolId={e['symbolId']} "
                        f"base={e['base']} quote={e['quote']}")
            log("Do not substitute another gold instrument without explicit approval.")
        log("=" * 60)

        log("Safe diagnostic summary:")
        for k, v in results.items():
            log(f"  {k:24s}: {'PASS' if v else 'FAIL'}")
        log(f"  symbols scanned          : {len(symbols)}")
        log(f"  gold candidates (name)   : {len(candidates)}")
        log(f"  verified XAU/USD         : {len(verified)}")
        log(f"  tradable verified        : {len(tradable_verified)}")
        log("  Credentials exposed      : NO")
        log("=" * 60)

        cleanup_and_stop(c)

    def cleanup_and_stop(c):
        """Stop the client and reactor."""
        try:
            c.stopService()
        except Exception:
            pass
        try:
            reactor.stop()
        except Exception:
            pass

    # Set callbacks
    client.setConnectedCallback(on_connected)

    # Start the client
    client.startService()

    # Run the reactor with a global timeout
    reactor.callLater(90, reactor.stop)
    reactor.run()

    return results["xauusd_unambiguous"]


def main():
    """Main entry point."""
    log("=" * 60)
    log("cTrader Open API Symbol Discovery — Gate 2")
    log("=" * 60)

    # Load configuration
    log("Loading configuration from .env ...")
    config = load_env()
    log("Configuration loaded (credentials NOT printed)")

    success = run_symbol_discovery(config)

    if not success:
        sys.exit(1)

    log("Symbol discovery completed successfully.")


if __name__ == "__main__":
    main()
