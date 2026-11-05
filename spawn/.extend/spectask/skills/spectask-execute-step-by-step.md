---
name: spectask-execute-step-by-step
description: Interactive mode - Step 5 one Execution Scheme subtask per run with per-step self-review; full Step 6 when all done (spec/main.md).
---

Interactive-mode variant of **spectask-execute**: user drives subtask-by-subtask. In `[auto]` run mode use **spectask-execute** instead — subtasks run continuously without per-step stops.

**Mandatory:** read **spec/main.md** in full — Steps 5-6, Coder protocol, Subagent run protocol.

**Role:** `A6-coordinator`

**Rules:** `R7-process`, `R10-ask`, `R13-model-line`, `R14-changed-files`, `R15-done-marking`, `R16-ambient`, `R23-review-scheme`

**Roles involved:** `A6-coordinator`, `A5-coder`, `A4-reviewer` (per-step scoped, then full Step 6)

**Flow:**

1. Read **spec/main.md** fully — Steps 5-6, Coder protocol, Subagent run protocol, `R13`-`R16`, `R23`.
2. Execute **one** pending Execution Scheme subtask under Step 5 (`A5-coder` → `R15-done-marking`); `R10-ask` if the task is unclear.
3. Run a scoped Step 6-style self-review for that step only (`A4-reviewer` per the Code review scheme); do not mark overview **Code self-review** yet.
4. If steps remain: stop and prompt for the next step.
5. If all steps done: mark Code implementation, execute full **Step 6** per spec/main.md; stop — wait for user Step 7.
