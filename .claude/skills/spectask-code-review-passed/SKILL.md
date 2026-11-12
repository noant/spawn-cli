---
name: spectask-code-review-passed
description: After user confirms code review — Steps 6–7 in one run (spec/main.md).
---


Operate within the **spectask** process defined in attached **spec/main.md**.

On the active `spec/tasks/{X}-{name}/overview.md`, finish **Step 6** (mark **code review passed** and the Step 6 prompt), then complete **Step 7** through **Design documents updated** in the same run. If **`overview.md`** ties a **`spec/seeds/`** file to this task, run **Step 7** item **6** (seed `_DONE_` rename) per **`spec/main.md`**. Ask which task if unclear.


Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.

Mandatory reads:
- `spec/main.md` - Spec-Tasks methodology — folder structure, seven-step process, overview template.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spec/design/hla.md` - Project high-level architecture; updated in Step 7.
