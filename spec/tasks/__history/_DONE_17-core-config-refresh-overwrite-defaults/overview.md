# 17: Core config refresh overwrites bundled defaults

## Source seed
- Path: none

## Status
- [x] Spec created
- [x] Self spec review passed
- [x] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [x] Code review passed
- [x] HLA updated

## Goal
Make `spawn refresh` rewrite `spawn/.core/config.yaml` to match the bundled default file exactly so defaults can shrink or change without stale patterns accumulating in the repo file.

## Design overview
- Affected modules: `spawn_cli.core.low_level` (`sync_core_config_from_defaults`), `spawn_cli.core.high_level` (refresh orchestration), `tests/core/test_low_level.py`, `spawn_cli.cli`, `spec/design/utility.md`, `spec/design/hla.md`.
- Data flow changes: On full-repository refresh, after validating that `spawn/.core/config.yaml` exists and parses as `CoreConfig`, replace its contents with the validated model loaded from `default_core_config.yaml` (same fields and ordering as the resource file). No union with prior `agent-ignore` entries.
- Integration points: `refresh_repository` continues to call the same low-level entrypoint; `spawn init` unchanged (still writes template when missing).

## Before → After
### Before
- `merge_core_config_from_defaults` (task 15) kept `agent-ignore` as bundled defaults **plus** any existing patterns not in the default set; removed-from-default globs lingered.

### After
- `sync_core_config_from_defaults` writes **only** the bundled `CoreConfig` after validating the existing file parses. Repository-local edits to `.core/config.yaml` are **not** preserved across `spawn refresh`. Extra ignore globs belong in extension-level `agent-ignore`.

## Details
- **Validation:** If the file is missing, empty, or invalid `CoreConfig`, keep existing `SpawnError` behavior (user must fix or re-run `init`). If the bundled resource is invalid, keep internal error behavior.
- **Naming:** Prefer renaming the function to a name that reflects overwrite semantics (e.g. `sync_core_config_from_defaults` or `overwrite_core_config_from_defaults`) and update `high_level` import + `__all__` in `low_level` if present; avoid keeping a misnamed `merge_*` that no longer merges.
- **Tests:** Replace the current merge test that expects `custom/glob/**` to survive with an assertion that after refresh, `agent-ignore` and `version` match the bundled default only. Add a case where the pre-refresh file contains extra patterns and they are **absent** after sync. Keep invalid/empty file tests; adjust messages only if implementation changes.
- **User-facing copy:** CLI `refresh` subparser help/description must no longer say `Merge`; describe **overwrite** / **replace with bundled defaults** consistently with `utility.md`.
- **Out of scope:** A second file for “user core overrides” is not part of this task.

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `_DONE_1-low-level-and-tests` → step `_DONE_2-cli-and-utility-docs`
