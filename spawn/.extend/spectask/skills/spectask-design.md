---
name: spectask-design
description: Use when registering architecture files in spec/design.yaml or drafting/updating spec/design/*.md, including the HLA document.
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
- Update HLA in Step 7 based on the task's changed/added files and symbols; keep it in sync with the repo.
- If a component is removed, delete its `###` block; if renamed, rename the block and update its fields.
