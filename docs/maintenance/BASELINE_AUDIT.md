# Baseline Audit — Foundation Repair & Cleanup

**Scope:** read-only inventory before any edits, deletes, or commits.
**Goal:** establish a protected, documented baseline for Git recovery, environment standardization, dependency unification, and safe cleanup.

> Non-destructive rule for this phase: no `.env` contents, no secret values, no destructive Git commands, no file deletion without manifest + reason.

---

## 1. Git state

- Current HEAD: `main`
- Commit (main): `ccc0d747` — `docs: update CHANGELOG.md [skip ci]`
- Remotes:
  - `origin` → `https://github.com/Basnassman/Trading.git`
  - `impo` → same URL (duplicate remote with different name)
- Local refs:
  - `refs/heads/main` → `ccc0d747`
  - `refs/remotes/origin/HEAD` → `ccc0d747`
  - `refs/remotes/origin/main` → `ccc0d747`
  - `refs/remotes/origin/dependabot/docker/python-3.14-slim` → `38b6aee3`
  - `refs/remotes/origin/dependabot/pip/rich-15.0.0` → `44cd24e5`
- Last fetch advertisement from remote matches local main exactly: `ccc0d747776660250fd32a0b0c15e455a0df54ff`

### Observed pack/index mismatch risk

- `git status` reported no dirty output here, but local context earlier indicated `git status` showing packfile/index mismatch.
- In this checkout:
  - `.git/index` timestamp: **2026-09-13 01:11:54**
  - pack idx timestamp: **2026-08-31 00:19:21**
  - pack file timestamp: **2026-09-12 23:07:29**
- This timing gap is suspicious: the packfile was rewritten/updated **after** the original idx, but the index file seen here is newer than the idx. That pattern is consistent with a partially rebuilt or corrupted index/pack relationship.
- Object counts:
  - Loose objects: `229`
  - In-pack objects: `25310`
  - One pack: `pack-6032ffe243e3944bb647b7f6e13d984c789e6a59`
- fsck (connectivity-only, non-destructive) reported many dangling commits but **no fatal unreachable/corrupt errors in this run**.
- Nominal object verification passed for sampled paths (`HEAD:main.py`, `HEAD:pyproject.toml`).

### Interpretation

- This repository is **not clearly healthy**, and the earlier `git status` packfile complaint is plausible. fsck can still pass partially while index/pack consistency is unreliable for normal working-tree ops.
- Recommendation: **do not trust this copy for new commits or history rewrites**. Treat it as a read-only reference until recovery is completed from a clean clone or a known-good bundle.

---

## 2. Local Python

- `python -V`: **Python 3.13.12**
- `git --version`: **git version 2.53.0**
- Node: **v24.15.0**
- npm: **11.16.0**

Note: local Python is **3.13**, but project tooling currently assumes other versions in places (see dependency/CI/Docker mismatch below).

---

## 3. Virtual environment state

- `.venv/pyvenv.cfg`:
  - `home = /usr/bin`
  - `version = 3.13.12`
  - `executable = /usr/bin/python3.13`
  - `command = /usr/bin/python3 -m venv /home/EBRAHIM/n/mt5-ai-xauusd-trader/.venv`
- Interpretation:
  - This is a **Linux venv** created under `/usr/bin`, with absolute Linux paths baked into `pyvenv.cfg`.
  - On Windows this environment is **not directly usable** because activation scripts, shebang resolution, and compiled bytecode/c extensions are not portable across OSes.
  - Size: **~1.6G** in `.venv`.
- Conclusion: `.venv` should be treated as **invalid for local Windows use** and replaced by a Windows-native venv later. It must not be reused as-is.

---

## 4. Build, package, CI, and Docker files

### Top-level package/requirements files

- `pyproject.toml`
- `requirements.txt`
- `requirements-ci.txt`
- `requirements-ci-no-talib.txt`
- `requirements-docker.txt`
- `requirements-linux.txt`
- `requirements-temp.txt`
- `requirements-test.txt`

### Build/CI/Docker

- `Makefile`
- `Dockerfile`
- `Dockerfile.dev`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `.pre-commit-config.yaml`
- `.pip-audit.ignore`
- `.github/workflows/*.yml` (many workflows)
- `.github/dependabot.yml`
- `.github/ISSUE_TEMPLATE/*.yml`

### Config/deployment directories

- `configs/`
- `deployment/`
- `scripts/`
- `migrations/`
- `models/`
- `logs/`

### Important version mismatch observations

- `pyproject.toml`:
  - `requires-python = ">=3.11"`
  - Tooling hints: `[tool.ruff] target-version = "py311"`, `[tool.mypy] python_version = "3.11"`
- CI (`.github/workflows/ci.yml`):
  - Uses **Python 3.11** for quality/security/test jobs.
- Docker:
  - `Dockerfile`: `FROM python:3.12-slim` (builder + runtime)
  - `Dockerfile.dev`: `FROM python:3.12-slim`
- Local environment:
  - Python **3.13.12** venv (Linux-originated)

So there are at least **three different Python versions in play**: 3.11 (CI/pyproject tool hints), 3.12 (Docker), 3.13 (local venv).

### Snapshot of dependency divergence (read-only)

- `pyproject.toml` declares a small core dependency set (`sqlalchemy`, `alembic`, `psycopg2-binary`, `numpy`, `pandas`, `pyyaml`, `python-dotenv`, `httpx`, `structlog`, `pytz`) plus a modest `dev` optional group.
- Requirements files are **pragmatic/legacy-pinned** and much larger, including ML/RL/TA-Lib/MetaAPI/cloud/etc.
- Notable examples:
  - `requirements-ci.txt`: pins numpy/pandas/scipy/sklearn, TA-Lib, redis, pydantic, metaapi-cloud-sdk, pytest stack, fastapi, etc.
  - `requirements-docker.txt`: adds torch CPU, stable-baselines3, uvicorn, tqdm, etc.
  - `requirements-linux.txt`: similar to docker but not identical; includes pre-commit/ruff/mypy.
  - `requirements-temp.txt`: almost identical to `requirements-linux.txt` with small differences.
