---
name: spectask-extract-patterns
description: After Step 7 — present reusable patterns as a single list to the user (no preliminary questions), then write per user's per-candidate decision.
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
