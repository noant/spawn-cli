# Agentic Flow

This document describes how Spawn creates a coherent AIDD experience from
navigation files, extension configs, rendered skills, and target-local rules.

## Agent-Facing Surface

Agents should normally read:

- the Spawn block of the IDE entry file (mandatory/contextual reads rendered
  from `spawn/navigation.yaml`);
- files listed by navigation;
- rendered IDE skills;
- target-local files such as `spawn/rules/{file}.yaml`.

Agents should not read `spawn/.extend/{ext}` during normal work. That directory
is the installed extension source used by the utility to rebuild outputs.

Each IDE entry point should contain a Spawn-managed instruction block.
The block renders the navigation reads as bullets (like a rendered skill),
states that
`read-required` is mandatory before work, and that `read-contextual`
contains optional context selected by task relevance. IDE adapters render this
block into the IDE's native entry file, such as `AGENTS.md`, `CLAUDE.md`, or an
equivalent tool-specific file.

## Startup Flow

At the start of work in a target repository:

1. The IDE entrypoint block lists every mandatory and contextual read as
   bullets (skill-like form), so agents get the full navigation surface
   directly in the entry file.
2. Read every file listed under `Mandatory reads`.
3. Consider files listed under `Contextual reads` and read only those relevant
   to the task.
4. If the user task triggers a rendered skill, follow that skill's mandatory
   and contextual reads.

`read-required` is strict context. Files listed there should be compact and
safe to load for every session.

`read-contextual` is discoverable context. The agent sees descriptions and
chooses files when the current task needs them.

When no rendered skill matches the task, the agent still follows the entrypoint
and navigation flow. In that case, `spawn/navigation.yaml` and local rules form
the complete Spawn-provided context surface.

## Instruction Precedence

Spawn does not replace the user's direct instructions. The intended precedence
for agent behavior is:

1. Current user request and active conversation context.
2. IDE/system/developer instructions outside Spawn.
3. Rendered skill instructions selected for the current task.
4. Files from `read-required`.
5. Relevant files from `read-contextual`.
6. General methodology files and examples.

If two Spawn-provided files conflict, the more specific task or skill context
wins over global context. Target-local rules under `spawn/rules/` win over
extension defaults when they intentionally customize the local repository.

## Pseudocode And Data Examples

Structured snippets and algorithms in this document are illustrative
pseudostructures and pseudocode. They describe the intended logic and data
relationships, not required implementation types or literal serialized formats.

Implementation must use standard language facilities and libraries for the
chosen language, such as typed data structures, YAML parsers, path APIs,
collections, and normal control flow. It must not depend on ad hoc parsing of
these examples as strings.

## Navigation During Work

Navigation is generated from two sources:

- extension files with `globalRead: required` or `globalRead: auto`;
- user-maintained local rules under `spawn/rules/`.

Merged **`spawn/navigation.yaml`** may also carry **hints**: each extension’s **`- ext:`** entry can include a **`hints`** list (mirrored from that pack’s **`hints.global`** in **`config.yaml`**). Under **`read-required` → `rules`**, maintainer reminders use **hint-only** rows (a **`hint`** mapping with **no** mandatory **`path`**); file-backed rows list **`path`** and **`description`** only—**`hint`** must not sit on the same row as **`path`** (refresh moves any legacy **`path`+`hint`** pair into a separate hint-only row). Only these maintainer hints and extension **`hints`** feed the IDE **Hints:** rollup for the **entry file** (`AGENTS.md` and equivalents); rendered skills carry only the owning extension's **`hints.local`** (**`hint`** on **`read-contextual` → `rules`** is ignored for all pipelines). Deduping is by exact stripped string (first occurrence wins ordering across streams).

Example:

