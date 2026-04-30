# 7: Metadata cleanup, IDE root dirs, and staging temp pruning

IMPORTANT: always use `spawn/navigation.yaml` and `spec/main.md` for rules.

## Status

- [x] Spec created
- [x] Self spec review passed
- [x] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [x] Code review passed
- [x] HLA updated

## Goal

Ensure Spawn removes IDE-specific metadata under `spawn/.metadata/<ide>/` when an IDE is removed, prunes Spawn-managed directories at the **repository root** for that IDE using **explicit vacancy checks** (`mcp.json` reduced to empty server map → unlink; IDE root folder empty → **delete the folder entirely**, e.g. `.cursor`), and prevents unbounded accumulation of orphaned UUID staging directories under `spawn/.metadata/temp/`.

## Design overview

- Affected modules: `spawn_cli.core.high_level.remove_ide`, `spawn_cli.ide.registry.IdeAdapter` and each IDE adapter (`finalize_repo_after_ide_removed`), `spawn_cli.core.low_level` (path removal / temp prune helpers), `spawn_cli.core.download._stage_extension`; CLI unchanged unless Details require otherwise.
- Data flow changes: On `spawn ide remove <ide>`, finish per-extension `remove_mcp` / `remove_skills`, then IDE `remove_agent_ignore`, then call adapter `finalize_repo_after_ide_removed` to prune leftover root dirs, then update `ide.yaml`, then remove `spawn/.metadata/<ide>/`. Separately: stale staging entries under `spawn/.metadata/temp/` are pruned on each staging run (best-effort, non-fatal).
- Integration points: `remove_ide`; `_stage_extension` / `StagedExtension.cleanup`; adapter tests alongside `tests/core/` and `tests/ide/`.

## Before To After

### Before

- `remove_ide` clears rendered skills/MCP in the IDE workspace and updates `ide.yaml` but leaves `spawn/.metadata/<ide>/` (rendered YAML, `agent-ignore.txt`, etc.).
- **Repository root** leftovers remain: empty shells such as `.cursor` after skills removal and MCP files left effectively empty (`"mcpServers": {}`).
- UUID directories under `spawn/.metadata/temp/` can linger after aborted runs, crashed processes, or platform-specific delete failures despite `finally: staged.cleanup()`.

### After

- After a successful `remove_ide`, the directory `spawn/.metadata/<ide>/` is absent (or empty only transiently during the operation).
- **Vacant** Spawn-managed IDE root trees are removed according to adapter-specific guarded rules (`finalize_repo_after_ide_removed`); adapters sharing roots with unrelated tooling (`/.github`, `/.vscode`) never wipe those trees wholesale (see Details).
- Orphan staging directories under `spawn/.metadata/temp/` are pruned on a defined policy so normal use does not grow `temp/` without bound.

## Details

Assumptions and defaults (blocking questions none; revise if product wants a user-facing command):

1. **IDE metadata path** — Canonical tree is `_spawn(target_root) / ".metadata" / ide` where `ide` matches the slug used in `ide.yaml` and `spawn/.metadata/<ide>/rendered-*.yaml` (see `_rendered_skills_path` in low_level). Removing this directory after tear-down supersedes file-by-file deletion of rendered stores and agent-ignore lists.

2. **Ordering** — Read `get_agent_ignore_list` and rendered YAML from metadata **before** `remove_*` adapters as today. Call `finalize_repo_after_ide_removed` **after** those removals and **before** removing the IDE from `ide.yaml` and removing `spawn/.metadata/<ide>/`.

3. **Shared roots** — For GitHub Copilot and similar, **never** `rmtree(".github")` or `rmtree(".vscode")`; vacancy-prune only Spawn-owned subtrees (for example `/.github/skills`) and apply the same MCP JSON vacancy rules cautiously via `finalize_repo_after_ide_removed`.

4. **User content** — If a directory holds files Spawn did not lay down (Cursor user `.cursor/rules/`), finalization MUST leave those paths untouched and MUST NOT delete the ancestor.

5. **Vacancy predicates and deleting the whole IDE folder** — Finalization MUST use deterministic checks (aligned with subtask **`_DONE_3-remove-ide-managed-repo-roots`**): treat MCP JSON as removable when configured server maps are empty (`mcpServers` absent/null/`{}` for Cursor-like files, document-level `{}`), then unlink when true; prune empty child dirs bottom-up; if the IDE root passes "removable with no unrelated files left", **`rmtree` that root** (Cursor `.cursor`, Gemini `.gemini`, etc.). Shared roots (`.github`, `.vscode`): never delete the hub directory as a whole; only unlink vacancy MCP paths and Spawn-only subtrees when empty.

6. **MCP merged files caveat** — User-defined servers merged under shared keys cannot be told apart from Spawn-rendered entries without ownership metadata; predicates still unlink when objective emptiness applies.

7. **Temp pruning policy** — Prune **only** under `spawn/.metadata/temp/`, **only** subdirectory names parsing as UUIDs (same convention as `_stage_extension` uses for `op`), older than **24 hours** (mtime). Skip entries that fail `rmtree`; optionally warn once per prune pass. Invoke from `_stage_extension` after resolving `temp_base.parent` before heavy staging IO. Exclude the staging UUID directory for the active operation.

8. **Concurrency** — Prune remains best-effort; tolerate races, missing paths, and `PermissionError`.

9. **Tests** — Metadata dir absent after `remove_ide`; Cursor `.cursor` removed on Spawn-only layout; negative fixture with extra subtree under `.cursor` preserving ancestor; timing-based temp pruning as before.

10. **Out of scope** — New `spawn clean`; changing gitignore for temp wholesale; rewriting `spec/design/ide-adapters.md` unless Step 7 needs a one-line behaviour note only.

## Execution Scheme

> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.

- Phase 1 (sequential): step `_DONE_3-remove-ide-managed-repo-roots` -> step `_DONE_1-remove-ide-metadata-dir` -> step `_DONE_2-prune-metadata-temp`
- Phase 2 (parallel): (none)
- Phase 3 (sequential): step review — inspect all changes, fix inconsistencies
