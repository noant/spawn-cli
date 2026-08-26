---
name: spawn-ext-extract-stack-patterns
description: Analyze a reference codebase and distill universal stack patterns into extension spec files and procedural skills.
---


Goal: turn patterns from a real reference repository into portable methodology for a Spawn extension — without embedding reference-product names in rules or skill ids.

## When to use

- User asks to analyze a reference project and update methodology (spec files, skills).
- User wants recurring layout, DI, naming, or architecture patterns codified from production code.
- User asks to shorten spec/skill wording or add a new universal rule derived from analysis.

## Prerequisites

- Extension repo with `extsrc/` skeleton and `config.yaml`.
- Reference repository path and optional category list from the user.
- Follow **`spawn-methodology-shape`** if namespaces or read surfaces are not defined yet.

## Workflow

### 1. Load extension context

- Read `spawn/navigation.yaml`, `extsrc/config.yaml`, existing `extsrc/files/**` and `extsrc/skills/*.md`.
- Use **`spawn-ext-config`** and **`spawn-ext-skill-sources`** when editing config or skills.

### 2. Plan analysis categories

Split the reference codebase into independent domains, for example:

- solution layout and project roles
- abstractions / contracts layer
- implementation projects
- DI and service registration
- persistence / ORM
- HTTP / Web API
- background workers, processors, jobs
- language style and conventions

Launch one explore subagent per category in parallel. Each subagent inspects multiple projects in that domain only.

### 3. Subagent output contract

Each subagent must return:

- universal layout and naming patterns (placeholders only: `{Product}`, `{Feature}`, `{Domain}`, example product prefix if the extension already uses one)
- what belongs in each layer vs anti-patterns
- 8–12 portable rules suitable for a spec file
- no reference-product type names, config keys, or project names in the final rules

### 4. Write or update spec files

- Put rules under `extsrc/files/` in the extension's chosen namespace (e.g. `spec/extend/`, `methodology/`, `spec/design/`).
- One topic per file; short `###` sections and bullet lists.
- Merge duplicates across categories; resolve contradictions explicitly.
- Rules must apply to any project on the stack, not only the reference repo.
- New cross-cutting rules go into the appropriate existing spec (style, layout, etc.).

### 5. Write or update procedural skills

- One skill per scaffold/workflow task (new abstractions project, new registration, new entry point, etc.).
- Skill ids: stable, prefixed by the **extension/pack** name if needed for uniqueness — never by the reference product name.
- Body: numbered steps, concise.
- **First step always:** `Read <spec paths>` — same paths as `required-read` in `config.yaml`.
- Long reference stays in spec files; skills are procedures only.
- Register every skill file under `skills:` in `config.yaml` with `description` and `required-read`.

### 6. Shorten text (when asked)

- Remove repetition and filler; keep technical meaning.
- Do not remove spec `Read` steps from skills.
- Do not shorten normative code examples unless the user asks.

### 7. Validate and release

- Every path under `extsrc/files/` must appear in `config.yaml`.
- Bump `version` via **`spawn-ext-increment-version`** after material changes.
- Run `spawn extension check . --strict`.

## Constraints

- Chat with user: their language preference. Spec, skill bodies, and code strings: English unless the extension defines otherwise.
- Do not commit unless asked.
- Do not add README or extra docs unless asked.
- Do not build or run the reference project unless asked.

Hints:
- When finishing a task that involved editing this repo's code or docs: call mempalace_mine (mempalace-mine-mcp), then mempalace_reconnect on mempalace-mcp if already connected.
- Prefer codebase search via mempalace-mcp first; use workspace full-text / ripgrep only if MemPalace is unavailable or insufficient.
- Use the platform ask tool when available (R10-ask in spec/main.md); otherwise, stop and request input from the user.

Mandatory reads:
- `spawn-ext-guide/ai/core.md` - Machine baseline — terms, extsrc tree rules, static vs artifact, name and uniqueness, install outputs.
- `spawn-ext-guide/ai/config-yaml.md` - Machine schema for config.yaml — keys, files/folders/skills modes, reads, ignores, setup, annotated example.
- `spawn-ext-guide/ai/skill-sources.md` - Machine rules for extsrc/skills/*.md — frontmatter, name/description resolution, rendered skill shape, example.
- `.mempalace/wakeup.md` - Bounded MemPalace wake-up context from the palace.
- `spawn/rules/00-general.md` - General language-agnostic conventions (ASCII, documentation, chat language).
- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual).

Contextual reads:
- `spawn-ext-guide/ai/mcp-json.md` - Machine schema for extsrc/mcp/windows.json, linux.json, macos.json — servers, OS selection, aligned name sets, transport, spawn_stdio_proxy (stdio IDE proxy), env, capabilities, validation against check, JSON examples.
- `spawn-ext-guide/ai/cli.md` - Machine CLI reference — spawn init/extension/build commands, extensions.yaml bundle shape, authoring checklist.
- `spec/main.md` - Spec-Tasks methodology — folder structure, seven-step process, overview template.
- `spec/design/hla.md` - Project high-level architecture; updated in Step 7.
- `spec/design.yaml` - Index of architecture documents under spec/design/ — path and description per entry.
