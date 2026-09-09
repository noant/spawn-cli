---
name: spectask-execute-step-by-step
description: Step 5 — one Execution Scheme subtask per run with per-step self-review; auto Step 6 when all done (spec/main.md).
---

**Mandatory:** read **spec/main.md** in full before acting — especially Steps 5–6, Coder protocol, Subagent run protocol.

**Role:** `A6-coordinator`

**Steps:** Step 5 one subtask per run (+ scoped self-review); when all done → full Step 6; then wait for Step 7.

**Rules:** `R7-process`, `R10-ask`, `R13-model-line`, `R14-changed-files`, `R15-done-marking`, `R16-ambient`

**Roles involved:** `A6-coordinator`, `A5-coder`, `A4-reviewer` (per-step scoped, then full Step 6)

**Flow:**

1. Read **spec/main.md** fully — **Step 5**, **Step 6**, Coder protocol, Subagent run protocol, `R13`–`R16`.
2. Execute **one** pending Execution Scheme subtask under Step 5 (`A5-coder` → `R15-done-marking`); `R10-ask` if the task is unclear.
3. Run a scoped Step 6-style self-review for that step only (`A4-reviewer`) — do not mark overview **Code self-review** yet.
4. If steps remain: stop and prompt for the next step.
5. If all steps done: mark Code implementation, then execute full **Step 6** exactly as in **spec/main.md**; stop — wait for user Step 7.
