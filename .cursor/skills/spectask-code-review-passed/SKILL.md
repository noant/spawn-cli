---
name: spectask-code-review-passed
description: After user confirms code review / debugging — Steps 6–7 then optional pattern extract (spec/main.md).
---


**Mandatory:** read **spec/main.md** in full before acting — especially Steps 6–7 and Optional: Pattern extract.

**Role:** `A1-drafter`

**Steps:** 6 → 7 → optional Pattern extract (same run).

**Rules:** `R1-paths`, `R2-no-clutter`, `R7-process`, `R14-changed-files`

**Roles involved:** User (Step 6 confirmation); `A1-drafter` (mark 6, run 7, pattern extract)

**Flow:**

1. Read **spec/main.md** fully — **Step 6: Code review / debugging**, **Step 7: Design document update**, **Optional: Pattern extract (after Step 7)**.
2. Execute **Step 6** exactly as written (mark `[V]` and prompt).
3. Execute **Step 7** exactly as written.
4. Execute **Optional: Pattern extract** exactly as written (or via **spectask-extract-patterns**): filter candidates, then present the entire filtered list to the user in one message in this run, then wait for the user to reply with per-candidate Required/Optional/Decline. Do not write under **`spawn/rules/`** or edit **`spawn/navigation.yaml`** until the user answers.


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
