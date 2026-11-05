---
name: spectask-design
description: Use when registering architecture files in spec/design.yaml or drafting spec/design/*.md.
---


**Mandatory:** read **spec/main.md** in full — Folder Structure and Step 8 design rules.

**Role:** `A1-drafter`

**Steps:** ad-hoc design docs / `spec/design.yaml` (not a Status step). Post-impl updates → Step 8.

**Rules:** `R1-paths`, `R2-no-clutter`, `R10-ask`, `R14-changed-files`

**Flow:**

1. Read **spec/main.md** fully — Folder Structure (`spec/design.yaml`, `spec/design/hla.md`, `spec/design/{name}.md`) and Step 8 Index / Scope / Write rules.
2. Add or edit `spec/design/{name}.md` as needed; paths under Folder Structure only (`R1-paths`).
3. Register or update rows in `spec/design.yaml` (`path` + `description`).
4. List changed files (`R14-changed-files`). Do not run the full Steps 1-8 Status cycle unless the user is closing a task via Step 8.

## HLA update rule

Follow the HLA template structure exactly — fixed top-level order, no invented sections:

1. `## Project Overview` — technologies, infrastructure services, frameworks.
2. `## Entry Points` — `### {name}` per user-facing surface (frontend, UI, console, CLI, worker): `Description`, `Used API / service entrypoints`.
3. `## Services & API Endpoints` — `### {name}` per service/endpoint: `Description`, `Used service abstractions`, `Used concrete implementations`.
4. `## Service Implementations` — `### {name}` per implementation: same fields as section 3.
5. `## Data Flow` — data flow through the system.

Rules:
- Add/remove `###` blocks freely; never reorder the five sections.
- Every `###` block carries all fields of its section (no empty or partial blocks).
- Update HLA in Step 8 from the task's changed/added files and symbols; keep in sync with the repo.
- Removed component → delete its block; renamed → rename block and update fields.


Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.
- Use the platform ask tool when available (R10-ask in spec/main.md); otherwise, stop and request input from the user.

Mandatory reads:
- `spec/main.md` - Spec-Tasks methodology — folder structure, eight-step process, overview template.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/rules/01-vacancy-cleanup-subtrees.md` - finalize_*_repo cleanup must know every adapter-written config subtree; avoid dead configs.
- `spawn/rules/02-agent-config-namespacing.md` - Local rule file.
- `spawn/rules/03-adapter-spawn-warning.md` - IDE adapters emit warnings via SpawnWarning category for friendly CLI output.
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spec/design/hla.md` - Project high-level architecture; updated in Step 8.
