---
document: spawn-extension-skill-sources
audience: machine
encoding: utf-8
prerequisite: spawn-ext-guide/ai/core.md; spawn-ext-guide/ai/config-yaml.md for skills map and required-read merge
---

# Skill sources — `extsrc/skills/*.md`

## skill_sources.extsrc_skills_md

format:

- encoding: UTF-8
- body_format: Markdown
- filename MUST match key under `config.skills` when that skill is declared.
- discovery: installed `extsrc/skills/*.md` + `skills:` entries together (keys supply overrides/`required-read`).
- for packs you publish: declare **every** shipped skill file under `skills:` so metadata is explicit; do not rely on discovery alone (see **`config-yaml`** invariant 3).

## frontmatter_body_collision

- Avoid a second line that is exactly `---` inside the skill body; anything after the **first** closing `---` belongs to the body — nested doc examples may need indentation or code fences so they do not terminate frontmatter early.

## frontmatter_syntax

- opens with line exactly `---`; closes at next line that is exactly `---`; inner block parsed as YAML (safe subset).
- common keys: `name`, `description`
- no valid frontmatter: entire file = skill body.

resolution_order.name:

1. `config.skills[<filename>].name` if present
2. else frontmatter `name` if present
3. else basename without `.md`

resolution_order.description:

1. `config.skills[<filename>].description` if present
2. else frontmatter `description` if present
3. else empty string

body_definition:

- body = content after closing frontmatter `---`, or whole file if no frontmatter.

rendering:

- Spawn does NOT copy skill file as-is to IDE; builds normalized metadata; IDE adapters write adapter-specific formats.

logical_rendered_markdown_shape (conceptual order):

1. YAML frontmatter `name`, `description`
2. Spawn-injected instruction to read **`spawn/navigation.yaml`** first (authors do **not** configure this path anywhere in extension **`config.yaml`** or templates — see **`spawn_navigation_yaml_authoring_rule`** in `spawn-ext-guide/ai/config-yaml.md`).
3. Mandatory reads (paths + descriptions)
4. Contextual reads if any
5. skill body from source

authoring_hint: keep body short procedural; long reference → `extsrc/files/` via globalRead/localRead/required-read (see `spawn-ext-guide/ai/config-yaml.md`). Do **not** mention `spawn/navigation.yaml` in extension configuration — it is generated and read automatically. Do **not** introduce a separate repo navigation index file; tune **`globalRead`** / **`localRead`** in **`config.yaml`** so Spawn builds navigation for you.

## skill_file.example.reference_only

```markdown
---
name: acme-run-task
description: Execute the Acme task flow in the current repo.
---

When the user wants to run an Acme task:

1. Read the mandatory context injected into this skill.
2. Open or create work under `spec/tasks/` as described in the methodology guide.
3. Report blockers explicitly instead of guessing.
```

note: if `config.skills` sets `name` and `description` for this filename, frontmatter MAY be omitted.
