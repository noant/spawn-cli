---
name: spectask-execute
description: Steps 5-6 in spec/main.md; in interactive mode wait for user Step 7, in auto mode continue to Step 8.
---

**Mandatory:** read **spec/main.md** in full — Steps 5-6, Coder protocol, Subagent run protocol.

**Role:** `A6-coordinator`

**Steps:** 5-6; then `[interactive]` wait for user Step 7 / `[auto]` continue to Step 8 (Step 7 skipped, unchecked).

**Rules:** `R7-process`, `R10-ask`, `R13-model-line`, `R14-changed-files`, `R15-done-marking`, `R16-ambient`, `R23-review-scheme`

**Roles involved:** `A6-coordinator`, `A5-coder` (per step), `A4-reviewer` (Step 6). Same chat as Steps 1-3: `A1-drafter` must not be coordinator — launch a new `A6-coordinator` sub-agent.

**Flow:**

1. Read **spec/main.md** fully — Roles, Subagent run protocol, Steps 5-6, Coder protocol, `R13`-`R16`, `R23`.
2. Assume coordinator role per Step 5 Executor rules (same-chat → launch `A6-coordinator` sub-agent; fresh chat → current agent is coordinator). `[auto]` run mode: no "implement" command needed.
3. Execute **Step 5** exactly as written (launch one `A5-coder` per Execution Scheme step — never inline).
4. Execute **Step 6** via `A4-reviewer` per the Code review scheme from `## Review models` (`R23`).
5. `[interactive]` — stop, wait for user Step 7, do not start Step 8. `[auto]` — proceed to Step 8 (and Pattern extract) per spec/main.md.
