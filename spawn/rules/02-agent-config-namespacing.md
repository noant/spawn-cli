# Rule: spawn-namespaced profiles in agent project configs (project-style adapters)

Optional. For IDE adapters that implement agent ignore or similar via the
agent's own project config file (Claude Code, Codex, Qoder, Qwen Code) instead
of a dedicated ignore file.

Conventions:

1. Write entries only under a spawn-namespaced key/profile
   (`permissions.spawn.*`, `permissions.deny`, `[permissions.spawn]`), never at
   config top level beyond that namespace.
2. Never mutate the agent's global activation keys (e.g. Codex
   `default_permissions`); the user activates manually. If a conflicting
   setting exists (`sandbox_mode` vs `default_permissions` are mutually
   exclusive in Codex), emit a `warnings.warn` explaining the rules may be
   inert — do not "fix" the user's config.
3. Use idempotent structures: dict/set-keyed entries (`"glob" = "deny"`,
   list membership checks) so re-adding is a no-op and diff-sync
   (`_sync_project_agent_ignore_permissions` + `agent-ignore.txt`) stays safe.
4. On removal, prune only empty spawn-owned subtrees; keep user content in the
   same file (paired rule: `spawn/rules/01-vacancy-cleanup-subtrees.md`).

Example (task 26, Codex):

```toml
[permissions.spawn]
extends = ":workspace"

[permissions.spawn.filesystem.":workspace_roots"]
"spawn/.core/**" = "deny"
```

State: `spawn/.metadata/<ide>/agent-ignore.txt` (maintained by
`core/high_level.py`) — adapters keep no extra state files.
