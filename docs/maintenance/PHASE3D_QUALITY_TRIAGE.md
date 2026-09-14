# Phase 3D Report — Quality and Security Triage

- Date: 2026-09-14
- Scope: **read-only** triage of the 16 failing tests, the Ruff population, and the pip-audit findings, in the locked environment. No file was modified except this report — `src/`, `tests/`, CI, Docker, `pyproject.toml`, `uv.lock` untouched (verified via `git status` at the end of the phase: only the Phase 3C changes are present). No cTrader/MT5 connection, no `.env` content read (file metadata only), no files deleted, no Git mutations (read-only `git log`/`status` used as evidence only).
- Method per directive: no failure is labeled "pre-existing" unless supported by (a) a cited prior report, (b) Git history, or (c) a restartable reproduction. Each group below states which of these applies.

## 1. Re-run results (locked environment)

Environment: Linux sandbox equivalent of the prescribed PowerShell battery — `uv run` = `& 'C:\ProgramData\uv\uv.exe' run`; `uv.lock`, Python 3.12.14 (locked), ruff 0.16.7, pytest 9.1.1, structlog 26.1.0, pydantic 2.13.5.

| Check | Command | Result |
|---|---|---|
| Ruff lint | `uv run ruff check src main.py` | **823 violations**, exit 1 (487 auto-fixable, +119 with `--unsafe-fixes`) |
| Ruff format | `uv run ruff format --check src main.py` | **33 files** would be reformatted (64 already formatted) |
| Tests | `uv run pytest tests -q` (CI-parity env vars) | **16 failed, 1113 passed, 1 skipped** — reproduced twice this phase (same 16 IDs) |
| pip-audit | `uv run pip-audit` | **17 known vulnerabilities in 5 packages**, exit 1 (2 packages skipped as not-on-PyPI: `torch 2.14.0+cpu`, this project) |

## 2. The 16 failing tests, grouped by root cause

Reproduction commands are in the appendix (§8). Categories used: **code bug**, **stale test**, **Windows/platform difference**, **missing dependency**, **uncertain**.

### G1 — Test targets an API that does not exist in `src/trading/risk_manager.py` (5 tests)

| Test | Actual error | Location |
|---|---|---|
| `test_drawdown_breaker` | `AttributeError: 'RiskManager' object has no attribute 'validate_signal'` | `tests/test_risk_manager_harmonized.py:74` |
| `test_daily_loss_limit` | same | `:82` |
| `test_max_positions` | same | `:93` |
| `test_directional_exposure` | same | `:105` |
| `test_full_approval` | same | `:122` |
| `test_atr_position_sizing` | `TypeError: size_position() missing 2 required positional arguments: 'avg_win' and 'avg_loss'` | `:112` |

- **Category: stale test.** `validate_signal` occurs **zero** times in `src/trading/risk_manager.py`; it exists in `src/trading/risk_engine.py:80`. The current `RiskManager` surface is `approve / size_position(symbol, win_rate, avg_win, avg_loss) / update_equity / record_pnl / reset_daily` (`risk_manager.py:79–168`), while the test calls `validate_signal(signal, market_data, positions)` and `size_position("XAUUSD", market_data)`.
- **"Pre-existing" evidence: Git history.** `tests/test_risk_manager_harmonized.py` last modified **2026-05-16** (`464f157c`), *newer* than both `src/trading/risk_manager.py` (2026-05-08, `f13e85e8`) and `src/trading/risk_engine.py` (2026-05-07, `f2483507`) — the test was written against a planned harmonized API that was implemented in `risk_engine.py` instead. Also restartable standalone.
- **Proposed fix (separate, small):** repoint the 6 tests to `RiskEngine.validate_signal` (`risk_engine.py:80`) and adapt the `size_position` call to the current signature — *or*, if `RiskManager` is meant to be the gate, add a thin `validate_signal` facade there. **Priority: HIGH** — this is the safety-critical risk-gating path with no executable coverage. Severity: test-only (no production defect demonstrated).

