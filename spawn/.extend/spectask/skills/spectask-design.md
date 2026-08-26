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
