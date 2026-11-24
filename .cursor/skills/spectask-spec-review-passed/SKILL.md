---
name: spectask-spec-review-passed
description: Step 4 — spec approved (spec/main.md).
---


Interactive-mode bookkeeping only. In `[auto]` run mode Step 4 is skipped (checkbox unchecked) and implementation starts automatically after Step 3 — do not use this skill.

**Mandatory:** read **spec/main.md** in full — Step 4.

**Role:** current agent (bookkeeping for User Step 4)

**Steps:** 4 only — then stop. Do not start Steps 5-6 here.

**Rules:** `R7-process`, `R10-ask`

**Flow:**

1. Read **spec/main.md** fully — Process Overview and **Step 4: Spec review** (wording for `[V]` and the prompt).
2. Execute **Step 4** exactly as written: resolve the active task overview (`R10-ask` if unclear); set `[V] Spec review`; prompt `Reply 'implement' to start.`
3. Stop — wait for the implementation command. Do not start Steps 5-8.


Before this skill, if the Spawn block instructions from `AGENTS.md` are not in context, read `AGENTS.md` first.

Mandatory reads:
- `spec/main.md` - Spec-Tasks methodology — folder structure, eight-step process, overview template.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.

Contextual reads:
- `spec/design/hla.md` - Project high-level architecture; updated in Step 8.
