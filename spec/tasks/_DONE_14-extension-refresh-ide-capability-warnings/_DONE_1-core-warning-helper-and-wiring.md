# 1: Core warning helper and wiring

## Goal
Centralize Spawn capability-gap warnings and invoke them from `add_ide`, `_refresh_extension_core`, and `refresh_extension_for_ide` without changing adapter contracts.

## Approach
1. Implement `_warn_capability_gaps(...)` beside related orchestration helpers in `high_level.py`; keep messages identical to existing `add_ide` literals when emitted.
2. Compute `needs_skill_render` via one pass over `low_level.list_extensions` using `list_skills` emptiness checks (cheap, mirrors render intent without duplicating `generate_skills_metadata` merges).
3. Compute `needs_mcp_merge` with `bool(low_level.list_mcp(target_root, extension).servers)` respecting each entry point’s scope described in `overview.md`.
4. Replace inline `warnings.warn(...)` capability checks in `add_ide` with the helper guarded by booleans computed for the freshly registered IDE scenario (skills: any extension has skill files; MCP: any extension has non-empty `list_mcp(...).servers` before the per-extension `refresh_mcp` loop). Note today `refresh_entry_point` runs between the old capability warnings and MCP refresh; predicates stay unchanged even if reorder is avoided.
5. At the beginning of `_refresh_extension_core`, before MCP loops: for **each IDE in `list_ides`**, compute booleans once and call `_warn_capability_gaps`. For `refresh_extension_for_ide` (**single IDE argument**): call the helper once for that IDE with MCP boolean from the named `extension` only and aggregate skills flag across all extensions.
6. Ensure warning category remains `SpawnWarning` so stderr formatting hooks continue to prefix `spawn: warning:` text.

## Affected files
- `src/spawn_cli/core/high_level.py`

## Verification hints (no automated run required here)
- Manual trace: `_refresh_extension_core` emits no capability warnings when all extensions omit skills/MCP but still rebuilds ignores/navigation unaffected.
