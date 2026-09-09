#!/usr/bin/env python3
"""cTrader Open API Smoke Test — Gate 1.

Isolated smoke test for cTrader Open API connectivity.
This is a diagnostic tool, NOT part of the production trading pipeline.

Flow:
1. Load configuration from .env
2. Connect to demo.ctraderapi.com:5035
3. Authenticate the application
4. Request account list using access token
5. Discover ctidTraderAccountId
6. Authenticate the selected cTrader account
7. Print safe diagnostic information

Security:
- NEVER prints Client Secret
- NEVER prints Access Token
- NEVER prints Refresh Token
- Only outputs safe diagnostic information
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


def run_smoke_test(config: dict[str, str]) -> bool:
    """Run the cTrader Open API smoke test.

    Args:
        config: Dictionary containing cTrader credentials.

    Returns:
        True if all steps pass, False otherwise.
    """
    from twisted.internet import reactor, defer
    from ctrader_open_api import Client, EndPoints, Protobuf
    from ctrader_open_api.tcpProtocol import TcpProtocol

    # Initialize protobuf message registry
    Protobuf.populate()

    results = {
        "sdk_import": False,
        "connection": False,
        "app_auth": False,
        "account_list": False,
        "account_found": False,
        "ctid_discovered": False,
        "account_auth": False,
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

            app_auth_res = yield c.send(
                app_auth_req,
                responseTimeoutInSeconds=10,
            )

            if app_auth_res.payloadType == 2142:
                # Error response
                error_msg = Protobuf.extract(app_auth_res)
                error_code = getattr(error_msg, "errorCode", "UNKNOWN")
                error_desc = getattr(error_msg, "description", "No description")
                log(f"Step 3: Application authentication — FAIL")
                log(f"  Error code: {error_code}")
                log(f"  Description: {error_desc}")
                log("  LIKELY CAUSE: CTRADER_CLIENT_ID or CTRADER_CLIENT_SECRET is incorrect.")
                log("  ACTION: Verify credentials at https://openapi.ctrader.com")
                cleanup_and_stop(c)
                return

            if app_auth_res.payloadType == 2101:
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

        # ── Step 4: Get Account List ─────────────────────
        log("Step 4: Requesting account list ...")
        try:
            get_accounts_req = Protobuf.get("GetAccountListByAccessTokenReq")
            get_accounts_req.accessToken = config["CTRADER_ACCESS_TOKEN"]

            get_accounts_res = yield c.send(
                get_accounts_req,
                responseTimeoutInSeconds=10,
            )

            if get_accounts_res.payloadType == 2142:
                error_msg = Protobuf.extract(get_accounts_res)
                error_code = getattr(error_msg, "errorCode", "UNKNOWN")
                error_desc = getattr(error_msg, "description", "No description")
                log(f"Step 4: Account list — FAIL")
                log(f"  Error code: {error_code}")
                log(f"  Description: {error_desc}")
                cleanup_and_stop(c)
                return

            accounts = get_accounts_res.ctidTraderAccount
            num_accounts = len(accounts)
            log(f"Step 4: Account list retrieved — PASS (found {num_accounts} account(s))")
            results["account_list"] = True

            # ── Step 5: Find target account ──────────────
            log(f"Step 5: Searching for account login: {account_login} ...")
            target_account = None
            for acc in accounts:
                acc_login = str(acc.traderLogin)
                acc_type = "LIVE" if acc.isLive else "DEMO"
                log(f"  - Found account: login={acc_login}, "
                    f"ctidTraderAccountId={acc.ctidTraderAccountId}, "
                    f"type={acc_type}")
                if acc_login == account_login:
                    target_account = acc

            if target_account is None:
                log(f"Step 5: Account {account_login} NOT FOUND — FAIL")
                log("Available accounts listed above.")
                cleanup_and_stop(c)
                return

            ctid_trader_account_id = target_account.ctidTraderAccountId
            account_type = "LIVE" if target_account.isLive else "DEMO"
            log(f"Step 5: Account found — PASS")
            log(f"  - Selected trading account login: {account_login}")
            log(f"  - Discovered ctidTraderAccountId: {ctid_trader_account_id}")
            log(f"  - Account type/environment: {account_type}")
            results["account_found"] = True
            results["ctid_discovered"] = True

        except Exception as e:
            log(f"Step 4-5: Account list retrieval — FAIL: {type(e).__name__}: {e}")
            cleanup_and_stop(c)
            return

        # ── Step 6: Authenticate Account ─────────────────
        log("Step 6: Authenticating cTrader account ...")
        try:
            account_auth_req = Protobuf.get("AccountAuthReq")
            account_auth_req.ctidTraderAccountId = ctid_trader_account_id
            account_auth_req.accessToken = config["CTRADER_ACCESS_TOKEN"]

            account_auth_res = yield c.send(
                account_auth_req,
                responseTimeoutInSeconds=10,
            )

            if account_auth_res.payloadType == 2142:
                error_msg = Protobuf.extract(account_auth_res)
                error_code = getattr(error_msg, "errorCode", "UNKNOWN")
                error_desc = getattr(error_msg, "description", "No description")
                log(f"Step 6: Account authentication — FAIL")
                log(f"  Error code: {error_code}")
                log(f"  Description: {error_desc}")
                cleanup_and_stop(c)
                return

            if account_auth_res.payloadType == 2103:
                log("Step 6: Account authentication — PASS")
                results["account_auth"] = True
            else:
                log(f"Step 6: Unexpected response type: {account_auth_res.payloadType}")
                cleanup_and_stop(c)
                return

        except Exception as e:
            log(f"Step 6: Account authentication — FAIL: {type(e).__name__}: {e}")
            cleanup_and_stop(c)
            return

        # ── All Steps Complete ───────────────────────────
        all_pass = all(results.values())
        log("=" * 60)
        if all_pass:
            log("GATE 1 STATUS: PASS")
        else:
            log("GATE 1 STATUS: FAIL")
        log("=" * 60)
        log("Safe diagnostic summary:")
        log(f"  SDK import:             {'PASS' if results['sdk_import'] else 'FAIL'}")
        log(f"  Connection:             {'PASS' if results['connection'] else 'FAIL'}")
        log(f"  Application auth:       {'PASS' if results['app_auth'] else 'FAIL'}")
        log(f"  Account list retrieval: {'PASS' if results['account_list'] else 'FAIL'}")
        log(f"  Account {account_login} found: "
            f"{'PASS' if results['account_found'] else 'FAIL'}")
        log(f"  ctidTraderAccountId:    {'PASS' if results['ctid_discovered'] else 'FAIL'}")
        log(f"  Account authentication: {'PASS' if results['account_auth'] else 'FAIL'}")
        log("  Credentials exposed:    NO")
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
    reactor.callLater(45, reactor.stop)
    reactor.run()

    return all(results.values())


def main():
    """Main entry point."""
    log("=" * 60)
    log("cTrader Open API Smoke Test — Gate 1")
    log("=" * 60)

    # Load configuration
    log("Loading configuration from .env ...")
    config = load_env()
    log("Configuration loaded (credentials NOT printed)")

    # Verify .gitignore protects .env
    log("Verifying .gitignore protects .env ...")
    gitignore_path = ".gitignore"
    if os.path.exists(gitignore_path):
        with open(gitignore_path) as f:
            content = f.read()
            if ".env" in content:
                log(".env is protected by .gitignore — OK")
            else:
                log("WARNING: .env may NOT be protected by .gitignore!")
    else:
        log("WARNING: No .gitignore found!")

    # Run smoke test
    success = run_smoke_test(config)

    if not success:
        sys.exit(1)

    log("Smoke test completed successfully.")


if __name__ == "__main__":
    main()
