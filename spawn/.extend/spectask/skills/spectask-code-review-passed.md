---
name: spectask-code-review-passed
description: After user confirms code review / debugging — Steps 7–8 then pattern extract (spec/main.md).
---

**Mandatory:** read **spec/main.md** in full before acting — especially Steps 7–8 and Pattern extract.

**Role:** `A1-drafter`

**Steps:** 7 → 8 → Pattern extract (same run).

**Rules:** `R1-paths`, `R2-no-clutter`, `R7-process`, `R14-changed-files`

**Roles involved:** User (Step 7 confirmation); `A1-drafter` (mark 7, run 8, pattern extract)

**Flow:**

1. Read **spec/main.md** fully — **Step 7: Code review / debugging**, **Step 8: Design document update**, **Pattern extract (after Step 8)**.
2. Execute **Step 7** exactly as written (mark `[V]` and prompt).
3. Execute **Step 8** exactly as written.
4. Execute **Pattern extract** exactly as written (or via **spectask-extract-patterns**): filter candidates, then present the entire filtered list to the user in one message in this run, then ask per-candidate Required/Optional/Decline via the ask tool. Do not write under **`spawn/rules/`** or edit **`spawn/navigation.yaml`** until the user answers.
