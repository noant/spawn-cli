---
name: spectask-execute
description: Steps 5–6 in spec/main.md; then wait for user Step 7.
---

**Mandatory:** read **spec/main.md** in full before acting — especially Steps 5–6, Coder protocol, Subagent run protocol.

**Role:** `A6-coordinator`

**Steps:** 5–6 — then wait for user Step 7.

**Rules:** `R7-process`, `R10-ask`, `R13-model-line`, `R14-changed-files`, `R15-done-marking`, `R16-ambient`

**Roles involved:** `A6-coordinator`, `A5-coder` (per step), `A4-reviewer` (Step 6). Same chat as Steps 1–3: `A1-drafter` must not be coordinator — launch a new `A6-coordinator` sub-agent.

**Flow:**

1. Read **spec/main.md** fully — Roles, Subagent run protocol, **Step 5: Code implementation**, **Step 6: Code self-review**, Coder protocol, `R13`–`R16`.
2. Assume coordinator role per Step 5 Executor rules (same-chat → launch `A6-coordinator` sub-agent; fresh chat → current agent is coordinator).
3. Execute **Step 5** exactly as written in **spec/main.md**.
4. Execute **Step 6** exactly as written in **spec/main.md**.
5. Stop — wait for user Step 7. Do not start Step 8.
