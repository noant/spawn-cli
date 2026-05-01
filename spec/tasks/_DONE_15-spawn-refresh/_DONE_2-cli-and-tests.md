# Subtask 2: CLI wiring, documentation touch, tests

## Goal
Expose `spawn refresh` on the CLI and add tests for core-config merge and the new command path.

## Approach
- In `spawn_cli.cli.build_parser`, add a top-level `refresh` subparser with short and long description consistent with `overview.md`.
- In `_dispatch`, handle `command == "refresh"` after `_require_init`, inside the existing `spawn_lock` context, calling the new high-level orchestrator.
- Add tests under `tests/` (e.g. `tests/core/test_refresh_repository.py` or extend an existing module): merge policy tests; CLI or orchestrator test with `tmp_path` and mocked/low-friction assertions following project patterns.

## Affected files
- `src/spawn_cli/cli.py`
- `tests/` (one or more new or extended test modules)

## Documentation
- During Step 7, update `spec/design/utility.md` **Public Commands** with `spawn refresh` semantics (mirror the style of `spawn rules refresh`: init required, lock, what mutates). If `spec/main.md` Step 7 also updates `hla.md`, mention the new command briefly there.
