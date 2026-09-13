# Cleanup Manifest

**Purpose:** classify repo items for safe removal, archival/review, or retention.
**Rule:** nothing in `archive_or_review` is deleted in this phase. Only `safe_to_remove_now` may be deleted after Phase 2+ approval and only if it matches the stated category.

---

## 1. `safe_to_remove_now`

These are non-source, regeneratable, or clearly local cache artifacts.

### Cache and bytecode

- `__pycache__/`
- `src/**/__pycache__/`
- `tests/**/__pycache__/`
- `tools/**/__pycache__/`
- `*.pyc` files throughout repo
- `.pytest_cache/`
- `.ruff_cache/` if present
- `.mypy_cache/` if present

### Invalid local environment

- `.venv/` — current venv is a Linux-originated environment and not usable for local Windows development.

### Other temporary local artifacts (if present)

- Local editor/OS metadata already covered by `.gitignore`
- Any ephemeral tool artifacts that are clearly regeneratable and not committed source

---

## 2. `archive_or_review`

These items must **not** be removed immediately. They should be classified, moved, or archived through a deliberate step with an owner decision.

### Large generated/audit outputs

- `audit_files.json`
- `audit_results.json`

Suggested handling:
- Determine whether these are regeneratable.
- If regeneratable and large, move to `artifacts/` or `reports/generated/` and exclude from Git.
- If they are audit evidence, consider external archive rather than repo storage.

### Local databases

- `audit.db`
- `trades.db`
- `test_engine.db`

Suggested handling:
- Classify each as:
  - operational data
  - test fixture
  - audit artifact
- Decide whether to keep in repo, move to `artifacts/`, or regenerate from migrations/scripts.
- Avoid deleting before confirming whether they are inputs to tests/operations.

### Reports and logs

- `reports/`
- `logs/`

Suggested handling:
- Treat as generated/runtime output.
- Keep only what is intentionally stored; exclude generated reports/logs from Git via `.gitignore`.
- Move historical artifacts to `reports/generated/` or an external archive.

### Unclear root files

- `info-porjact`
- `To`

Suggested handling:
- Review before deletion.
- If irrelevant, document reason and then remove; if useful, reclassify.

### Near-duplicate requirement files

- `requirements-temp.txt`
- `requirements-linux.txt` vs `requirements-ci.txt` vs `requirements-ci-no-talib.txt` vs `requirements-docker.txt` vs `requirements-test.txt`

Suggested handling:
- Do not delete yet.
- Decide which files become generated artifacts from a single locked source.
- Document obsolescence in `DEPENDENCY_MATRIX.md` and `.gitignore`/manifest policy.

### Documentation organization candidates

Current `docs/` layout is large and not yet aligned to the target structure. Candidates for future reclassification/migration:
- MT5-centric docs should later be marked legacy/pending cTrader migration.
- Generated status/audit-style docs may be better placed under `docs/legacy/` or `docs/maintenance/` depending on content.

### Git loose file objects at root

- `file:<hash>` entries seen at repo root are Git object artifacts from the current repo state.

Suggested handling:
- Not normal project files.
- Do not “clean” them by hand in the working tree.
- Resolve through Git recovery/refs/pack health steps, not by ad hoc deletion.

---

## 3. `must_keep`

These are source, tests, migrations, tooling, docs, configuration, and platform files that should be preserved in this phase.

### Source and canonical layers

- `src/`
- `src/canonical/`
- `src/providers/interfaces.py`
- `src/providers/mt5/`
- `src/providers/mock/`
- `src/providers/paper/`
- `main.py`

### Tests

- `tests/`
- All test modules and fixtures

### Migration and schema

- `migrations/`
- `alembic.ini`
- Related DB/schema tooling

### cTrader smoke tools and related tests/docs

- `tools/ctrader_smoke_test/`
- `tests/test_ctrader_spot_stream.py`
- `tests/test_ctrader_historical_data.py`
- `tests/test_gate4_session_validation.py`
- `docs/data/PHASE25_5_CTRADER_INTEGRATION_REPORT.md`

### Build, CI, Docker, and dev workflow

- `pyproject.toml`
- `Makefile`
- `Dockerfile`
- `Dockerfile.dev`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `.github/`
- `.pre-commit-config.yaml`
- `.pip-audit.ignore`
- `configs/`
- `deployment/`
- `scripts/`

### Documentation to preserve

- Existing architecture/operations/research docs
- Runbooks
- Security/quality/release docs
- Contribution docs
- Any doc that is part of active project knowledge

### Project-level docs and policies

- `README.md`
- `CHANGELOG.md`
- `SECURITY.md`
- Other top-level policy/docs that are part of the maintained project surface

---

## 4. Proposed future exclusions (Git hygiene)

After review, `.gitignore` should be expanded/aligned so these never re-enter the repo:

- Virtual environments (`.venv/`, `venv/`)
- Bytecode (`__pycache__/`, `*.pyc`)
- Test/cache artifacts (`.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`)
- Local runtime/regeneratable output (`logs/`, generated `reports/*`)
- Large generated audit artifacts if they are not intended as committed deliverables
- Local DB files if they are runtime/test artifacts rather than committed fixtures

---

*End of Phase 0 manifest.*
