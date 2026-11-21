# Step 2: Messages and tests

## Goal

Align warning copy with end users and lock behavior with tests.

## Approach

- Sweep all `warnings.warn(..., SpawnWarning)` (and any aligned IDE/static paths switched to `SpawnWarning` in step 1) and rewrite messages: short, clear, no stack-like or developer-only phrasing.
- At minimum, update the static file overwrite message in `download.py` to match the new tone.
- Add tests: subprocess running `python -m spawn_cli` (or equivalent) with a scenario that triggers a `SpawnWarning`, or unit-test the formatter with a controlled `warnings.warn`; assert stderr/on-hook output matches `spawn: warning:` and does not contain `.py:` line references or the substring `SpawnWarning`.

## Affected files

- `src/spawn_cli/core/download.py`, `high_level.py`, `low_level.py`, `scripts.py`, and any other `SpawnWarning` producers after grep.
- `tests/` — new or extended test module.
