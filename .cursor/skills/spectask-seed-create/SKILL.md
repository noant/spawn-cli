---
name: spectask-seed-create
description: Capture a rough idea as spec/seeds/{X}-{slug}.md (not a full task); then offer to start spectask-create.
---


**Mandatory:** read **spec/main.md** in full before acting — especially Seed paragraph and Seed file template.

**Role:** `A1-drafter`

**Steps:** none of 1–7 — seed only. Promotion → **spectask-create**; seed close → Step 7 item 6.

**Rules:** `R1-paths`, `R2-no-clutter`, `R3-code-num` / `R4-code-tracker` (when promoting later), `R10-ask`

**Flow:**

1. Read **spec/main.md** fully — Folder Structure (`spec/seeds/`), Seed paragraph, Seed file template (header).
2. Create `spec/seeds/{X}-{slug}.md` exactly per that template (`linked task: none` unless already bound).
3. Offer **spectask-create** when the user wants to promote. Do not run Steps 1–7 in this skill.



Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.
- Use the platform ask tool when available (R10-ask in spec/main.md); otherwise, stop and request input from the user.

Mandatory reads:
- `spec/main.md` - Spec-Tasks methodology — folder structure, seven-step process, overview template.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spec/design/hla.md` - Project high-level architecture; updated in Step 7.
