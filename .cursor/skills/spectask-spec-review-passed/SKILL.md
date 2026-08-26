---
name: spectask-spec-review-passed
description: Step 3 — spec approved (spec/main.md).
---


**Mandatory:** read **spec/main.md** in full before acting — especially Step 3.

**Role:** current agent (bookkeeping for User Step 3)

**Steps:** 3 only — then stop. Do not start Steps 4–5 here.

**Rules:** `R7-process`, `R10-ask`

**Roles involved:** User (confirmation); later Steps 4–5 → `A5-coordinator` via execute skills

**Flow:**

1. Read **spec/main.md** fully — Process Overview and **Step 3: Spec review** (wording for `[V]` and the prompt).
2. Execute **Step 3** exactly as written: resolve the active task overview (`R10-ask` if unclear); set `[V] Spec review`; prompt `Reply 'implement' to start.`
3. Stop — wait for the user’s implementation command. Do not start Steps 4–7.


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
