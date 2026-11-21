# 14: Warn on IDE capability gaps during extension-driven refresh

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
Emit the same Spawn capability-gap warnings as `add_ide` whenever extension work triggers IDE refresh, but only when skipped skills or MCP would have mattered for the current operation.

## Design overview
- Affected modules: `spawn_cli.core.high_level` (primary: shared warning helper, `add_ide`, `_refresh_extension_core`, `refresh_extension_for_ide`); tests under `tests/core/`.
- Data flow changes: Before adapter refresh, the utility calls `detect()` (or reuses `DetectResult` semantics) and emits `SpawnWarning` when `IdeCapabilities` indicate a gap **and** relevant extension metadata is non-empty; no new files under `spawn/` metadata.
- Integration points: IDE registry (`ide_get` + `IdeAdapter.detect`), `low_level.list_extensions`, `low_level.list_skills` / `low_level.list_mcp`, existing `spawn_cli.warnings_display` formatting for `SpawnWarning`.

## Before → After

### Before
- `spawn ide add` warns when `capabilities.skills == "unsupported"` or `capabilities.mcp` is `unsupported` or `external`, even if no extensions are installed (no skills/MCP to merge).
- `install_extension`, `update_extension`, `refresh_extension`, and related paths call `_refresh_extension_core` without those centralized warnings; operators only see adapter-local noise (if any).

### After
- One internal helper centralizes capability-gap warnings keyed off `IdeCapabilities`, reused from `add_ide` and from extension-driven refresh entry points (`_refresh_extension_core`, `refresh_extension_for_ide`).
- Warnings fire only when:
  - **Skills:** `skills == "unsupported"` and at least one installed extension exposes non-empty skill metadata for rendering (non-empty skill tree under `spawn/.extend/{ext}/skills` backing `generate_skills_metadata`, mirroring practical “something would be skipped” behavior).
  - **MCP:** `mcp` in (`unsupported`, `external`) and the merged MCP operation would touch at least one server for the relevant extensions (`low_level.list_mcp` returns `NormalizedMcp` with non-empty `servers` for the extension arguments actually refreshed in that call path).
- `add_ide` adopts the same conditional rules so an empty repo does not emit misleading “skills were skipped” / “limited MCP” lines.

## Details
- **Single helper** (example name `_warn_capability_gaps`) takes `target_root`, IDE key string, fresh `DetectResult` from `adapter.detect(target_root)`, and two booleans: `needs_skill_render`, `needs_mcp_merge`. Messages must match existing `add_ide` wording so UX stays stable when conditions are satisfied.
- **`_refresh_extension_core(target_root, extension)`:** For each registered IDE from `list_ides`, evaluate `needs_skill_render` as “any installed extension has skills to render”; evaluate `needs_mcp_merge` as `bool(list_mcp(target_root, extension).servers)` **for the extension argument of this refresh** only (MCP loops stay scoped per current code).
- **`refresh_extension_for_ide(target_root, ide, extension)`:** MCP boolean uses only the named `extension`; skills boolean uses merged “any extension has skill files” scope because this path re-renders all extensions’ skills on that IDE (same rationale as `_refresh_skills_all_extensions_for_ide`).
- **Out of scope:** `remove_extension` (cleanup path), granular per-adapter stubs beyond unified warnings, changes to MCP merge notice semantics (`MCP_MERGED_NOTICE`).
- **`spec/design/ide-adapters.md`:** During Step 7 (unless pulled into this task explicitly), tighten prose so “once at IDE registration time” aligns with extension-driven refresh emitting the shared warnings (`spec/design/ide-adapters.md` presently states registration-only for some bullets while also expecting refresh-path warnings elsewhere).

## Execution Scheme

> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `1-core-warning-helper-and-wiring` → step `2-tests`
