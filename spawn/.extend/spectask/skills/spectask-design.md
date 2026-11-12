---
name: spectask-design
description: Use when registering architecture files in spec/design.yaml or drafting/updating spec/design/*.md, including the HLA document.
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
