---
name: mempalace-search
description: MemPalace MCP or CLI search first; workspace grep only as fallback.
---


Use **`mempalace-mcp`** search/query tools when the server works; otherwise run **`mempalace search "<query>"`** from the repo root. If MemPalace is down or irrelevant, use normal workspace search.


Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.

Mandatory reads:
- `.mempalace/guides/guide.md` - MemPalace in the target repo — install, init, MCP mine/wake-up workflow, links to official docs.
- `.mempalace/guides/configuration.md` - Reference for config.json, mempalace.yaml, env vars, and repo-local palace_path.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spec/main.md` - Spec-Tasks methodology — folder structure, seven-step process, overview template.
- `spec/design/hla.md` - Project high-level architecture; updated in Step 7.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
