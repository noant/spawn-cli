---
name: spectask-design
description: Use when registering architecture files in spec/design.yaml or drafting spec/design/*.md.
---


**Mandatory:** read **spec/main.md** in full before acting — especially Folder Structure and Step 7 design rules.

**Role:** `A1-drafter`

**Steps:** ad-hoc design docs / `spec/design.yaml` (not a Status step). Post-impl updates → Step 7.

**Rules:** `R1-paths`, `R2-no-clutter`, `R10-ask`, `R14-changed-files`

**Flow:**

1. Read **spec/main.md** fully — Folder Structure (`spec/design.yaml`, `spec/design/hla.md`, `spec/design/{name}.md`) and Step 7 Index / Scope / Write rules for design docs.
2. Add or edit `spec/design/{name}.md` as needed; keep paths under Folder Structure only (`R1-paths`).
3. Register or update rows in `spec/design.yaml` (`path` + `description`).
4. List changed files (`R14-changed-files`). Do not run the full Steps 1–7 Status cycle unless the user is closing a task via Step 7.


Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.
- Use the platform ask tool when available (R10-ask in spec/main.md); otherwise, stop and request input from the user.

Mandatory reads:
- `spec/main.md` - Spec-Tasks methodology — folder structure, seven-step process, overview template.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spec/design/hla.md` - Project high-level architecture; updated in Step 7.
