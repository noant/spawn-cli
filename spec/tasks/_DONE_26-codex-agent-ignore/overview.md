# 26: Codex agent-ignore support via permission profiles

## Source seed
- Path: spec/seeds/4-codex-agent-ignore.md

## Status
- [V] Research [GLM-5.3, Kimi-k3, GLM-5.3]
- [V] User research review
- [V] Spec drafting [GLM-5.3-flash]
- [V] Spec self-review [GLM-5.3]
- [V] Spec review
- [V] Code implementation [GLM-5.3-flash]
- [V] Code self-review [GLM-5.3]
- [V] Code review / debugging
- [V] Design document update [GLM-5.3-flash]

## Goal
Make spawn-managed agent-ignore entries actually apply to Codex targets by writing deny rules into the `.codex/config.toml` permission profile.

## Motivation
new feature — spawn-managed ignore (core + extensions, `ll.get_all_agent_ignore`) currently silently does nothing for codex; Codex now ships beta permission profiles that can enforce deny rules, so the capability gap can be closed.

## Invasiveness level
medium-invasive — adapter + vacancy cleanup + tests; adjacent `core/high_level.py` needs no changes (its `project` branch already works), `cli.py` untouched unless spec self-review requires it.

## Research summary
- No `.codexignore` exists (openai/codex #6530, #24993 open); feature request #2847 closed as completed via beta permission profiles: `[permissions.<name>.filesystem.":workspace_roots"]`, `"path" = "deny"`, activated by `default_permissions = "<name>"`.
- `default_permissions` and `sandbox_mode` are mutually exclusive; naive write makes rules inert (user with `sandbox_mode`) or degrades their sandbox (project file overrides global `default_permissions`). Decision (user): never write `default_permissions`; write spawn-namespaced profile `[permissions.spawn]` with `extends = ":workspace"`; warn when `sandbox_mode` present; user activates manually with `default_permissions = "spawn"`.
- `.gitignore` is respected only for file discovery (@-picker), bypassed via shell — rejected.
- Protocol facts: registry methods are `add_agent_ignore` / `remove_agent_ignore` (+ optional hooks `rewrite_core_agent_ignore` / `rewrite_extension_agent_ignore` / `clear_spawn_agent_ignore`, default no-op). `core/high_level.py`: `refresh_core_agent_ignore` (L92) branches on `native` vs `project` -> `_sync_project_agent_ignore_permissions` (L79) which diffs `spawn/.metadata/<ide>/agent-ignore.txt`. Claude Code precedent: `claude_code.py` L103-137 (`agent_ignore="project"`, permissions.deny in settings.json, `clear_spawn_agent_ignore` via state file).
- Writers of `.codex/config.toml`: `codex.py add_mcp/remove_mcp` (load_toml/save_toml) and `_vacancy.finalize_codex_repo` (L176-196, deletes file only when keys <= {mcp_servers} and empty). `permissions` coexists with `mcp_servers` (separate top-level keys); `save_toml` rewrites the whole file (existing accepted behavior).
- Glob strings are used verbatim as TOML keys (1:1 compatible); tomli_w handles quoting (verified empirically: produces `[permissions.spawn.filesystem.":workspace_roots"]` with quoted glob keys, round-trips).
- Known Codex limits: Desktop ignores project `default_permissions` (#22553); Windows needs Codex > 0.108.0-alpha.8 (apply_patch regression #13574).
- Reports reviewed by A4-reviewer (GLM-5.3): facts verified against repo, no contradictions.

## Design overview
- Affected modules: `spawn_cli.ide.codex` (CodexAdapter), `spawn_cli.ide._vacancy` (finalize_codex_repo), tests for both.
- Files & symbols:
  - `src/spawn_cli/ide/codex.py` — `CodexAdapter.detect` (capabilities), new module constant `SPAWN_PERMISSIONS_PROFILE = "spawn"`, `CodexAdapter.add_agent_ignore`, `CodexAdapter.remove_agent_ignore`, new `CodexAdapter.clear_spawn_agent_ignore`.
  - `src/spawn_cli/ide/_vacancy.py` — `finalize_codex_repo`.
  - `tests/ide/test_codex.py` — replace `test_add_agent_ignore_warns` (L157-162), `test_remove_agent_ignore_warns` (L165-169), update `test_detect_with_codex_dir` L24.
  - `tests/ide/test_vacancy.py` (new file; no vacancy tests exist today) — config.toml cleanup cases with `permissions`.
- Data flow changes: with cap=`project`, `refresh_core_agent_ignore`/`refresh_extension_agent_ignore` now call `_sync_project_agent_ignore_permissions` -> diff vs state file `spawn/.metadata/codex/agent-ignore.txt` -> adapter add/remove -> deny entries under `[permissions.spawn.filesystem.":workspace_roots"]` in `.codex/config.toml`. `spawn ide remove codex` -> `clear_spawn_agent_ignore` + `finalize_codex_repo` removes the spawn subtree and the file when vacant.
- Integration points: `.codex/config.toml` (TOML round-trip via `spawn_cli.io.toml_io.load_toml/save_toml`); `core/high_level.py` unchanged; `spawn ide list-supported-ides` output changes automatically to `agentIgnore: project`.
- Step 8 note: update `spec/design/ide-adapters.md` (codex agent-ignore row "Unsupported ... steer via AGENTS/policy", and the Codex adapter table row) to reflect permissions-profile deny rules.

## Before -> After
### Before
- `IdeCapabilities.agent_ignore="unsupported"`; `add_agent_ignore`/`remove_agent_ignore` are warn stubs; no `clear_spawn_agent_ignore` override; spawn ignore lists silently not applied for codex; `finalize_codex_repo` only knows `mcp_servers`.
### After
- `IdeCapabilities.agent_ignore="project"`; adapter writes/removes deny globs in `[permissions.spawn]` profile; `clear_spawn_agent_ignore` removes recorded globs; `finalize_codex_repo` cleans the `permissions` subtree and deletes the config when only empty `mcp_servers`/`permissions` remain; tests cover write/remove/clear/cleanup/warn-on-sandbox_mode.

## Details
Target TOML produced by the adapter (never writes `default_permissions`):

```toml
[permissions.spawn]
extends = ":workspace"

[permissions.spawn.filesystem.":workspace_roots"]
"spawn/.core/**" = "deny"
"secrets/**" = "deny"
```

User activation (manual, documented; mutually exclusive with `sandbox_mode`):
```toml
default_permissions = "spawn"
```

Warn condition: project config already contains top-level `sandbox_mode` -> `warnings.warn("codex: sandbox_mode is set; permissions.spawn deny rules are inert unless the user switches to default_permissions")`.

`clear_spawn_agent_ignore` mirrors `claude_code.py` L134-137: read recorded globs from `ll.get_agent_ignore_list(target_root, self.key)`, remove them.

State: `spawn/.metadata/codex/agent-ignore.txt` maintained by `core/high_level.py` — no adapter-side state.

## Execution Scheme
Suggested coordinator model: GLM-5.3-flash
> Each step id is the subtask filename (e.g. `1-codex-adapter`).
> Each step is executed by a dedicated `A5-coder` subagent (see Step 5).
- Phase 1 (sequential): step 1-codex-adapter -> step 2-vacancy-cleanup -> step 3-tests
- Phase 2 (sequential): step review — inspect all changes, fix inconsistencies