### G2 — `MagicMock(spec=TradingConfig)` cannot see pydantic v2 fields (1 test)

| Test | Actual error | Location |
|---|---|---|
| `test_config_validator_auto_hardening` | `AttributeError: Mock object has no attribute 'database_url'` | test call at `tests/test_security_mitigation.py:92` → `src/core/config_validator.py:734` |

- **Category: stale test** (mock-fixation pattern), with a secondary robustness gap in `src`.
- Evidence (restartable): the fixture builds `MagicMock(spec=TradingConfig)` from the **class** (`tests/test_security_mitigation.py:17`); under pydantic v2, class-level `dir(TradingConfig)` does **not** expose fields, but `TradingConfig.model_fields` **does** contain `database_url` (declared at `src/core/config.py:175`). `MagicMock(spec=<instance>)` exposes it. Fails standalone too — not an ordering issue. Not platform-related; not a missing dependency.
- **Proposed fix:** spec the mock from an instance (e.g. `MagicMock(spec=TradingConfig(MT5_LOGIN=0, MT5_PASSWORD="x", MT5_SERVER="x"))`) or set `database_url` explicitly on the mock. **Priority: MEDIUM.** Severity: low (test-only).

### G3 — Order-dependent structlog reconfiguration breaks 3 security tests (3 tests)

| Test | Standalone | In full suite | Actual error |
|---|---|---|---|
| `test_regime_detector_load_path_validation` | PASS | FAIL | `TypeError: BoundLoggerBase._proxy_to_logger() takes from 2 to 3 positional arguments but 4 were given` at `src/models/regime_detector.py:1010` |
| `test_regime_detector_load_path_bypass_attempt` | PASS | FAIL | same, `:1010` |
| `test_regime_detector_insecure_permissions` | PASS | FAIL | same, `:1024` |

- **Category: code/test-hygiene bug (global state leakage)**; the *identity of the polluting test* is **uncertain**.
- Mechanism (reproduced twice in full runs): some earlier test calls `structlog.configure(...)` (or `main.configure_logging`) with a `wrapper_class` incompatible with the configured processor signatures, and never restores the default configuration. The three tests then crash inside `logger.error(...)` on the *security-rejection paths* they are trying to assert, so their real assertions (`_gmm is None`) are never evaluated.
- Polluter evidence: pairwise runs of these 3 tests with each of the 6 other failing files, and with the 4 files known to reconfigure structlog (`test_cli_ux.py`, `test_trace_correlation.py`, `test_jules_ux_new.py`, `test_institutional_feedback_loop.py`), were all **clean** → the polluter sits among the passing files between `test_reporting_v2` and `test_security_mitigation` in alphabetical order (or is fixture-scoped). **Uncertain** — deliberately not named without proof.
- **Proposed fix (two small, independent options):** (a) add an autouse fixture that snapshots `structlog.get_config()` and restores it after each test; (b) make the 3 tests call `structlog.configure(cache_logger_on_first_use=False)` with defaults up front. Also fix the underlying wrapper/processor mismatch once the polluter is identified. **Priority: MEDIUM-HIGH** — it currently masks three security-path assertions.

### G4 — File-permission test expects "warn", validator now auto-hardens silently (1 test)

| Test | Actual error | Location |
|---|---|---|
| `test_validator_file_permissions` | `assert any(e.field == "FILE_PERMISSION" and ".env" in e.message for e in result.errors)` → `False` | `tests/test_config_validator.py:792` |

- **Category: stale test** (behavior drift), reproduced standalone on Linux.
- Evidence: `_harden_path` (`src/core/config_validator.py:761–784`) silently `chmod`s an insecure 0o666 file to 0o600 and appends a `ValidationError` **only when chmod succeeds-and-verifies**… for *hardened* files it appends `"Hardened insecure permissions..."` — but in this test's flow the mocked `os.stat`/`Path.exists` make the validator resolve the real `.env` (created 0600 by G5's side effect, see below) rather than the tmp file, so no error entry is produced. The test was written for a warn-only validator.
- Platform note: test self-skips on `win32`; failure mode is Linux-specific but the assertion mismatch is not.
- **Proposed fix:** assert the hardening outcome (`os.stat(...).st_mode & 0o777 == 0o600`) and/or expect the "Hardened" error entry, instead of the legacy "FILE_PERMISSION warning" contract. **Priority: LOW-MEDIUM.**

