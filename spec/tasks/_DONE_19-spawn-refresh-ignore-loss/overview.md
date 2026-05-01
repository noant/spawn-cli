# 19: Split core vs extension agent-ignore refresh

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
Split agent-ignore refresh into **core** and **extensions** with separate managed regions in IDE ignore files, compose them in one orchestrator, and use that orchestrator everywhere agent-ignore must be refreshed.

## Design overview
- Affected modules: `spawn_cli.core.high_level` (new split entrypoints, single orchestrator, all call sites), `spawn_cli.core.low_level` (ext-only persistence for `agent-ignore` metadata, helpers to list extension merge without core), `spawn_cli.ide._helpers` (partition/rewrite per block kind), native-ignore IDE adapters (`cursor`, `windsurf`, `gemini_cli`, registry contracts if needed), `tests/core/`, `tests/ide/`.
- Data flow changes: **Core** globs come only from `spawn/.core/config.yaml` after any preceding `sync_core_config_from_defaults`; the IDE file gets a **dedicated Spawn block** rewritten in full on each refresh (no idempotency file slice for core). **Extension** globs come from merged `spawn/.extend/*/config.yaml` `agent-ignore`; the IDE file gets a **second Spawn block** updated using ext-only idempotency in `spawn/.metadata/{ide}/agent-ignore.txt` (contents = last rendered extension merge only) or equivalent renamed file. **`refresh_agent_ignore(ide)`** = `refresh_core_agent_ignore(ide)` then `refresh_extension_agent_ignore(ide)` (order fixed in spec; document in code).
- Integration points: `spec/design/utility.md`, `spec/design/data-structure.md`, `spec/design/ide-adapters.md` — managed blocks, ownership, uninstall semantics; `remove_ide` / `remove_extension_for_ide` must remove or reconcile both regions and metadata consistently.

## Before → After
### Before
- One `# spawn:start` … `# spawn:end` region and one combined list in `agent-ignore.txt`. `remove_ignore_block(..., [])` removes the entire region; `refresh_agent_ignore` passes empty diffs when `old == new`, wiping ignores. Core and extension globs are merged in one metadata list.

### After
- Two regions, e.g. `# spawn:core:start` … `# spawn:core:end` and `# spawn:ext:start` … `# spawn:ext:end` (exact marker strings implemented once in `_helpers` and documented for adapters).
- `refresh_core_agent_ignore` / `refresh_extension_agent_ignore` are separate public (or package-internal) operations; `refresh_agent_ignore` is the **only** composition used by `refresh_repository`, `add_ide`, `_refresh_extension_core`, `refresh_extension_for_ide`, and any other path that today calls `refresh_agent_ignore`.
- `remove_extension_for_ide` stops using the combined merge + combined metadata diff; it updates **extension** block and ext-only metadata (core block untouched).
- `remove_ide` clears **both** Spawn regions for that IDE and removes IDE metadata (including ext idempotency file).
- Regression tests cover: no-op full refresh with stable configs (core + ext blocks unchanged), extension-only remove, core sync then refresh (core block matches bundled `default_core_config.yaml`), and migration or first-run handling for repos that still have the legacy single block.

## Details
- **API shape (high_level):** Add `refresh_core_agent_ignore(target_root, ide)` and `refresh_extension_agent_ignore(target_root, ide)`. Implement `refresh_agent_ignore` as a thin orchestrator calling both in order; **do not** duplicate orchestration at call sites. Callers that today invoke `refresh_agent_ignore` stay on the orchestrator only. **`remove_extension_for_ide`** must call the extension refresh path (or orchestrator minus core — prefer a single code path that cannot forget core when inappropriate: for extension removal, only extension half + ext metadata).
- **Adapter contract:** Native-ignore IDEs rewrite two blocks via shared helpers (preferred) or minimal extra methods; Copilot/CodeX stubs remain no-ops. No empty-list “delete entire file region” for the **refresh** path: core refresh is always “write desired core globs into core region”; extension refresh uses explicit diff against **ext-only** prior state or full replace of ext region if spec chooses full replace (if full replace, metadata optional — default in this spec: **keep ext idempotency file** for extension half only).
- **Metadata:** `spawn/.metadata/{ide}/agent-ignore.txt` stores **only** the merged extension ignore list (not core). On first migration from legacy, treat missing ext metadata as empty and derive extension block from configs; legacy combined file may need one-time split (document behavior if old file listed core+ext lines).
- **Init:** `ll.init` does not configure IDEs; `add_ide` and full refresh already hit the orchestrator. If any code path must materialize ignores without `add_ide`, it must use the same orchestrator (verify `spawn init` / CLI and add calls if gaps exist).
- **Out of scope for this task:** `refresh_gitignore` split core vs extension (core `git-ignore` in `CoreConfig` is a separate follow-up unless the same PR is trivial).
- **Docs/tests:** Update design snippets for dual blocks; add tests that use real `rewrite_*` paths (not only stub IDE) for at least Cursor or `_helpers` unit tests.

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `1-helpers-and-adapters` → step `2-low-level-metadata` → step `3-high-level-wire-and-tests`