```yaml
read-required:
  - ext: spectask
    hints:
      - Prefer spectask steps in order.
    files:
      - path: spec/main.md
        description: Spec task process.
  - rules:
      - path: spawn/rules/team.yaml
        description: Team rules.
      - hint: Keep replies concise for this repo (standalone reminder).
      - hint: Another maintainer reminder without a rule file path.
read-contextual:
  - ext: spectask
    files:
      - path: spec/design/hla.md
        description: High-level architecture.
  - rules:
      - path: spawn/rules/frontend.yaml
        description: Frontend rules.
```

Navigation answers: what repository and methodology context exists, and what
must be read globally?

## Skill Flow

A rendered skill answers: what procedure should the agent follow for this
task?

When a skill is used:

1. Read the IDE entry file (such as `AGENTS.md`) when its Spawn block with the
   navigation index is not in context.
2. Read the skill's mandatory files.
3. Consider the skill's contextual files.
4. Follow the skill body, the entrypoint instruction (read the IDE entry file
   when its Spawn block is not in context), and any **Hints** list rendered in the
   skill file.
5. Continue to respect global navigation and local rules.

Rendered skills do not duplicate navigation: skill metadata carries only
skill-local context (the owner extension's `localRead` files plus the skill's
`required-read`). Global reads and hints live in the entry-point block
(embedded `spawn/navigation.yaml`, task 32); the skill references that
context through the entrypoint instruction instead of listing navigation
paths itself.

**Hints in rendered skills:** normalized metadata carries only **`hints.local`**
of the extension that owns the skill, rendered as a **Hints:** section **after**
the skill **body** and **before** **Mandatory reads** (plain-text strings,
deduped by exact stripped string). Per-hint and combined-size budgets still
apply to the skill block: **`SpawnWarning`** when limits are exceeded, and the
block may be **truncated** (including a terminal bullet with `...`).
**`hints.global`** and maintainer **`read-required` → `rules`** hints live only
in the IDE entry-point rollup (AGENTS.md managed block) and are not merged into
skills.

`spawn/navigation.yaml` remains the canonical index of which repository rules exist
and whether each is mandatory or contextual for the merged navigation surface.

## Entrypoint Contract

The Spawn-managed IDE entrypoint block should express this logic in plain
agent-facing language:

```markdown
Read every file listed under `Mandatory reads`.
Inspect `Contextual reads` descriptions and read only files relevant to the
current task.

Hints:
- {rollup hints, full text}

Mandatory reads:
- `spawn/rules/team.yaml` - Team rules.
- `spec/main.md` - Spec task process.

Contextual reads:
- `spec/design/hla.md` - High-level architecture.
```

When `spawn/navigation.yaml` is missing, refresh emits `SpawnError` instead of
rendering an empty block.

When hints are present, Spawn renders a **`Hints:`** bullet list (full text, no truncation) before the reads lists; the rollup is built from **`rollup_hints_for_agents`** — extension **`hints.global`** in installed-extension order, then maintainer **`read-required` → `rules`** hints — and may emit warnings if size thresholds are exceeded.

Adapters may format the block differently, but the semantic contract is the
same across IDEs.

## Read Categories

Spawn combines these read categories:

- Global required: extension files with `globalRead: required`.
- Global contextual: extension files with `globalRead: auto`.
- Local required: extension files with `localRead: required`, used by rendered
  skills from the same extension.
- Local contextual: extension files with `localRead: auto`, listed in rendered
  skills from the same extension.
- Skill required: files listed in one skill's `required-read`.
- Rule reads: files under `spawn/rules/`, managed through navigation.

`no` means the file is not mentioned in generated context for that category.

## Skill Metadata Generation

`generate-skills-metadata(extension)` creates normalized skill records for IDE
adapters.

Conceptual pseudocode:

```text
local_required = get-required-read-ext-local(extension)
local_auto = get-auto-read-local(extension)

for skill_path in list-skills(extension):
  skill_info = get-skill-raw-info(extension, skill_path)
  required = distinct(
    skill_info.required-read +
    local_required
  )
  auto = distinct(local_auto)
  resolve descriptions for required and auto files from read metadata
  emit skill metadata
```

`skill_info.required-read` is only for skill-specific mandatory files. It does
not need to repeat files from `local_required`, because the generation step
always merges those categories and removes duplicates.

