---
name: spectask-design
description: Use when registering architecture files in spec/design.yaml or drafting spec/design/*.md.
---


**Mandatory:** read **spec/main.md** in full before acting — especially Folder Structure and Step 8 design rules.

**Role:** `A1-drafter`

**Steps:** ad-hoc design docs / `spec/design.yaml` (not a Status step). Post-impl updates → Step 8.

**Rules:** `R1-paths`, `R2-no-clutter`, `R10-ask`, `R14-changed-files`

**Flow:**

1. Read **spec/main.md** fully — Folder Structure (`spec/design.yaml`, `spec/design/hla.md`, `spec/design/{name}.md`) and Step 8 Index / Scope / Write rules for design docs.
2. Add or edit `spec/design/{name}.md` as needed; keep paths under Folder Structure only (`R1-paths`).
3. Register or update rows in `spec/design.yaml` (`path` + `description`).
4. List changed files (`R14-changed-files`). Do not run the full Steps 1–8 Status cycle unless the user is closing a task via Step 8.

## HLA update rule

When updating `spec/design/hla.md`, follow the template structure exactly. Do not invent new top-level sections; keep the fixed order:

1. `## Project Overview` — technologies, infrastructure services, frameworks.
2. `## Entry Points` — one `### {name}` block per user-facing/external surface (frontend, UI, console, CLI, worker). Each block: `Description`, `Used API / service entrypoints`.
3. `## Services & API Endpoints` — one `### {name}` block per service/API endpoint. Each block: `Description`, `Used service abstractions`, `Used concrete implementations`.
4. `## Service Implementations` — one `### {name}` block per concrete implementation. Each block: `Description`, `Used service abstractions`, `Used concrete implementations`.
5. `## Data Flow` — how data flows through the system.

Rules:

- Add or remove `###` blocks within a section as components change; never reorder the five top-level sections.
- Every `###` block must carry the fields listed for its section (no empty blocks, no missing fields).
- Update HLA in Step 8 based on the task's changed/added files and symbols; keep it in sync with the repo.
- If a component is removed, delete its `###` block; if renamed, rename the block and update its fields.


Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.
- Use the platform ask tool when available (R10-ask in spec/main.md); otherwise, stop and request input from the user.

Mandatory reads:
- `spec/main.md` - Spec-Tasks methodology — folder structure, eight-step process, overview template.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spec/design/hla.md` - Project high-level architecture; updated in Step 8.
