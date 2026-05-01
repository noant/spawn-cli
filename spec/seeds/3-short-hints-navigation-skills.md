linked task: spec/tasks/18-hints-navigation-skills-agents/overview.md

## Idea (informal)

**Short agent-facing instructions** stored **inside each extension** (a compact snippet or small block — same spirit as **`localRead`** surfaces in config), readable in **two scopes**:

- **Local (this extension only):** during work scoped to **that extension’s skills** — the short instruction is part of what agents see for tasks/skills belonging to this pack only.
- **Global (all extensions):** during **any** extension’s skills — the same mechanism contributes **merged** hints into **`spawn/navigation.yaml`** / derived agent context so cross-pack sessions still see shared reminders without opening long Markdown.

Together with navigation merge, instructions should **not rely only on opening separate files**: they land in merged navigation and **appear in every relevant skill** (or one injection path), so obey/read paths and workflows show up immediately.

Goal: shrink the gap between “rule exists in the repo” and “agent never picked it up”, especially for **read-required**, contextual blocks, and repeated reminders from **AGENTS.md** / navigation.

## Repo navigation hints (maintainer-owned)

The **same kind** of short agent-facing text can also live in **merged navigation**, following the **`rules`** model:

- **Who edits it:** the **repository user / maintainer** adds or maintains entries — **not** the extension author. Same ownership idea as **`read-required`** paths under **`rules`** in `spawn/navigation.yaml`: local repo overlay on top of what packs ship.
- **Where:** a dedicated **`hints`** section in navigation (exact YAML shape TBD), merged with other slices the same way navigation already merges.
- **Rendering:** on skill generation/render, **`hints`** are injected **into every skill**, alongside **required-read material derived from rules** — one pipeline for “always show this in agent context”, without relying on agents opening long Markdown.

This is **related but distinct** from **extension-pack hints** (see **Idea** above): packs may declare portable snippets (local/global); **`hints`** in navigation are **workspace-specific**, repo-controlled glue. Spec/work should treat merge order, deduplication, and AGENTS.md overlap explicitly.

## Design questions (for `spectask-create`)

- **Extension-local vs global:** single field or two (e.g. “always merge globally” vs “only attach when skill belongs to this extension”), and whether dependent extensions inherit another pack’s **local-only** hints (see seed `1-extension-link-localread-bridge.md`).
- **Navigation `hints` vs extension hints:** merge order (repo vs pack), dedup, maximum size / truncation, and whether `hints` entries can reference paths vs inline text only.
- **Navigation `hints` vs `rules`:** shared injector with required-read lists or parallel section only; precedence if both convey similar reminders.
- **Source of truth**: single file (e.g. YAML/snippet) that generates or embeds into navigation and skills, vs duplication checked in CI.
- **Granularity**: global hints vs per-extension vs per-task seeds.
- **IDE scope**: Spawn CLI merge only vs Cursor rules/skills without blowing context limits.
- **Maintenance**: part of `spectask-design` / codegen vs manual process documented in `spec/design/agentic-flow.md`.

When you promote this seed, run **`spectask-create`**; **Step 1** and **Step 7** item **4** (seed ↔ overview linking) apply **only after** the new task actually covers what this seed describes (today: **still open**; task 16 only addressed **navigation `rules` → skill read lists**, not hints-without-files or unified snippet source).
