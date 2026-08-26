---
name: spectask-execute-step-by-step
description: Step 4 — one Execution Scheme subtask per run with per-step self-review; auto Step 5 when all done (spec/main.md).
---

**Mandatory:** read **spec/main.md** in full before acting — especially Steps 4–5, Coder protocol, Subagent run protocol.

**Role:** `A5-coordinator`

**Steps:** Step 4 one subtask per run (+ scoped self-review); when all done → full Step 5; then wait for Step 6.

**Rules:** `R7-process`, `R10-ask`, `R13-model-line`, `R14-changed-files`, `R15-done-marking`, `R16-ambient`

**Roles involved:** `A5-coordinator`, `A4-coder`, `A3-reviewer` (per-step scoped, then full Step 5)

**Flow:**

1. Read **spec/main.md** fully — **Step 4**, **Step 5**, Coder protocol, Subagent run protocol, `R13`–`R16`.
2. Execute **one** pending Execution Scheme subtask under Step 4 (`A4-coder` → `R15-done-marking`); `R10-ask` if the task is unclear.
3. Run a scoped Step 5-style self-review for that step only (`A3-reviewer`) — do not mark overview **Code self-review** yet.
4. If steps remain: stop and prompt for the next step.
5. If all steps done: mark Code implementation, then execute full **Step 5** exactly as in **spec/main.md**; stop — wait for user Step 6.
