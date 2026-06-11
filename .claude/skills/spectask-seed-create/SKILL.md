---
name: spectask-seed-create
description: Capture a rough idea as spec/seeds/{X}-{slug}.md (not a full task); then offer to start spectask-create.
---


Operate within the **spectask** process defined in attached **spec/main.md**.

Follow the short **Seed** paragraph and **[Seed file template (header)](#seed-file-template-header)** in **spec/main.md**.

Pick a kebab-case **slug** and the next **`X`** under **`spec/seeds/`** (default: max numeric prefix among **`*.md`** there + **1**). Create **`spec/seeds/{X}-{slug}.md`**: **`linked task: none`** unless it already binds to an **`overview.md`** path — blank line — then informal notes (**not** a full spectask).

Suggest **spectask-create** when the user promotes; **Step 1** and **Step 7** item **6** covering seed wiring live there.

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
