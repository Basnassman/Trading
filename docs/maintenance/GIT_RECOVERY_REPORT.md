# Git Recovery Report

**Scope:** local-authoritative-source recovery preparation only.
**Rule:** the local checkout is the authoritative project source. GitHub is used only as a clean Git history/metadata reference.
**Constraint:** no files were copied from the sibling clone into the local authoritative project. No checkout, reset, merge, or history rewrite was performed in the local repository.

---

## 1. Local source authority

- Local repo root: `/home/EBRAHIM/n/mt`
- Local HEAD branch: `main`
- Local HEAD commit: `ccc0d747` — `docs: update CHANGELOG.md [skip ci]`
- Remotes:
  - `origin` → `https://github.com/Basnassman/Trading.git`
  - `impo` → same URL (duplicate remote name)

Local working tree and staged/index state were treated as authoritative for project files. Git metadata in `.git/` was **not** treated as project content and was intentionally excluded from the source backup.

---

## 2. GitHub used only as a clean Git reference

- Remote repository: `https://github.com/Basnassman/Trading.git`
- Used for: fetchable Git history, ref advertisement, and a clean clone for comparison.
- Not used for: restoring or replacing any local project file.

---

## 3. Local file safety artifacts created before recovery

### Manifest (read-only, pre-recovery)

- `docs/maintenance/LOCAL_SOURCE_MANIFEST.md`
  - SHA-256 manifest of local authoritative source files.
  - Covers `src/`, `tests/`, `configs/`, `docs/`, `deployment/`, `tools/`, `scripts/`, plus top-level `main.py`, `pyproject.toml`, and `requirements*.txt`.
  - Excludes by design: `.git/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, secret/env files, local DBs, logs, generated reports/artifacts.

### Backup (safe local copy)

- Backup root: `/home/EBRAHIM/n/project-backup-local`
- Backup manifest: `/home/EBRAHIM/n/project-backup-local/backup-manifest.md`
- Files copied: **604**
- Excluded items documented as present at backup time:
  - `.git/` — Git metadata, not source backup
  - `.venv/` — invalid Linux venv for this Windows-bound project
  - `__pycache__/`, `.pytest_cache/` — cache
  - `.env` — secret, excluded
  - `audit.db`, `trades.db`, `test_engine.db` — local DBs, excluded
  - `logs/`, `reports/` — runtime/generated output
  - `audit_files.json`, `audit_results.json` — large generated audit artifacts

### Integrity verification

- Backup manifest was re-verified against the local authoritative files by recomputing SHA-256.
- Results:
  - manifest rows: **605**
  - missing local file entries: **1** (`---` artifact from the manifest table separator, not a real file)
  - mismatch count: **0**

This confirms the backup matches the local source it was derived from.

---

## 4. Clean sibling clone (Git reference only)

- Sibling clone path: `/home/EBRAHIM/n/Trading-recovered`
- Cloned from: `https://github.com/Basnassman/Trading.git`
- Cloned branch: `main`
- Purpose: clean Git reference for history/metadata and comparison only.

### Clean clone Git state

- `refs/remotes/origin/main`: `ccc0d747776660250fd32a0b0c15e455a0df54ff`
- `HEAD` (sibling): `ccc0d747776660250fd32a0b0c15e455a0df54ff`
- Latest commit: `ccc0d747 docs: update CHANGELOG.md [skip ci]`
- Commit count on `HEAD`: **1442**
- `git fsck --connectivity-only --no-progress`: exit code **0**

No Git objects were copied onto the local repository from this sibling clone.

---

## 5. Comparison: local authoritative source vs GitHub clean clone

Comparison was done at the tracked-file level using `git ls-tree -r HEAD --name-only`.

- Local tracked files: **672**
- Sibling tracked files: **672**
- Common tracked paths: **672**
- Only in local: **0**
- Only in sibling: **0**

From a tracked-file-listing perspective, the local Git index on `main` and the clean GitHub clone on `main` currently list the same tree contents. That is a metadata-level snapshot, not a byte-level comparison of the working tree.

Important nuance:
- This does **not** imply the local `.git` pack/index state is healthy.
- It does **not** imply uncommitted local edits (if any) are reflected in GitHub.
- It does **not** mean the sibling clone should replace the local project.

---

## 6. Recovery plan (documented, not executed)

### If a healthy Git rewrite/rebuild is needed later

1. Keep using the current local checkout as the authoritative source for project files.
2. Use the clean sibling clone only as a Git metadata reference.
3. If a new healthy Git repo is required:
   - Create a new workspace from a clean clone.
   - Copy the authoritative local source files into it.
   - Local files always take precedence.
   - Verify every transferred source file against the local source manifest/backup hashes.
   - Report differences between the local authoritative tree and GitHub as a report only.
4. Do not replace the local authoritative project before explicit approval.

### What was not done on purpose

- No `git reset --hard`
- No `git clean -fdx`
- No checkout/merge/rebase in the local repo
- No copying of any file from the sibling clone into the local authoritative project
- No reading or moving of `.env` or secrets

---

## 7. Conclusion

- Local checkout remains the authoritative source for project files.
- GitHub is usable as a clean Git history/metadata reference; the clean clone appears reachable and connectivity-clean, with `main` at `ccc0d747`.
- Local source files were safely backed up and verified against the local tree before any recovery action.
- No transfer, replacement, or rewrite of the local authoritative project occurred.

Next step (if approved): use the local source manifest/backup as the ground truth when building any future healthy Git workspace, and move the local authoritative files only into that workspace, never the reverse.

---

*End of report.*
