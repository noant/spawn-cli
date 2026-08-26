---
name: spectask-from-jira
description: Import Jira tickets into spec/tasks/{task-code}-{slug}/; codebase analysis for Step 1-2; offline fallback.
---

**Mandatory:** read **spec/main.md** in full before acting. Do not invent procedure beyond that file.

**Role:** `A1-drafter`

**Steps:** fetch → scaffold → Steps 1–2 — then stop for user Step 3.

**Rules:** `R4-code-tracker`, `R5-new-task`, `R7-process`, `R8-concrete`, `R9-greenfield`, `R10-ask`, `R11-navigation`, `R13-model-line`, `R14-changed-files`, `R16-ambient`

**Roles involved:** `A1-drafter`, optional `A2-explorer`, `A3-reviewer` (Step 2)

**Flow:**

1. Read **spec/main.md** fully — especially `R4-code-tracker`, Step 1–2, overview template — then follow this skill’s import steps below.
2. **Fetch ticket** — Prefer MCP tool `jira_fetch` (pass issue key). On failure try `spectask-mcp run --issue KEY`. On failure use **`R10-ask`** to ask the user for key + pasted title/body.
3. **Scaffold** — Derive a kebab-case slug from the ticket summary. Create `spec/tasks/{task-code}-{slug}/`.
4. **Spec (Steps 1–2)** — Ticket body is source requirements only — not a finished spec. Do not copy it as-is into overview.md.
   - Explore the repo and relevant **spec/design/** docs to map ticket intent to concrete paths and symbols before writing anything. Also follow **`R11-navigation`** in **spec/main.md**.
   - In **Details**, add a **Jira source** subsection (key, summary, relevant ticket fields/body). Clarifications and constraints go below it.
   - Execute **Step 1** and **Step 2** exactly as in **spec/main.md** and **spectask-create**.
5. Stop — wait for the user’s Step 3. Do not start Steps 4–7.
