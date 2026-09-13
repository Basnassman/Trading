# Phase 3B Report — Dependency Declaration Fixes

- Date: 2026-09-13
- Basis: `docs/maintenance/DEPENDENCY_INVENTORY_RAW.md` (Phase 3A, point-in-time snapshot — left unmodified)
- Scope: user-approved selection from Phase 3A findings (see §1). All edits are declaration/config edits; no packages installed, no lockfiles generated, no tests run, no network, no Git operations.

## 1. Approved scope (user selection)

1. Declare the undeclared packages (ctrader-open-api, Twisted, MetaTrader5, playwright).
2. Fill `requirements-ci.txt` gaps (psycopg2-binary, pyyaml, python-dotenv, pytz).
3. Harmonize ruff/mypy pins between CI workflows and requirements files.
4. Fix the stale Dockerfile AMD64 sed block.
5. Fix the "Python 3.10+" headers in requirements-linux/-temp.

## 2. Changes made

### 2.1 `pyproject.toml` — new optional-dependencies groups

Added three extras groups (dev group untouched). Versions intentionally unpinned because no baseline version exists anywhere in the repo (they were never declared):

- `ctrader`: `ctrader-open-api`, `Twisted` — imported by all 5 files in `tools/ctrader_smoke_test/`.
- `mt5`: `MetaTrader5` — imported by `src/providers/mt5/market_data.py`, `src/trading/mt5_connector.py`, `tests/test_system_bootstrap_to_execution.py`.
- `playwright`: `playwright` — imported by `tests/verify_reporting_frontend.py`.

Rationale: extras keep these optional (MT5 is Windows-only; cTrader tools are standalone), so `pip install .` and CI requirements remain unchanged in behavior.

### 2.2 `requirements-ci.txt` — gap fill (aligned with pyproject.toml / other requirements files)

- Added `psycopg2-binary==2.9.12` (matches -docker/-linux/-temp pins).
- Added configuration block: `python-dotenv==1.2.3`, `pyyaml>=6.0`, `pytz==2026.3.post1`.
  - `python-dotenv` is imported by `scripts/doctor.py` and the 5 cTrader smoke-test files; the pydantic-settings pin already depends on it transitively, so the pin matches what was actually resolving.
  - `pyyaml` uses `>=6.0` matching `pyproject.toml`/`requirements.txt` (no pinned baseline existed in any requirements file).
  - `pytz` pin matches -docker/-linux/-temp.

### 2.3 CI workflows — ruff/mypy pin harmonization

Aligned to the requirements-file pins (`ruff==0.16.6`, `mypy==2.3.1`), since the requirements files are the canonical declaration source and CI installs were the drifting side:

- `.github/workflows/ci.yml`: `ruff==0.16.1 mypy==2.3.0` → `ruff==0.16.6 mypy==2.3.1`
- `.github/workflows/release.yml`: same replacement in the validate job install line.
- `.github/workflows/pre-deploy-validation.yml`: same replacement in the validation tools install line.

### 2.4 `Dockerfile` — stale AMD64 sed block

The AMD64 branch rewrote `torch==2.3.1` / `torchvision==0.18.1`, but `requirements-docker.txt` pins `torch==2.14.0+cpu` and `torchvision` is declared nowhere — the sed was a no-op. Replaced with an explicit no-op branch (`echo "AMD64: using requirements-docker.txt as-is"`) plus a comment. The ARM64 branch is untouched (it correctly strips `+cpu` and the extra index).

### 2.5 `requirements-linux.txt` / `requirements-temp.txt` — version headers

Header comment changed from `# Compatible: Python 3.10+` to `# Compatible: Python 3.11+` to match `pyproject.toml` `requires-python = ">=3.11"`.

## 3. Verification (user-selected: harmonization script only)

- `python3 scripts/verify_dependencies.py` was run **before** the edits to capture a baseline: it exited 1 with 45 mismatch lines, all of the pre-existing "pyproject.toml open range vs requirements exact pin" regime (e.g. `numpy >=1.24` vs `==2.4.6`) plus 5 requirements-vs-requirements range-vs-pin lines (`pytest`, `pytest-cov`, `hypothesis`, `ruff`, `mypy`).
- After the edits, the script's requirements-vs-requirements mismatch set is **unchanged** (same 5 lines). The gap fill added pyproject-range-vs-pin lines only for packages that already appeared in that regime via -docker/-linux/-temp (`psycopg2-binary`, `python-dotenv`, `pytz`); **no new requirements-to-requirements conflicts were introduced**.
- The script exits 1 on the pre-existing regime by design (exact-string comparison). That regime divergence was documented in Phase 3A §8.2 and is **out of scope** for this phase; it would require either pinning pyproject or relaxing requirements — a decision left for a future phase.
- `pyproject.toml` parses successfully (tomllib); extras groups now: `ctrader`, `dev`, `mt5`, `playwright`.
- Grep confirms no `ruff==0.16.1` / `mypy==2.3.0` remains under `.github/workflows/`, and both version headers read `Python 3.11+`.

## 4. Explicitly not done (constraints honored)

- No `uv` commands, no `uv sync`, no `uv.lock`.
- No package installs or removals; no venv changes.
- No test runs; no application code changes.
- No network connections (cTrader/MT5 untouched); no `.env` reads.
- No Git operations (nothing staged or committed).
- Phase 3A inventory left as-is (it documents the pre-fix state; this report supersedes its §6/§8.2 findings).

## 5. Residual items (for a future phase, not executed)

- pyproject open-range vs requirements exact-pin regime (verify_dependencies.py exit 1 driver).
- CI ad-hoc tool installs (`pip-audit`, `pip-licenses`, `torchvision`) not declared in any requirements file.
- TA-Lib C library (v0.6.4) vs Python binding (`TA-Lib==0.7.1`) version-family note.
- `hypothesis` declared in 4 sources but never imported in the scanned scope.

---

_End of Phase 3B report._
