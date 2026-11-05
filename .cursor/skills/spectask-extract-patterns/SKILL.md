---
name: spectask-extract-patterns
description: After Step 8 — extract reusable patterns into spawn/rules/ and navigation (spec/main.md).
---


**Mandatory:** read **spec/main.md** in full — **Pattern extract (after Step 8)**.

**Role:** `A1-drafter`

**Steps:** after Step 8 only — not a Status checkbox.

**Rules:** `R14-changed-files` (+ Selection criteria and Write rules in **spec/main.md**)

**Flow:**

1. Read **spec/main.md** fully — Pattern extract (Discover, Selection criteria, Present, Ask, Apply, Write).
2. **Discover** exactly as written.
3. Zero candidates → say so briefly and stop (no ask, no present, no fillers).
4. `[auto]` run mode: skip Present/Ask — write ALL survivors as Optional (read-contextual), add them to `spawn/navigation.yaml`, run `spawn refresh`, list changed files (`R14`), and stop.
5. `[interactive]`: **Present** the entire filtered list in **one message** right after Step 8; per survivor: short title + one-line rationale + scope (Required = `read-required`, Optional = `read-contextual`).
6. `[interactive]`: **Ask** per-candidate Required/Optional/Decline plus "decline all" via the ask tool (`R10-ask`); wait. Do not write rules, run `spawn refresh`, or start the next task yet.
7. **Apply**: write only Required/Optional candidates; unanswered candidates default to Decline; all Declined → write nothing.
8. **Write** exactly as written (Required/Optional only), then `spawn refresh`.


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
