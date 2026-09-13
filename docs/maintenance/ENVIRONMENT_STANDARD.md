# Environment Standard — XAUUSD Toolchain (Phase 2)

> Status: Phase 2 completed. `.venv` created on Windows using direct Python 3.12 and `uv` paths. No project packages installed, no `uv sync`, no `uv.lock`.

## Official target runtime

- **Python version:** 3.12 (official project target).
- **Environment manager:** `uv` (official project tool for environment + lockfile lifecycle).
- **Lockfile:** `uv.lock` is **not** generated in Phase 2. It is created only during Phase 3 (package unification).

## Host environment requirement

The project's intended execution host is **native Windows**, not WSL.

- WSL is **not** the official runtime environment for this project.
- A Linux shell, Linux Python installation, or a WSL filesystem path is not sufficient to claim Phase 2 completion for this project.
- Phase 2 should be completed from a Windows PowerShell/CMD session on the real Windows host, with local Windows paths and the Windows Python `py` launcher.

## Windows host prerequisites and installation

Prerequisite tools on the real Windows host:

- `winget` (optional install helper)
- Python 3.12 (`python.exe`)
- `uv` (`uv.exe`)

Example install commands on Windows (if missing):

```powershell
winget install -e --id Python.Python.3.12
winget install -e --id astral-sh.uv
```

If the Windows Python Launcher (`py.exe`) is unavailable, the project can use the direct Python and `uv` paths instead of `py -3.12`. In that case:

- Python 3.12: direct path to `python.exe`
- `uv`: direct path to `uv.exe`

Verification using direct paths:

```powershell
& '<Python312>\python.exe' --version
& '<uv>\uv.exe' --version
```

## Environment creation

Create the project environment only after the host and tooling are verified on the real Windows host:

```powershell
uv venv --python 3.12
```

If `uv` is not on PATH, use the direct `uv.exe` path:

```powershell
& '<uv>\uv.exe' venv --python '<Python312>\python.exe' .venv
```

This should create a Windows-local `.venv` that:

- runs on Windows;
- uses Python 3.12;
- does not depend on any Linux path.

## Verification checklist (Phase 2)

- Confirm the working session is on a real Windows host, not WSL, and not a `/home/...` path.
- Confirm Python 3.12 and `uv` are available (directly or on PATH).
- If `py.exe` is unavailable, use the direct Python 3.12 and `uv` paths.
- Create `.venv` using `uv venv --python 3.12` (or the direct `uv.exe` path if needed).
- Verify `.venv` uses Python 3.12 on Windows.
- Verify `.venv` is inside `.gitignore`.

## Explicit out-of-scope constraints for Phase 2

- No `pip freeze`.
- No pip-tools as a substitute.
- No `uv sync`.
- No `uv.lock` generation in this phase.
- No edits to `pyproject.toml` or any `requirements*.txt` in this phase.
- No project dependency installation.
- No cTrader connection.
- No reading, displaying, or copying of `.env`.
- No Git history changes, reset, checkout, or clean.
- No deletion of other project files.

## Note on `uv.lock`

`uv.lock` will be created only during Phase 3 (package unification), after Phase 2 verification is approved.

