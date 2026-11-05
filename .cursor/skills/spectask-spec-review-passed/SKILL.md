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
