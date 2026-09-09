---
name: spectask-extract-patterns
description: After Step 8 — extract reusable patterns into spawn/rules/ and navigation (spec/main.md).
---


**Mandatory:** read **spec/main.md** in full before acting — especially Pattern extract (after Step 8).

**Role:** `A1-drafter`

**Steps:** after Step 8 only — not a Status checkbox.

**Rules:** `R14-changed-files` (+ Selection criteria and Write rules in **spec/main.md**)

**Roles involved:** `A1-drafter`; User (per-candidate Required/Optional/Decline via the ask tool)

**Flow:**

1. Read **spec/main.md** fully — **Pattern extract (after Step 8)** (Discover, Selection criteria, Present, Ask, Apply, Write).
2. Execute **Discover** exactly as written.
3. If Discover leaves zero candidates, say so briefly and stop (do not ask, do not present, do not invent fillers).
4. Otherwise **Present** the entire filtered list in **one message** in this run, right after Step 8. For each survivor: short title + one-line rationale + suggested scope (Required = `read-required`, Optional = `read-contextual`).
5. **Ask** per-candidate acceptance via the ask tool (`R10-ask`): per-candidate Required/Optional/Decline, plus a "decline all" option. Wait for the user's answer. Do not write rules yet, do not run `spawn refresh`, do not start the next task.
6. After the answer, **Apply** the user's decision: write only Required/Optional candidates; candidates not addressed default to Decline. If everything is Declined, write nothing.
7. Execute **Write** exactly as written (Required/Optional only), then `spawn refresh`.


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
