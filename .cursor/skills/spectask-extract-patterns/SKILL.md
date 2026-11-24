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
4. `[auto]`: skip Present/Ask — write all survivors, scope auto-detected (Required = repo-wide rule, Optional = context-specific), update `spawn/navigation.yaml`, `spawn refresh`, list changed files (`R14`).
5. `[interactive]`: **Present** the entire filtered list in **one message** right after Step 8; per survivor: short title + one-line rationale + scope (Required = `read-required`, Optional = `read-contextual`).
6. `[interactive]`: **Ask** per-candidate Required/Optional/Decline plus "decline all" via the ask tool (`R10-ask`); wait. Do not write rules, run `spawn refresh`, or start the next task yet.
7. **Apply**: write only Required/Optional candidates; unanswered candidates default to Decline; all Declined → write nothing.
8. **Write** exactly as written (Required/Optional only), then `spawn refresh`.


Before this skill, if the Spawn block instructions from `AGENTS.md` are not in context, read `AGENTS.md` first.

Mandatory reads:
- `spec/main.md` - Spec-Tasks methodology — folder structure, eight-step process, overview template.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.

Contextual reads:
- `spec/design/hla.md` - Project high-level architecture; updated in Step 8.
