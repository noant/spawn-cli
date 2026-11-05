linked task: spec/tasks/_DONE_26-codex-agent-ignore

## Idea (informal)

Codex agent ignore support in the existing **CodexAdapter** (`src/spawn_cli/ide/codex.py`).

### Problem

Adapter declared `agent_ignore="unsupported"` in `IdeCapabilities` and warned in `add_agent_ignore` / `remove_agent_ignore`: "codex: agent ignore is unsupported; steer via AGENTS.md policy instead". Meanwhile Codex shipped beta permission profiles, so spawn-managed `agent-ignore` entries (core + extensions, `spawn_cli.core.low_level.get_all_agent_ignore`) were silently not applied for codex targets.

### Outcome (implemented as task 26)

- Capability switched to `agent_ignore="project"`; deny rules written as `"glob" = "deny"` under `[permissions.spawn.filesystem.":workspace_roots"]` in `.codex/config.toml` (`extends = ":workspace"`).
- `default_permissions` is never written (mutually exclusive with `sandbox_mode`); user activates manually.
- `clear_spawn_agent_ignore` rollback via state file; `finalize_codex_repo` is permissions-aware.
- No `.codexignore` exists upstream (openai/codex #6530, #24993); `.gitignore` only affects file discovery.

### Research notes (original plan, for reference)

- Precedent adapters copied from: `cursor.py`, `windsurf.py` (native), and especially `claude_code.py` (project-style).
- Tests mirrored under `tests/ide/test_codex.py`; new `tests/ide/test_vacancy.py`.
