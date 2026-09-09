# cTrader Open API Smoke Test

Isolated smoke test for cTrader Open API connectivity.

This is a diagnostic tool, NOT part of the production trading pipeline.

## Usage

```bash
.venv/bin/python tools/ctrader_smoke_test/smoke_test.py
```

## Requirements

- `.env` file with cTrader credentials
- `ctrader-open-api` SDK installed
- Network access to `demo.ctraderapi.com:5035`

## Security

- NEVER prints credentials
- NEVER prints secrets
- Only outputs safe diagnostic information
