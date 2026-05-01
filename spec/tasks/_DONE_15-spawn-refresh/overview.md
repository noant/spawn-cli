# 15: Top-level `spawn refresh` (core config + full render)

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
Add a top-level `spawn refresh` command that syncs `spawn/.core/config.yaml` from the bundled default policy, then rebuilds all IDE-facing Spawn outputs (skills, MCP, agent ignore, navigation including rules, gitignore metadata, entry points) in one locked invocation.

## Design overview
- Affected modules: `spawn_cli.cli` (new subparser and dispatch), `spawn_cli.core.low_level` (core config merge/write helper), `spawn_cli.core.high_level` (orchestration entrypoint reusing existing refresh primitives), `tests/` (coverage for merge + command), `spec/design/utility.md` (command documentation in Step 7 if needed per methodology — register as design touch in subtasks).
- Data flow changes: On `spawn refresh`, load bundled `default_core_config.yaml`, merge into existing `CoreConfig` on disk (see Details), persist, then run a single full-repository refresh pass equivalent to refreshing every installed extension without running extension setup scripts.
- Integration points: Existing `refresh_mcp`, `_refresh_skills_all_extensions_for_ide`, `refresh_agent_ignore`, `refresh_gitignore`, `refresh_navigation`, `refresh_entry_point`; MCP notice batching pattern from `add_ide` (merge across extensions, print `MCP_MERGED_NOTICE` at most once).

## Before → After
### Before
- `spawn init` creates `spawn/.core/config.yaml` only when missing; upgrading the CLI never updates an existing file.
- Authors run `spawn rules refresh` for rules-only navigation updates, or trigger full IDE rebuilds via extension lifecycle commands (`extension add` / `update` / `reinstall`, which call `_refresh_extension_core`); there is no dedicated one-shot "sync core defaults and repair everything" command.
### After
- `spawn refresh` (after `spawn init`) updates core config from the package default policy, then re-renders skills, MCP, agent-ignore, merged navigation (extensions + rules), gitignore lists, and entry points for every IDE in `spawn/.metadata/ide.yaml`, under the usual non-blocking repository lock. Documented in `spec/design/utility.md`; architecture notes in `spec/design/hla.md`.

## Details
- **CLI shape:** Top-level subcommand `refresh` with no nested subcommands (distinct from `spawn rules refresh`). Help text states that it syncs core config and rebuilds rendered IDE metadata.
- **Preconditions:** Same as other mutating commands: `spawn/` must exist (`SpawnError` with `need init before` otherwise). Acquire `spawn_lock` for the whole handler.
- **Core config merge policy:** Load current `spawn/.core/config.yaml` via `load_yaml`. Load bundled template from `spawn_cli.resources.default_core_config.yaml`. Parse both through `CoreConfig` (invalid existing file → `SpawnError` with a clear message). `version` in the written file is set to the **bundled default** `version` (tracks the schema/package line). **`agent-ignore`:** ordered union — first all entries from the bundled default in resource order, then any entries present in the existing repo file that are **not** in the default list (preserve user-added globs). Write the result with existing YAML helpers (`save_yaml` / same style as other config writes). Unknown top-level keys are **not** in `CoreConfig` today; Pydantic validation ignores extras on read, and the written file contains only `version` and `agent-ignore` unless `CoreConfig` is extended in the same change-set.
- **Full refresh semantics:** Do **not** run extension `before-install` / `after-install` scripts (unlike `refresh_extension`). Implement a dedicated orchestrator (e.g. `refresh_repository`) that:
  1. Merges and saves core config as above.
  2. Emits IDE capability warnings once per IDE using aggregated predicates: `needs_skill_render = _any_extension_has_skill_files`, `needs_mcp_merge = _any_extension_has_mcp_servers` (same idea as `add_ide`).
  3. For **each** IDE in `list_ides`: for **each** installed extension, call `refresh_mcp(..., emit_mcp_merged_notice=False)`; then call `_refresh_skills_all_extensions_for_ide` **once** for that IDE (same structure as `_refresh_extension_core`, but the MCP inner loop covers **all** extensions). Track whether **any** `refresh_mcp` returned a non-empty server-name list across the whole command; after step 4, print `MCP_MERGED_NOTICE` **at most once** if that flag is set.
  4. For **each** IDE: `refresh_agent_ignore`.
  5. `refresh_gitignore` once.
  6. `refresh_navigation` once (includes `save_rules_navigation` per existing `refresh_navigation` behavior — rules stay in sync without requiring a separate `spawn rules refresh`).
  7. For **each** IDE: `refresh_entry_point`.
- **Idempotence:** Re-running `spawn refresh` converges to the same rendered state as other refresh paths; no duplicate metadata when inputs are unchanged.
- **Tests:** Unit tests for core-config merge (default-only file, user extra ignore lines preserved, version bumped from default). Integration-style test with `tmp_path`: init, tweak core config, run refresh orchestrator entry (or CLI main), assert merged config and that refresh helpers were invoked / state consistent (mirroring patterns in existing `tests/core`).

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `_DONE_1-core-config-and-refresh-orchestration` → step `_DONE_2-cli-and-tests`
