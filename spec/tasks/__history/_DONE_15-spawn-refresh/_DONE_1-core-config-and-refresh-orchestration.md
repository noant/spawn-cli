# Subtask 1: Core config merge and full refresh orchestration

## Goal
Implement merging of `spawn/.core/config.yaml` with bundled defaults and a `refresh_repository` (name may match codebase naming) entry in `high_level` that performs the full IDE/metadata refresh described in `overview.md`.

## Approach
- Add a low-level function (e.g. `merge_core_config_from_defaults` or `refresh_core_config`) that reads the repo file and resource template, applies the ordered-union policy for `agent-ignore`, sets `version` from the default, validates with `CoreConfig`, and writes back.
- Add `refresh_repository` in `high_level` that calls the low-level merge first, then orchestrates MCP (batched notices), skills, agent-ignore, gitignore, navigation, entry points per `overview.md`. Reuse `_warn_capability_gaps` with aggregated needs flags.
- Export new symbols from `high_level.__all__` if the module maintains an explicit export list.

## Affected files
- `src/spawn_cli/core/low_level.py`
- `src/spawn_cli/core/high_level.py`

## Notes
- Avoid running `scripts.run_before_install_scripts` / `run_after_install_scripts` inside this path.
- Keep ordering consistent with `spec/design/utility.md` refresh ordering (validate before mutate; existing helpers already encode phases).
