# 13: Re-render all extension skills when the extension set changes

## Source seed
- Path: none

## Status
- [V] Spec created
- [V] Self spec review passed
- [V] Spec review passed
- [V] Code implemented
- [V] Self code review passed
- [V] Code review passed
- [V] HLA updated

## Goal
When an extension is installed, updated, removed, or otherwise refreshed through the orchestration path that rebuilds navigation, rendered IDE skills for **every** installed extension must be regenerated so merged global (and cross-extension) mandatory reads stay correct.

## Design overview
- Affected modules: `spawn_cli.core.high_level` (primary: `_refresh_extension_core`, `remove_extension`, optionally `refresh_extension_for_ide`); tests under `tests/core/`.
- Data flow changes: Skill metadata is built with `merged_global_required` / `merged_global_auto` from **all** extensions (`low_level.generate_skills_metadata`). Navigation already reflects all extensions after `refresh_navigation`; rendered skills for extension A must be rewritten when extension B adds or removes globally visible files, not only when A’s own config changes.
- Integration points: `install_extension`, `update_extension`, `refresh_extension` (all use `_refresh_extension_core`); `remove_extension` (must refresh survivors’ skills after the removed extension’s rendered assets and `.extend` tree are gone); `add_ide` already loops all extensions for `refresh_skills`—no behavior regression expected there.

## Before → After
### Before
- `_refresh_extension_core` calls `refresh_mcp` and `refresh_skills` only for the **single** extension argument. `refresh_navigation` rebuilds the merged index for all extensions, but other extensions’ rendered skills keep stale mandatory/contextual read lists.
- `remove_extension` removes rendered skills for the removed extension only; remaining extensions’ skills are not rewritten when a contributor of global reads disappears.

### After
- After any MCP merge for the **target** extension, **each** initialized IDE re-renders skills for **every** currently installed extension (deterministic order, e.g. `sorted(ll.list_extensions(...))` if the list is not already ordered).
- `remove_extension`: after `spawn/.extend/{ext}` is removed and navigation/rules/gitignore/agent-ignore/entrypoints are updated, re-run the same “all extensions × all IDEs” skill refresh for **remaining** extensions so dropped global reads disappear from peer skills.
- `refresh_extension_for_ide`: keep MCP scoped to the named extension; extend `refresh_skills` to all installed extensions for that IDE so a narrow API does not leave peers stale (document in docstring).

## Details
- **Why**: Per `spec/design/agentic-flow.md`, each skill’s mandatory reads include skill-specific entries, extension-local required reads, and **all** `globalRead: required` files across extensions. Adding an extension can introduce new global mandatory files; removing one can remove them. Only re-rendering the changed extension’s skills is insufficient.
- **MCP**: Cross-extension merge is per-server definitions from each extension; re-running `refresh_mcp` for unrelated extensions on every install is not required by this task. Scope stays: refresh MCP for the extension(s) the current operation owns; refresh **skills** for all.
- **`validate_rendered_identity`**: Already invoked inside `refresh_skills`; full skill refresh may call it repeatedly—acceptable unless profiling says otherwise; no change required unless tests or code clarify a single batched validation.
- **Helpers**: Prefer one internal helper (e.g. `_refresh_skills_all_extensions_for_ide` / `refresh_skills_all_extensions`) to avoid duplicating loops in `_refresh_extension_core` and `remove_extension`.
- **Design doc note**: In Step 7, align `spec/design/utility.md` “Rebuild Semantics” / refresh-extension narrative with “skills: all extensions; MCP: affected extension(s)” if the text currently implies a single-extension skill refresh only.

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `_DONE_1-core-orchestration.md` → step `_DONE_2-tests.md`