**Hints** carry only **`hints.local`** of the `extension` argument (exact merge
and dedupe in `low_level.generate_skills_metadata`; truncation budgets for the
skill block preserved). **`hints.global`** and maintainer hint strings live
only in the entry-point block (AGENTS.md rollup) and are not part of skill
metadata.

Illustrative output pseudostructure:

```yaml
name: spectask-execute
description: Execute approved spectasks.
content: "Skill body without optional name/description notation."
hints:
  - Prefer spectask steps in order.
required-read:
  - file: spec/main.md
    description: Spec task process.
auto-read:
  - file: spec/design/hla.md
    description: Project high-level architecture.
```

If the same file appears more than once, the generated metadata keeps one entry.
Descriptions are resolved from local required, local auto, global required, or
global auto metadata.

## Rendered Skills

Each IDE adapter renders normalized skill metadata into the IDE's skill format.
A rendered skill must include:

- name;
- description;
- original skill content;
- an entrypoint instruction: when the Spawn block from the IDE entry file
  (such as `AGENTS.md`) is not in context, read that entry file first (rendered
  before mandatory reads);
- optional **Hints** bullets (owner `hints.local` only), placed after the body
  and before mandatory reads;
- mandatory read files (skill-local required reads only, no navigation paths);
- contextual read files;
- skill-local repository context via those reads.

Example rendered Markdown:

```markdown
---
name: spectask-execute
description: Execute approved spectasks.
---

Use this skill body...

Before this skill, if the Spawn block instructions from `AGENTS.md` are not
loaded, read `AGENTS.md` first.

Optional when hints exist:

Hints:
- Prefer spectask steps in order.

Mandatory reads:
- `spec/main.md` - Spec task process.

Contextual reads:
- `spec/design/hla.md` - Read when architecture context is needed.
```

Rendered skills are the active skill surface. Source skills in
`spawn/.extend/{ext}/skills/` are not read directly by agents.

Rendered skill filenames should be stable for each IDE adapter. **Across
installed extensions**, normalized skill names must be unique; duplicates are a
hard error before render (`utility.md`, Cross-extension rendered identity). The
adapter does not rename or namespace to hide conflicts.

## Local Rules

`spawn/rules/` is target-owned. Rules can capture team conventions, local
processes, domain notes, and project-specific constraints without modifying an
extension.

`save-rules-navigation()` keeps navigation aligned with this folder:

- new rule files are added to `read-required -> rules` by default;
- missing rule files are removed from navigation with a warning.

## Coherent AIDD Experience

Spawn separates packaging from experience:

- extension authors write `extsrc/config.yaml`, source skills, files, setup
  scripts, and MCP definitions;
- the utility installs those sources into `spawn/.extend/{ext}`;
- the utility renders `spawn/navigation.yaml`, IDE skills, MCP config, and
  ignore files;
- agents read the rendered surface, not the extension package internals.

Because every IDE adapter receives the same normalized skill, MCP, and read
metadata, the AIDD workflow is consistent across Cursor, Codex, Qoder,
Claude Code, Qwen Code, Windsurf, GitHub Copilot, Aider, Zed, Gemini CLI, and
Devin even when their storage formats differ.

## Example End-To-End Flow

1. A user asks the agent to execute a methodology task.
2. The IDE sees a rendered skill whose name or description matches the request.
3. The entrypoint instruction in the skill tells the agent to read the IDE
   entry file when its Spawn block is not in context.
4. The agent reads all `read-required` files and selects relevant
   `read-contextual` files by description.
5. The agent reads the skill's local required files and any skill-specific
   required reads.
6. The agent performs the task in the target repository.
7. If files under `spawn/rules/` changed, a later Spawn refresh syncs
   navigation so future agents discover the new or removed rules.

This is the main AIDD experience Spawn is trying to preserve: methodology
source is packaged once, rendered into each IDE's native surface, and then
combined with target-local rules at task time.
