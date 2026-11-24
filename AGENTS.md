<!-- spawn:start -->
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.
- Use the platform ask tool when available (R10-ask in spec/main.md); otherwise, stop and request input from the user.

Read every file listed under `Mandatory reads`.
Mandatory reads:
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/rules/01-vacancy-cleanup-subtrees.md` - finalize_*_repo cleanup must know every adapter-written config subtree; avoid dead configs.
- `spawn/rules/02-agent-config-namespacing.md` - Local rule file.
- `spawn/rules/03-adapter-spawn-warning.md` - IDE adapters emit warnings via SpawnWarning category for friendly CLI output.
- `spawn/rules/04-adapter-skill-name-constraints.md` - Local rule file.
- `spawn/rules/05-adapter-canonical-config-file.md` - Local rule file.
- `spawn/rules/06-new-ide-adapter-checklist.md` - Local rule file.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.

Inspect `Contextual reads` descriptions and read only files relevant to the current task.
Contextual reads:
- `spec/main.md` - Spec-Tasks methodology — folder structure, eight-step process, overview template.
- `spec/design/hla.md` - Project high-level architecture; updated in Step 8.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
<!-- spawn:end -->