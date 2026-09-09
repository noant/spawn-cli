---
name: spectask-create
description: Use when drafting a new spectask (specification only, per spec/main.md).
---

**Mandatory:** read **spec/main.md**.

**Role:** `A1-drafter`

**Steps:** 0–3 only (Classify, Research, Spec drafting, Spec self-review) — then stop for user Step 4.

**Rules:** `R3-code-num`, `R4-code-tracker`, `R5-new-task`, `R7-process`, `R8-concrete`, `R9-greenfield`, `R10-ask`, `R11-navigation`, `R13-model-line`, `R14-changed-files`, `R16-ambient`

**Roles involved:** `A1-drafter`, optional `A3-explorer`/`A2-researcher` (Step 1, 2.6), `A4-reviewer` (Steps 1.2.4, 3)

**Mandatory gate:**
Do nothing else until all three actions below are done, in order.

1. **Classify** the request per `R17-classify`:
   - `[A]` Question → answer directly; the gate ends here (no Steps 1–3).
   - `[B]` Initiative → continue to action 2.
   - If unclear, ask via `R10-ask` and wait.
2. **Read spec/main.md fully** (Folder Structure, Embedded rules, Roles, Subagent run protocol, Process Overview, templates).
3. **Ask research depth** via `R10-ask` (`[inline]` / `[medium]` / `[high]` / `[skip]`, per spec/main.md 1.1). Do not start research until the user answers.

Only after the gate passes, run the flow below.

**Flow:**

1. **Step 1: Research** as `A1-drafter` (spec/main.md 1.1–1.3) — run the loop at the depth chosen in the gate, then get user research review.
2. **Step 2: Spec drafting** as `A1-drafter` (spec/main.md 2.1–2.6).
3. **Step 3: Spec self-review** via `A4-reviewer` (spec/main.md).
4. Stop — wait for user Step 4. Do not start Steps 5–8.

**Constraint:** no product implementation until spec review passes.