### G5 — Setup-wizard test writes a real `.env` in the project root (1 test)

| Test | Actual error | Location |
|---|---|---|
| `test_setup_wizard_save_logic` | `assert 'MT5_LOGIN=123456\n' in written_data` → written_data is `''` | `tests/test_jules_setup_wizard.py:45` |

- **Category: bug (test hygiene / incomplete mocking).** Reproduced standalone.
- Evidence: the test mocks `builtins.open`, but `main.py:921` writes via `os.open(env_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)` — not interceptable by `mock_open`. The wizard therefore **actually wrote `./.env`**: file exists with mode `-rw-------` and mtime *Sep 14 19:13* (metadata inspected only; content never read), i.e. created by today's test runs, not by a human. The mocked `writelines` capture is empty because `os.fdopen(...).writelines` bypasses the mock. Side effect on every full-suite run: a real `.env` in the repo root.
- **Proposed fix:** patch `main.os.open` (and `os.fdopen`) or run the test with `tmp_path` monkeypatched as CWD; add explicit cleanup. **Priority: HIGH** — recurring side effect on the host filesystem, and the test asserts against the wrong object.

### G6 — `PerformanceContext.sharpe_ratio` missing its documented upper bound (1 test)

| Test | Actual error | Location |
|---|---|---|
| `test_performance_context_constraints` | `Failed: DID NOT RAISE ValidationError` | `tests/test_schema_enforcement.py:50` |