- Conclusion: there is no single source of truth for dependencies today. This is a primary repair target in later phases.

---

## 5. Direct MT5 dependencies and cTrader assets

### Direct MT5 references (code)

- `src/trading/mt5_connector.py` — primary MT5 connector implementation, including `place_order(...)`.
- `main.py` — calls `connector.place_order(signal)`.
- `src/core/config.py` — defines MT5 settings (`mt5_login`, `mt5_password`, `mt5_server`, `mt5_path`) and MetaAPI cloud fallback settings.
- Test files exercise MT5 connector behavior (for example `tests/test_mt5_connector_new.py`, `tests/test_resilience_v2.py`, `tests/test_circuit_breaker.py`).
- MT5 also appears across many docs/features/specs (see later section).

### cTrader-related assets (keep)

- `tools/ctrader_smoke_test/`:
  - `smoke_test.py`
  - `historical_data.py`
  - `spot_stream.py`
  - `symbol_discovery.py`
  - `symbol_schedule_reconciliation.py`
  - `README.md`
  - plus `__pycache__` artifacts (cache, not source).
- Tests referencing cTrader smoke-test modules:
  - `tests/test_ctrader_spot_stream.py`
  - `tests/test_ctrader_historical_data.py`
  - `tests/test_gate4_session_validation.py` (imports `tools.ctrader_smoke_test.historical_data`)
- Docs referencing cTrader:
  - `docs/data/PHASE25_5_CTRADER_INTEGRATION_REPORT.md`
  - Plus MT5-related docs that also mention cTrader in a migration/comparison context.

### Provider/canonical layers to preserve

- `src/canonical/` — broker-neutral contracts layer.
- `src/providers/interfaces.py` — provider interface layer.
- `src/providers/mt5/` — current MT5 provider implementation.
- `src/providers/mock/` — mock provider(s).
- `src/providers/paper/` — paper/execution provider(s).

---

## 6. Large, generated, duplicated, or unclear items

### Very large / storage-heavy

- `.venv/` — ~1.6G (invalid Linux venv on this Windows-bound project).
- `audit_files.json` — ~7.3G (large generated/audit artifact candidate).
- `audit_results.json` — ~7.8G (large generated/audit artifact candidate).
- `audit.db`, `trades.db`, `test_engine.db` — local SQLite databases (operational/audit data).
- Many `file:<hash>` loose objects at repo root are **Git object artifacts** and are not project deliverables; they should be handled through Git recovery, not as normal project files.

### Generated / runtime artifacts

- `reports/` — reports directory (likely generated output).
- `logs/` — logs directory.
- `__pycache__/`, `src/**/__pycache__/`, `tests/**/__pycache__/`, `tools/**/__pycache__/` — bytecode caches.
- `.pytest_cache/`
- Many `*.pyc` files under `src/`, `tools/`, and `tests/`.
- `audit_files.json` / `audit_results.json` — appear to be generated audit outputs.
- `info-porjact` — unclear purpose; appears to be a top-level non-standard file.

### Documentation volume / organization issues

- `docs/` is large and currently organized in many subfolders that do not yet match the target maintenance layout requested for this project.
- There is no `docs/maintenance/` yet.
- There is no `docs/legacy/mt5/` yet.

### Unclear purpose items (flag for review, not delete)

- `info-porjact`
- `To` (empty file at root)
- `requirements-temp.txt` (appears near-duplicate of `requirements-linux.txt`)
- `requirements-ci-no-talib.txt` vs `requirements-ci.txt`
- Multiple near-duplicate requirements files overall.

---

## 7. CI/Docker/local Python version table

| Environment | Python version seen | Notes |
|---|---|---|
| Local venv | 3.13.12 (Linux) | Invalid for local Windows use as-is |
| pyproject tooling hints | 3.11 | ruff target-version, mypy python_version |
| CI workflows | 3.11 | setup-python in ci.yml |
| Docker (Dockerfile) | 3.12-slim | builder + runtime |
| Docker dev (Dockerfile.dev) | 3.12-slim | skeleton dev image |

This is a clear standardization candidate.

---

## 8. MT5 and cTrader doc footprint (read-only)

- MT5 appears across a large portion of `docs/`, including specs, features, runbooks, audits, status, releases, and architecture docs.
- cTrader-specific doc footprint is smaller and currently centered on:
  - `docs/data/PHASE25_5_CTRADER_INTEGRATION_REPORT.md`
- This aligns with the known state: MT5 is the active operational path; cTrader has been explored/testable via smoke tools but not yet migrated.

---

## 9. Baseline conclusion

1. Git: **not safe as a working source of truth** yet; a clean remote-sourced clone or bundle is preferred before any commits.
2. Python: **version drift exists** across local, CI, and Docker; standardization is required.
3. `.venv`: **invalid Linux venv** for this Windows-bound project; replace, do not reuse.
4. Dependencies: **multiple conflicting requirement files**; `pyproject.toml` should become the source of truth.
5. MT5: **still core operational dependency** in code and docs; must be preserved and labeled legacy/pending migration.
6. cTrader: **smoke test tooling and related tests/docs must be preserved**; they are future bridge assets.
7. Cache/large/generated items: **present and must be classified** before any cleanup.

---

*End of Phase 0 audit.*
