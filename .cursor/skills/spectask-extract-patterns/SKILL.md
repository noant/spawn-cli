---
name: spectask-extract-patterns
description: After Step 7 — optional extract of reusable patterns into spawn/rules/ and navigation (spec/main.md).
---


**Mandatory:** read **spec/main.md** in full before acting — especially Optional: Pattern extract (after Step 7).

**Role:** `A1-drafter`

**Steps:** after Step 7 only — not a Status checkbox.

**Rules:** `R14-changed-files` (+ Selection criteria and Write rules in **spec/main.md**)

**Roles involved:** `A1-drafter`; User (per-candidate Required/Optional/Decline in one reply)

**Flow:**

1. Read **spec/main.md** fully — **Optional: Pattern extract (after Step 7)** (Discover, Selection criteria, Present, Apply, Write).
2. Execute **Discover** exactly as written.
3. If Discover leaves zero candidates, say so briefly and stop (do not ask, do not present, do not invent fillers).
4. Otherwise **Present** the entire filtered list in **one message** in this run, right after Step 7 — no `R10-ask`, no per-candidate tool questions, no pauses. For each survivor: short title + one-line rationale + suggested scope (Required = `read-required`, Optional = `read-contextual`). End the message with an explicit reply request: tell the user how to respond (per-candidate Required/Optional/Decline, or "decline all" to skip everything).
5. **Wait** for the user's reply. Do not write rules yet, do not run `spawn refresh`, do not start the next task.
6. After the reply, **Apply** the user's answer: write only Required/Optional candidates; candidates not addressed default to Decline. If everything is Declined, write nothing.
7. Execute **Write** exactly as written (Required/Optional only), then `spawn refresh`.


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
