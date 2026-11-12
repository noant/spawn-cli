---
name: spectask-code-review-passed
description: Interactive Steps 7-8 then pattern extract (spec/main.md). Step 7 is skipped in auto run mode.
---

**Mandatory:** read **spec/main.md** in full — Steps 7-8 and Pattern extract.

**Role:** `A1-drafter`

**Steps:** 7 → 8 → Pattern extract (same run). `[auto]` run mode: Step 7 skipped (checkbox unchecked) — start at Step 8.

**Rules:** `R1-paths`, `R2-no-clutter`, `R7-process`, `R14-changed-files`

**Flow:**

1. Read **spec/main.md** fully — **Step 7**, **Step 8**, **Pattern extract (after Step 8)**.
2. `[interactive]`: execute **Step 7** exactly as written (mark `[V]` and prompt).
3. Execute **Step 8** exactly as written.
4. Execute **Pattern extract** exactly as written (or via **spectask-extract-patterns**): filter candidates; `[interactive]` present the filtered list in one message and ask per-candidate Required/Optional/Decline; `[auto]` skip Present/Ask and write all survivors with auto-detected scope (Scope rule in spec/main.md).