- **Category: code bug** (missing model constraint). Restartable probe: `PerformanceContext(sharpe_ratio=11.0)` → **no raise**; `max_drawdown=1.5` → raises; `profit_factor=-1.0` → raises. The field (`src/core/decision_support.py:63–66`) declares `ge=-10.0` but **no `le=10.0`**, while the test (and the model's own audit contract) requires Sharpe ≤ 10.
- **Proposed fix:** add `le=10.0` to `sharpe_ratio` in `PerformanceContext`. **Priority: HIGH** — this is a data-integrity guard on operator-facing performance metrics. Severity: low runtime impact, high audit value.

### G7 — Markdown template renders the enum repr instead of the status value (1 test)

| Test | Actual error | Location |
|---|---|---|
| `test_v2_template_rendering` | `assert '- **Status:** VERIFIED' in md` → md contains `- **Status:** SectionStatus.VERIFIED` | assertion at `tests/test_reporting_v2.py:51`; field at `src/research/reporting.py:417` (`overall_status: SectionStatus`); template line 7 of `src/research/templates/research_report.md.j2` |

- **Category: code bug** (rendering). Full-string probe (pytest truncation ruled out): the render emits the enum repr `SectionStatus.VERIFIED`. The HTML assertion passes only by substring accident (`"VERIFIED" in "SectionStatus.VERIFIED"`).
- **Proposed fix:** render `.value` in the template (`{{ overall_status.value }}`) or add a `value` field on `ResearchReport` via a computed/serialized property. **Priority: LOW-MEDIUM** — cosmetic in Markdown/HTML reports, but machine-parsed reports would break.

### G8 — Manifest harmonization comparator vs declared range/pin divergence (1 test)

| Test | Actual error | Location |
|---|---|---|
| `test_verify_dependencies_script_success` | script exit 1, 53 `Package:` mismatch lines (pyproject open ranges vs requirements exact pins) | `tests/test_verify_dependencies.py:19`; comparator `scripts/verify_dependencies.py:1–20` |

- **Category: stale comparator / declared-intentional divergence.** This is the **only** group where "pre-existing" is used with direct evidence: documented in PHASE3B §3 and PHASE3C §8.4, plus a fresh re-run this phase. The 5 requirements-vs-requirements conflicts are unchanged from the Phase 3B baseline; Phase 3C's exact pins added none.
- **Proposed fix:** teach the comparator set semantics (a pin `==2.4.6` satisfies a declared range `>=1.24`) *or* pin pyproject fully — a policy decision. **Priority: MEDIUM.**

**Category tally:** stale test 8 (G1 ×6, G2, G4) · code bug 2 (G6, G7) · test-hygiene bug 1 (G5) · global-state bug w/ uncertain polluter 3 (G3) · stale comparator 1 (G8). **Missing dependency: 0** — no failure is caused by an absent package.

## 3. Ruff — 823 violations (src + main.py)

### By rule code, with classification

| Rule | Count | Nature | Class |
|---|---|---|---|
| W293 blank-line-with-whitespace | 318 | whitespace on blank lines | **pure formatting** |
| E501 line-too-long | 177 | >100 chars | **formatting** (ruff format does not wrap) |
| UP045 `Optional[X]` → `X \| None` | 131 | modernization | lint (auto) |
| UP006 `List/Dict` → `list/dict` | 36 | modernization | lint (auto) |
| UP037 quoted annotations | 30 | modernization | lint (auto) |
| UP042 `StrEnum` | 27 | modernization | lint (manual/unsafe) |
| F401 unused-import | 24 | dead code | **lint/logical** (needs judgment) |
| UP017 `timezone.utc` → `UTC` | 21 | modernization | lint (auto) |
| N806 non-lowercase variable | 20 | naming | lint/style (manual) |
| I001 unsorted-imports | 13 | import order | **formatting-adjacent** (auto) |
| UP035 deprecated-import | 10 | modernization | lint (auto) |
| N818 exception-name-suffix | 10 | naming | lint/style (manual) |
| N813 camelCase-imported-as-lowercase | 2 | naming | lint/style (manual) |
| UP015 redundant-open-modes | 2 | modernization | lint (auto) |
| F841 unused-variable | 2 | dead code | **lint/logical** (needs judgment) |

### Formatting vs lint/logical split

- **Formatting (508 + 33 files):** W293 (318) + E501 (177) + I001 (13) = **508 violations** are pure formatting/whitespace/import-order; additionally **33 files** fail `ruff format --check`. Resolved by one approved `ruff format` + `I001/F401 --fix` pass — zero semantic risk.
- **Modernization (257):** UP045/UP006/UP037/UP042/UP017/UP035/UP015 = 257, behavior-preserving syntax updates; 240 safe-auto-fixable, UP042 (27, StrEnum) is the risky one.
- **Lint/logical (58):** F401 (24) + F841 (2) = 26 dead-code findings that require human judgment (a "unused" import may be a re-export), and N806/N818/N813 (32) naming conventions. **No outright logic errors were detected by Ruff** (no F821 undefined-name, no B-class bugs in the selected ruleset).

### Largest affected files

| File | Violations |
|---|---|
| `src/engines/interfaces.py` | 73 |
| `src/providers/interfaces.py` | 62 |
| `src/canonical/contracts.py` | 53 |
| `main.py` | 51 |
| `src/audit/contracts.py` | 48 |
| `src/validation/validators.py` | 47 |
| `src/persistence/models.py` | 39 |
| `src/trading/mt5_connector.py` | 30 |
| `src/ingestion/pipeline.py` | 30 |
| `src/models/ensemble.py` | 25 |

## 4. pip-audit — 17 findings, all transitive

Fresh re-run (`uv run pip-audit`, exit 1). Direct/transitive status determined from `uv.lock` reverse-dependency analysis (reproducible — see appendix). **None of the project's direct dependencies carries a finding; every vulnerable package is pulled in by `ctrader-open-api==0.9.2` (or its chain).**

| Package | Version | Findings | Direct/Transitive | Path (uv.lock) | Fix versions |
|---|---|---|---|---|---|
| cryptography | 42.0.8 | 7 (PYSEC-2026-35/-1284/-2141/-3553/-3554, GHSA-h4gh-qq45-vh27, GHSA-537c-gmf6-5ccf) | transitive | pyopenssl → **ctrader-open-api**; service-identity | 43.0.1 … 49.0.0 |
| pyopenssl | 24.1.0 | 2 (PYSEC-2026-2269, PYSEC-2026-2268) | transitive (direct dep of the SDK) | **ctrader-open-api** | 26.0.0 |
| protobuf | 3.20.1 | 3 (PYSEC-2026-899, PYSEC-2026-1806, PYSEC-2026-1805) | transitive (direct dep of the SDK) | **ctrader-open-api** | 3.20.2 / 4.25.8 / 5.29.6+ |
| requests | 2.32.3 | 2 (PYSEC-2026-1872, PYSEC-2026-2275) | transitive (direct dep of the SDK; also metaapi-cloud-sdk, pip-audit, cachecontrol) | **ctrader-open-api** | 2.32.4 / 2.33.0 |
| twisted | 24.3.0 | 3 (PYSEC-2024-75, PYSEC-2026-160, PYSEC-2026-1992) | transitive (direct dep of the SDK) + locked explicitly (Phase 3C item 3) | **ctrader-open-api** | 24.7.0rc1 / 26.4.0 |

Skipped (not findings): `torch 2.14.0+cpu` (CPU index, not on PyPI — by design), `xauusd-trading-system` (this project).

### cTrader impact assessment

- `uv.lock` shows `ctrader-open-api 0.9.2` declares **no version constraints** on twisted/pyopenssl/protobuf/requests — so all four are freely bumpable **without changing the SDK pin**, which keeps Phase 3C's documented-pin policy intact.
- **requests → 2.32.4** (patch): near-zero risk to cTrader; **protobuf → 3.20.2** (patch on the same 3.20 line): near-zero risk.
- **pyopenssl → 26.0.0** (major): TLS API churn; requires co-bumping `cryptography` (→ 43.0.1+ for GHSA-h4gh, ideally 46+ for the newest advisories) and re-running the cTrader smoke test (`tools/ctrader_smoke_test/`) to validate the Twisted–pyOpenSSL handshake path. **No source changes expected.**
- **twisted → 24.7.0rc1 is a release candidate** (not stable); the stable fix line is 26.4.0 (major). Bumping Twisted departs from the SDK's own tested pin (24.3.0) recorded in Phase 3B/3C — needs an explicit decision plus a cTrader smoke-test re-run. Until then, `PYSEC-2024-75`/`PYSEC-2026-160`/`PYSEC-2026-1992` remain accepted risk.
- Current verified state: `import ctrader_open_api` is clean in both the venv and the Docker image (Phase 3C §5) — the advisories are latent, not active regressions.

## 5. `service-identity` placement — verified correct

- Declared **only** in `[project.optional-dependencies].ctrader` (`pyproject.toml`), alongside `ctrader-open-api==0.9.2` and `Twisted`; **not** in `[project.dependencies]` (core).
- `uv.lock` confirms: under `xauusd-trading-system`, `ctrader = [{ name = "ctrader-open-api" }, { name = "service-identity" }, { name = "twisted" }]`; `service-identity 24.2.0` pulls `attrs/cryptography/pyasn1/pyasn1-modules` (the latter two add `pyasn1-modules` to the lock, previously absent).
- Grep across `src/`, `main.py`, `scripts/`, `tools/`: **zero** direct imports of `service_identity` in core code — it is Twisted's optional TLS-hardening bundle, required by the cTrader/TLS path, not by core. Placement matches the directive: cTrader-scoped because the cTrader path needs it; core would be wrong (core never imports it).

## 6. Proposed small fixes (one per root cause — none applied without approval)

| # | Root cause | Minimal fix | Severity | Priority |
|---|---|---|---|---|
| 1 | G1 risk-API drift (6 tests) | Repoint `test_risk_manager_harmonized.py` to `RiskEngine.validate_signal` (`risk_engine.py:80`) + fix `size_position` call args; or add a `validate_signal` facade to `RiskManager` | High (untested risk gate) | **P1** |
| 2 | G5 wizard test writes real `.env` | Patch `main.os.open`/`os.fdopen` (or tmp-CWD) in `test_jules_setup_wizard.py`; assert on the mock | High (host side effect) | **P1** |
| 3 | G6 missing Sharpe cap | Add `le=10.0` to `sharpe_ratio` in `PerformanceContext` (`decision_support.py:63`) | Medium | **P1** |
| 4 | G3 structlog global-state leakage (3 tests) | Autouse fixture to snapshot/restore `structlog.get_config()`; then identify the polluter with a `-p xdist`-free bisect | Medium-High | **P2** |
| 5 | G2 mock-spec vs pydantic fields | Spec the mock from a `TradingConfig` instance (or set `database_url` on it) | Low | **P2** |
| 6 | G4 permissions contract drift | Update `test_validator_file_permissions` to assert hardening outcome (0o600) | Low-Medium | **P2** |
| 7 | G7 enum repr in reports | Render `{{ overall_status.value }}` in `research_report.md.j2` (and check `.html.j2`) | Low-Medium | **P3** |
| 8 | G8 comparator semantics | Make `verify_dependencies.py` treat a pin as satisfying a range (policy decision) | Medium | **P3** |
| 9 | Ruff formatting (508 + 33 files) | One approved `ruff format` + safe `--fix` (W293/E501-adjacent/I001) — no logic changes | Low | **P2** |
| 10 | Ruff dead code (F401 ×24, F841 ×2) | Case-by-case review, then targeted removal | Low | **P3** |
| 11 | Ruff modernization (UP*, 257) | Safe auto-fixes; UP042 StrEnum separately with review | Low | **P3** |
| 12 | requests 2.32.3 → 2.32.4, protobuf 3.20.1 → 3.20.2 | `uv lock`-scoped bumps (no SDK pin change) + cTrader smoke test re-run | Medium | **P2** |
| 13 | pyopenssl/cryptography chain | Coordinated bump (pyopenssl 26.0.0 + cryptography 43.0.1+) + cTrader smoke test re-run | Medium-High | **P2-P3** |
| 14 | twisted 24.3.0 advisories | Decision required: stay on SDK-tested pin (accept risk) vs move to 26.4.0 (major) — both need a smoke test | Medium | **P3 (decision)** |

## 7. Constraint compliance

- `src/`, `tests/` untouched; CI/Docker/`pyproject.toml`/`uv.lock` untouched; no Ruff/pip-audit ignores added; no files deleted; no cTrader/MT5 connection; no `.env` content read (metadata `ls -l` only, to prove G5's side effect); no Git mutations (read-only `git log`/`status` as evidence). Single output file: this report.

## 8. Reproducibility appendix

```bash
export MT5_LOGIN=0 MT5_PASSWORD=test MT5_SERVER=test MODE=demo PYTHONPATH=.
uv run pytest tests -q                                   # 16 failed / 1113 passed
uv run pytest tests/test_risk_manager_harmonized.py -q   # G1: 6 failures, standalone
uv run pytest tests/test_security_mitigation.py -q       # G2 fails; G3's 3 regime tests PASS standalone (order dependence)
uv run ruff check src main.py --statistics               # 823, per-rule table
uv run ruff format --check src main.py                   # 33 files
uv run pip-audit --progress-spinner off                  # 17 findings, exit 1
.venv/bin/python -c "from src.core.config import TradingConfig; \
  print('database_url' in TradingConfig.model_fields)"   # True (vs dir() -> False, G2 evidence)
```

Reverse-dependency mapping for §4 (deterministic): parse `uv.lock`, list packages whose `dependencies` contain each target.

---

**Phase 3D stops here. No fix has been applied; each item above requires explicit approval before execution.**
