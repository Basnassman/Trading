# Phase 3C Report — Finish Reproducible Build

- Date: 2026-09-14
- Basis: user directive "Phase 3C: Finish Reproducible Build" (items 1–11), executed after explicit approval of an extended scope: declaring the 12 runtime packages that `src/` imports directly but that were missing from `pyproject.toml` (they would otherwise have made `uv sync` + CI tests fail).
- All Phase 3B fixes kept. No trading logic changed, no `src/` file touched (verified: `git diff --stat -- src/` is empty). No `.env` read, no cTrader/MT5 connections, no files deleted, no destructive Git commands, no `uv lock --upgrade`.

## 1. Prescribed items 1–11 — status

| # | Requirement | Status |
|---|---|---|
| 1 | `requires-python = ">=3.12,<3.13"` | Already present (3B); confirmed; `uv.lock` records `requires-python = "==3.12.*"` |
| 2 | `ctrader-open-api==0.9.2` | Already present (3B); confirmed in `[project.optional-dependencies].ctrader` |
| 3 | Twisted: direct import → declared, locked | `from twisted.internet import ...` confirmed in all 5 files of `tools/ctrader_smoke_test/`; declared in `ctrader` extra; locked in `uv.lock` as `twisted==24.3.0` (SDK's own tested pin) |
| 4 | `playwright` → `dev` only | Already present (3B); confirmed in `[dependency-groups].dev`; no optional runtime extra |
| 5 | `MetaTrader5` in documented `legacy-mt5` extra, never core | Already present (3B); extra documented "Never add to core"; `metaapi-cloud-sdk==29.1.1` added to the same extra (both imports in `src/trading/mt5_connector.py` are guarded) |
| 6 | requirements files not a new build source, not deleted | Untouched on disk; Docker/CI no longer consume them |
| 7 | Lockfile from project root | `uv lock` run at project root (Linux sandbox equivalent of the prescribed Windows PowerShell `& 'C:\ProgramData\uv\uv.exe' lock` — see §7); `uv.lock` created (v1/revision 3, 137 packages) |
| 8 | First sync without MT5 legacy | `uv sync --group dev --extra ctrader --extra research` succeeded; `research` is a valid extra in the final config; no MT5/MetaAPI installed (verified absent from `.venv`) |
| 9 | CI → Python 3.12 + uv + `uv sync` from lock, no ad-hoc installs | `ci.yml` and `migration-safety.yml` already uv/3.12 (kept); `pre-deploy-validation.yml` and `release.yml` converted from pip/3.11 to uv/3.12; all `pip install ...` and `pip-audit -r requirements*.txt` steps removed; all script/tool invocations go through `uv run` |
| 10 | Docker → 3.12, copy lock, uv install, no sed, requirements-docker not a path | Dockerfile rewritten: `python:3.12-slim`, `COPY pyproject.toml uv.lock`, `uv sync --locked` (no dev group in image), `sed` torch block deleted entirely, `requirements-docker.txt` no longer referenced |
| 11 | Verification battery | Executed; results in §5 |

## 2. Deviations within the approved scope (declared for transparency)

1. **12 missing core dependencies added** (user-approved "Full" option): `pydantic==2.13.5`, `pydantic-settings==2.15.0`, `rich==13.9.4`, `jinja2==3.1.6`, `fastapi==0.141.1`, `psutil==7.2.2`, `prometheus-client==0.26.0`, `redis==8.1.0`, `python-telegram-bot==22.8`, `joblib==1.6.0`, `nest-asyncio==1.6.0`, `optuna==4.9.0` — all directly imported by `src/`/`main.py` at runtime; pins match `requirements-ci.txt`/`requirements-docker.txt`. Without them the locked env could not run the app or the tests.
2. **`build-backend` typo fix**: `setuptools.backends._legacy:_Backend` (nonexistent module) → `setuptools.build_meta`. First `uv sync` failed on this (`ModuleNotFoundError: No module named 'setuptools.backends'`); without the fix no locked build is possible.
3. **New documented extras**: `ta-lib = ["TA-Lib==0.7.1"]` (C library note included) and `service-identity` added to `ctrader` after the SDK emitted a TLS-hostname-verification warning without it.
4. **`requirements-ci.txt` gap items from Phase 3B remain as-is** (files intentionally untouched).

## 3. pyproject.toml — final dependency topology

- **core**: data layer + the 12 runtime packages above.
- **extras**: `ctrader` (`ctrader-open-api==0.9.2`, `Twisted`, `service-identity`), `research` (CPU torch via `[tool.uv]` pytorch-cpu index + SB3/gymnasium/scipy/sklearn pins), `legacy-mt5` (Windows-only `MetaTrader5` + `metaapi-cloud-sdk==29.1.1`; documented "never add to core"), `ta-lib` (`TA-Lib==0.7.1`).
- **group `dev`**: pytest stack, ruff, mypy, playwright, pip-audit, pip-licenses (test/CI tooling only).
- MT5/MetaAPI are **not** in the default sync path.

## 4. uv.lock

- Generated with `uv lock` (no `--upgrade`), then re-locked after the `service-identity` addition.
- `uv lock --check` → **OK** (pyproject and lock in sync).
- 137 packages resolved; `requires-python = "==3.12.*"`; resolution markers include `sys_platform == 'win32'` for the MT5 extra (never synced here).
- Locked tool versions used for verification: `ruff==0.16.7`, `mypy==2.3.1`, `pytest==9.1.1`.

## 5. Verification results (item 11)

Environment note: this session runs on a Linux sandbox; the prescribed PowerShell verification commands were executed via their exact Linux equivalents (same tools, same flags, same project root). `uv` 0.12.13.

| Check | Command (Linux equivalent) | Result |
|---|---|---|
| Python 3.12 | `.venv/bin/python --version` | **Python 3.12.14** |
| cTrader SDK import | `.venv/bin/python -c "import ctrader_open_api; ..."` | **OK — "cTrader SDK import OK"**, no `service_identity` warning (verified with warnings-as-errors) |
| Ruff check | `uv run ruff check src main.py` | **823 pre-existing violations** (UP045 131, UP006 36, UP037 30, UP042 27, F401 24, UP017 21, N806 20, I001 13, …); 487 auto-fixable. Not fixed in this phase (would be a mass `src/` edit) |
| Ruff format check | `uv run ruff format --check src main.py` | **34 files** would be reformatted (pre-existing). Not fixed in this phase |
| Bootstrap | `python main.py --show-config` (CI parity env vars) | **Exit 0**, config renders |
| Core module imports | config / health / monitor / feature_engineering / mt5_connector | **All OK** (talib + mt5 + metaapi guards fall back cleanly) |
| Test suite | `pytest tests/` (CI parity env vars) | **1113 passed, 16 failed, 1 skipped** in 103 s — see attribution below |
| Lock integrity | `uv lock --check` | **OK** |
| Sync idempotency | re-run `uv sync` | **"Checked 112 packages"** — no changes |
| pip-audit (locked env) | `uv run pip-audit` | **17 advisories in 5 transitive packages** — see §8 |
| Docker build | `docker build --platform linux/amd64` | **Success** (exit 0) |
| Docker runtime | healthcheck import; torch/talib/ctrader inside image | **"healthy"**; `torch 2.14.0+cpu` (CUDA False, no sed involved); `talib.SMA(...)` functional against C lib 0.6.4; `ctrader_open_api` imports clean |
| Workflow YAML | parsed all 4 touched/kept workflows | **All valid** (a latent unquoted-`name:` YAML error at release.yml line 99 was found and fixed) |
| MT5 absence | site-packages scan | **MetaTrader5 / metaapi not installed** (correct) |

### Test-failure attribution (16) — none introduced by this phase

- **5 × `test_risk_manager_harmonized.py`**: `AttributeError: 'RiskManager' object has no attribute 'validate_signal'` — code/test drift, unrelated to dependencies.
- **`test_verify_dependencies.py::test_verify_dependencies_script_success`**: the script exits 1 on the **pre-existing** pyproject-open-range vs requirements-exact-pin regime (documented in 3B §3; 53 mismatch lines today). My new `==` core pins match the requirements files, adding zero new requirements-vs-requirements conflicts (still the same 5 from the 3B baseline).
- **`test_config_validator.py::test_validator_file_permissions` (+ security-mitigation file-permission variants)**: permission-sensitive checks; sandbox user is `EBRAHIM`, project targets a Windows host.
- **`test_debt_cleanup.py`, `test_jules_setup_wizard.py`, `test_reporting_v2.py`, `test_schema_enforcement.py`**: assertions on code shape/templates independent of the dependency changes.

No trading logic was touched to make tests pass, per constraints.

## 6. CI / Docker — final state

- **ci.yml**: unchanged (already uv + 3.12 + `uv sync --locked --group dev --extra ctrader --extra research`; ruff/format/pip-audit/pytest/docker all through `uv run`).
- **migration-safety.yml**: unchanged (already uv + 3.12).
- **pre-deploy-validation.yml**: converted — setup-uv@v5 with Python 3.12 + `uv sync --locked` in all three stages; Gitleaks/Trivy/docker gates unchanged; pip-audit now audits the **locked environment** instead of requirements files; license scan runs `uv run pip-licenses` against the locked env; Gate 11 smoke test uses the locked env (`uv sync --locked --group dev`) instead of `pip install httpx`.
- **release.yml**: converted — same uv pattern; the release job's ad-hoc `pip install pydantic ...` removed (target scripts are stdlib-only; `tomli` fallbacks are guarded); packaging step activates the uv venv so `package_release.sh`'s `python3` calls use Python 3.12 locked env.
- **Dockerfile**: multi-stage `python:3.12-slim`; TA-Lib C 0.6.4 built from source; `uv` copied from `ghcr.io/astral-sh/uv:0.12.13`; `COPY pyproject.toml uv.lock` → `uv sync --locked --extra ctrader --extra research --extra ta-lib` (no dev group in the image, no MT5); runtime copies `.venv`, TA-Lib libs, src; torch CPU-only comes from the `[tool.uv]` pytorch-cpu index on both amd64 and arm64 — **the sed block is gone**; `requirements-docker.txt` is not referenced anywhere.

## 7. Windows-host replication note

The directive's PowerShell commands target the official Windows host (`docs/maintenance/ENVIRONMENT_STANDARD.md`). This sandbox session executed the equivalent POSIX commands. To replicate on the Windows host:

```powershell
& 'C:\ProgramData\uv\uv.exe' lock
& 'C:\ProgramData\uv\uv.exe' sync --group dev --extra ctrader --extra research
& '.\.venv\Scripts\python.exe' --version
& '.\.venv\Scripts\python.exe' -c "import ctrader_open_api; print('cTrader SDK import OK')"
& 'C:\ProgramData\uv\uv.exe' run ruff check src main.py
& 'C:\ProgramData\uv\uv.exe' run ruff format --check src main.py
```

Expected: identical results on Python 3.12 (lock is host-independent; the win32 resolution markers cover the `legacy-mt5` extra, which stays uninstalled).

## 8. Remaining items (only these)

1. **823 ruff violations / 34 unformatted files** in `src`+`main.py` (pre-existing; 487 auto-fixable). CI currently fails on these if run as-is. Needs an approved bulk `ruff check --fix` + `ruff format` pass (a `src/` change, out of this phase's constraints).
2. **16 test failures** (§5 attribution): `RiskManager.validate_signal` drift (5), `verify_dependencies.py` open-range-vs-pin regime (1), sandbox-permission-sensitive tests (~5), misc assertion drift (~5). All pre-existing.
3. **17 pip-audit advisories** in locked transitives: `cryptography 42.0.8` (7), `protobuf 3.20.1` (3), `pyopenssl 24.1.0` (2), `requests 2.32.3` (2, fix = 2.32.4/2.33.0), `twisted 24.3.0` (3 — SDK-pinned; fixes start at 24.7.0rc1/26.4.0). The cryptography/pyopenssl chain arrives via the Twisted/cTrader dependency tree. Resolving requires version bumps beyond the documented/tested SDK pin — needs explicit approval (no blanket upgrade was allowed this phase). `torch 2.14.0+cpu` is not auditable on PyPI by design (CPU index).
4. **`verify_dependencies.py` regime** (53 lines): pyproject exact pins now match requirements where they exist, but legacy open ranges (`numpy>=1.24`, etc.) still trip the exact-string comparator; the requirements files themselves remain the declared fallback source.
5. **Windows-host replication** (§7) and a **CI run on GitHub** remain to be observed on the real infrastructure (sandbox executed everything locally).
6. **`requirements*.txt` retirement decision** (future phase): they are now unused by CI/Docker but still referenced by `scripts/verify_dependencies.py` and the audit tooling.

---

**Phase 3C stops here. Phase 4 requires explicit user approval.**
