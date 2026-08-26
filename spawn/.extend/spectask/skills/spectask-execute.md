---
name: spectask-execute
description: Steps 4–5 in spec/main.md; then wait for user Step 6.
---

**Mandatory:** read **spec/main.md** in full before acting — especially Steps 4–5, Coder protocol, Subagent run protocol.

**Role:** `A5-coordinator`

**Steps:** 4–5 — then wait for user Step 6.

**Rules:** `R7-process`, `R10-ask`, `R13-model-line`, `R14-changed-files`, `R15-done-marking`, `R16-ambient`

**Roles involved:** `A5-coordinator`, `A4-coder` (per step), `A3-reviewer` (Step 5). Same chat as Steps 1–2: `A1-drafter` must not be coordinator — launch a new `A5-coordinator` sub-agent.

**Flow:**

1. Read **spec/main.md** fully — Roles, Subagent run protocol, **Step 4: Code implementation**, **Step 5: Code self-review**, Coder protocol, `R13`–`R16`.
2. Assume coordinator role per Step 4 Executor rules (same-chat → launch `A5-coordinator` sub-agent; fresh chat → current agent is coordinator).
3. Execute **Step 4** exactly as written in **spec/main.md**.
4. Execute **Step 5** exactly as written in **spec/main.md**.
5. Stop — wait for user Step 6. Do not start Step 7.
