---
name: spectask-create
description: Use when drafting a new spectask (specification only, per spec/main.md).
---

**Mandatory:** read **spec/main.md** in full before acting. Do not invent procedure beyond that file.

**Role:** `A1-drafter`

**Steps:** 1–2 only — then stop for user Step 3.

**Rules:** `R3-code-num`, `R4-code-tracker`, `R5-new-task`, `R7-process`, `R8-concrete`, `R9-greenfield`, `R10-ask`, `R11-navigation`, `R13-model-line`, `R14-changed-files`, `R16-ambient`

**Roles involved:** `A1-drafter`, optional `A2-explorer` (1.6), `A3-reviewer` (Step 2)

**Flow:**

1. Read **spec/main.md** fully — Folder Structure, Embedded rules, Roles, Subagent run protocol, Process Overview, overview and subtask templates.
2. Execute **Step 1: Spec drafting** as `A1-drafter` (items 1.1–1.6) exactly as written in **spec/main.md**.
3. Execute **Step 2: Spec self-review** via `A3-reviewer` exactly as written in **spec/main.md**.
4. Stop — wait for user Step 3. Do not start Steps 4–7.

**Constraint:** no product implementation until spec review passes.
