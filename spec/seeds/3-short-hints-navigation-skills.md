linked task: none

## Idea (informal)

**Short agent-facing instructions** that **do not rely on opening separate files**: they should land in **merged navigation** (`spawn/navigation.yaml` and derived agent context) and **appear in every relevant skill** (or be injected via one mechanism), so obey/read paths and workflows are visible immediately without manually reading long Markdown.

Goal: shrink the gap between “rule exists in the repo” and “agent never picked it up”, especially for **read-required**, contextual blocks, and repeated reminders from **AGENTS.md** / navigation.

## Design questions (for `spectask-create`)

- **Source of truth**: single file (e.g. YAML/snippet) that generates or embeds into navigation and skills, vs duplication checked in CI.
- **Granularity**: global hints vs per-extension vs per-task seeds.
- **IDE scope**: Spawn CLI merge only vs Cursor rules/skills without blowing context limits.
- **Maintenance**: part of `spectask-design` / codegen vs manual process documented in `spec/design/agentic-flow.md`.

When you promote this seed, run **`spectask-create`**; **Step 1** and **Step 7** item **4** (seed ↔ overview linking) apply **only after** the new task actually covers what this seed describes (today: **still open**; task 16 only addressed **navigation `rules` → skill read lists**, not hints-without-files or unified snippet source).
