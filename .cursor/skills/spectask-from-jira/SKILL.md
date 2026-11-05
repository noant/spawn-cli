---
name: spectask-from-jira
description: Import Jira tickets into spec/tasks/{task-code}-{slug}/; codebase analysis for Steps 2-3; offline fallback.
---

**Mandatory:** read **spec/main.md** in full. Do not invent procedure beyond that file.

**Role:** `A1-drafter`

**Rules:** `R4-code-tracker`, `R5-new-task`, `R7-process`, `R8-concrete`, `R9-greenfield`, `R10-ask`, `R11-navigation`, `R13-model-line`, `R14-changed-files`, `R16-ambient`, `R23-review-scheme`

**Roles involved:** `A1-drafter`, optional `A3-explorer`/`A2-researcher`, `A4-reviewer` (Step 3), `A6-coordinator` (auto mode, Step 5)

**Flow:**

1. Read **spec/main.md** fully — `R4-code-tracker`, Steps 1-3, overview template.
2. **Combined Step 1.1 ask** per **spectask-create** gate item 3 (run mode, depth, review schemes, etc.) — one `R10-ask` call.
3. **Fetch ticket** — prefer MCP tool `jira_fetch` (issue key); fallback `spectask-mcp run --issue KEY`; fallback `R10-ask` for key + pasted title/body.
4. **Scaffold** — kebab-case slug from the ticket summary; create `spec/tasks/{task-code}-{slug}/`.
5. **Spec (Steps 2-3)** — ticket body is source requirements only, never copied as-is. Map intent to concrete paths/symbols (repo + `spec/design/`, `R11-navigation`). In **Details** add a **Jira source** subsection (key, summary, relevant fields/body); clarifications and constraints below it. Execute Steps 2-3 as in **spec/main.md** and **spectask-create**.
6. **Run mode branch:** `[interactive]` — stop, wait for user Step 4; `[auto]` — continue automatically to Steps 5-6, then Step 8 and Pattern extract (Steps 4 and 7 skipped, checkboxes unchecked).


Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.
- Use the platform ask tool when available (R10-ask in spec/main.md); otherwise, stop and request input from the user.

Mandatory reads:
- `spec/main.md` - Spec-Tasks methodology — folder structure, eight-step process, overview template.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/rules/01-vacancy-cleanup-subtrees.md` - finalize_*_repo cleanup must know every adapter-written config subtree; avoid dead configs.
- `spawn/rules/02-agent-config-namespacing.md` - Local rule file.
- `spawn/rules/03-adapter-spawn-warning.md` - IDE adapters emit warnings via SpawnWarning category for friendly CLI output.
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spec/design/hla.md` - Project high-level architecture; updated in Step 8.
