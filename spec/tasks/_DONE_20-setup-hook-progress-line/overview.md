# 1: Setup hook progress line on stderr

## Source seed
- Path: none

## Status
- [x] Spec created
- [x] Self spec review passed
- [x] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [x] Code review passed
- [x] Design documents updated

## Goal
Print a clear, single-line status message immediately before each extension setup hook subprocess runs (phase + script file name).

## Design overview
- Affected modules: `spawn_cli.core.scripts` (all paths that run `setup/*.py` via subprocess); tests under `tests/core/test_scripts.py` (and any test that asserts on hook output, if added elsewhere).
- Data flow changes: none; only user-visible stdout/stderr behavior before existing `subprocess.run` calls.
- Integration points: callers of `run_*_install/uninstall` scripts and `run_healthcheck_scripts` remain unchanged; behavior is localized to `scripts.py`.

## Before → After
### Before
- Setup hooks run with no announcement; the CLI shows nothing until a warning or error appears.

### After
- Before each configured hook (and before healthcheck script execution), the CLI prints one line naming the setup phase and the script file name (e.g. `before-install` and `bootstrap.py`), using English text per project conventions.

## Details
- **Channel**: Print informational lines to **stderr** so they align with other user-facing CLI status (`spawn_cli.warnings_display`, errors in `cli.py`) and do not pollute stdout (which may be parsed by scripts).
- **Phases and wording**: Use the same phase labels as in `config.yaml` keys, in order:
  - `before-install`, `after-install`, `before-uninstall`, `after-uninstall`, `healthcheck`.
- **Line shape** (exact string for implementation): `spawn: running {phase} script: {filename}` where `{filename}` is the basename only (as declared in config, e.g. `bootstrap.py`).
- **Coverage**:
  - All invocations that go through `_run_script` should emit the line once per run (parameterize `_run_script` with `phase: str` or print in each public entrypoint before calling `_run_script` — either is fine if duplication stays minimal).
  - `run_after_uninstall_from_snapshot` must print for `after-uninstall` using `snap.script_path.name` before `subprocess.run`.
- **When not to print**: If a phase is skipped (no script configured, or early return such as missing layout in `run_after_uninstall_scripts`), do not print.
- **Tests**: Extend `tests/core/test_scripts.py` so that when `subprocess.run` is patched, at least one test asserts stderr contains the expected `spawn: running before-install script: hook.py` (or cap equivalent). Keep existing failure/skip behavior tests valid.

## Execution Scheme
> Single cohesive change in one module + tests; no subtask split.
