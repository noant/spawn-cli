# 18: Short hints in navigation, skills, and AGENTS.md

## Source seed
- Path: spec/seeds/_DONE_3-short-hints-navigation-skills.md

## Status
- [x] Spec created
- [ ] Self spec review passed
- [x] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [x] Code review passed
- [x] HLA updated

## Goal
Carry short plain-text agent hints from extension config and from maintainer-authored navigation `rules` into merged `spawn/navigation.yaml`, rendered IDE skills (after skill body, before mandatory file lists), and the Spawn-managed block of `AGENTS.md` where applicable.

## Design overview
- Affected modules: `spawn_cli.core.low_level` (navigation merge, validation warnings, hint collection helpers), `spawn_cli.models.skill` (`SkillMetadata` extension), `spawn_cli.ide._helpers` (`render_skill_md` section order), `spawn_cli.core.high_level` (`refresh_extension_for_ide`, `refresh_entry_point`), tests under `tests/core/` (and IDE helper tests if split).
- Data flow changes: extension refresh merges **global** hints into the existing per-extension **`read-required`** stanza (`- ext:` / `files` + **`hints`** string list). Maintainer **`hint`** applies **only** to **`rules`** rows under **`read-required`** — **`hint` on `read-contextual` → `rules` rows is ignored** for hint injection (paths/descriptions there behave as today). `generate_skills_metadata` builds per-skill hint lists from **`ExtensionConfig`** (extension hints) plus **`read-required` rule-row hints**; `render_skill_md` prints **Hints** after `content`, before **Mandatory reads**. **`refresh_extension_for_ide`** calls **`refresh_navigation`** so merged navigation (including extension YAML mirrors) stays current when only IDE-facing merge runs.
- Documentation (Step 7): update listed **`spec/design/*.md`** files and **`spec/design/hla.md`** so flows and authoring guides match behavior (see subtask **`3-design-docs.md`**).

## Before → After
### Before
- Navigation `read-required` holds `rules` groups and `- ext:` `files` groups only; no first-class hint strings.
- `SkillMetadata` has no hints; `render_skill_md` goes from body straight to mandatory reads.
- `SPAWN_ENTRY_POINT_PROMPT` is static text; AGENTS.md does not list merged hints.
- `refresh_extension_for_ide` does not refresh navigation.

### After
- Merged navigation includes per-extension **`hints`** (global, from pack config) and optional **`hint`** on **`read-required` → `rules`** rows only.
- Skills carry hints in metadata with **per-hint** and **total** limits (**truncate** with warning).
- AGENTS managed block lists hints **without truncation**; **warnings** when limits exceeded plus recommendation to shorten hints and/or reduce installed extensions.
- End-user / maintainer docs state that **manual edits** in `spawn/navigation.yaml` target **`rules`** sections only — **`- ext:` blocks are machine-owned**.
- `refresh_extension_for_ide` runs **`refresh_navigation`**.

## Details

### Format
- **Plain text only** for every hint (no path indirection, no markdown file include). Newlines inside a hint: discouraged; validation may warn.

### Extension config YAML (**canonical authoring shape**)

Use a top-level **`hints`** map with **`global`** / **`local`** string lists (mirrors existing extension terminology):

```yaml
hints:
  global:
    - Prefer spectask steps in order.
  local:
    - This skill expects Step 3 approval before coding.
```

- **`global`:** merged into **`read-required`** under the `- ext:` entry for this extension as **`hints`** (strip, drop empties, dedupe within merge output).
- **`local`:** injected **only** into skills owned by this extension.

### Maintainer hints
- Optional **`hint`** on **`rules`** rows under **`read-required`** only.
- **`hint` present on `read-contextual` → `rules` rows:** **do not ingest** into skills or AGENTS (may remain in YAML for forward compatibility — ignored by Spawn hint pipelines).
- **`save_rules_navigation`** preserves **`hint`** on surviving **`read-required`** / **`read-contextual`** rows when syncing paths so manual **`read-required`** hints are not wiped; ingestion still skips contextual rows.

### Ordering and placement (rendered skill)
- After **`skill.content`**, emit **Hints** (stable heading), bullet list, deterministic merge order (document in code — subtask 2).
- Then **Mandatory reads** / **Contextual reads** unchanged aside from metadata consumption.

### Dedup
- After strip, **identical strings collapse to one** (first occurrence wins ordering).

### Limits

| Scope | Per-hint max | Total budget | Behavior |
|-------|----------------|--------------|----------|
| **Rendered skills** | **512** Unicode codepoints | **4096** characters for combined hints block | **`SpawnWarning`** when a hint exceeds per-hint max or total exceeds budget; **truncate** over-long single hints to **512**; truncate combined block to **4096** ending with **`...`**. |
| **AGENTS managed block** | Same thresholds for measurement | Same totals | **No truncation.** Emit **`SpawnWarning`** when any hint exceeds **512** OR combined hints text exceeds **4096**, with **recommendation** to shorten hints and/or reduce installed extensions. Still render **full** hint bullets in the managed block. |

### AGENTS.md policy
- Spawn-managed block regenerated on refresh; content outside **`<!-- spawn:start -->`** … **`<!-- spawn:end -->`** untouched.
- **Local** extension hints **not** listed in AGENTS (skills-only).

### Entry point file shape (`AGENTS.md`)

Spawn writes only the **`<!-- spawn:start -->`** … **`<!-- spawn:end -->`** region (`rewrite_managed_block`).

**Illustrative full file:**

```markdown
You may keep permanent repo guidance here; Spawn does not edit this paragraph.

<!-- spawn:start -->
Before working, read `spawn/navigation.yaml`.
Read every file listed under `read-required`.
Inspect `read-contextual` descriptions and read only files relevant to the current task.

Hints:
- Keep replies concise (maintainer hint from read-required rule row).
- Prefer spectask steps in order (extension global hint).
<!-- spawn:end -->

Optional footer: team conventions, links, etc.
```

**Inside the managed block:** static spine + **`Hints:`** bullets (**full text**, no ellipsis truncation). If warnings fire for oversize content, warnings carry remediation text (shorten hints / fewer extensions).

### Pipeline choices (**explicit**)

- **`_refresh_extension_core`:** keep **skills → navigation → entry point** order; **accepted** — no reorder in this task.
- **Skills vs AGENTS vs final `navigation.yaml`:** possible one-pass skew for navigation-derived **rule paths** only — **accepted** for this task (same as today).

### Non-goals
- Cross-extension dependency graphs / seed `1-extension-link-localread-bridge.md`.
- Golden multi-extension fixture repos.
- Changing mandatory read **path** dedup semantics.

### Documentation deliverables (see subtask `3-design-docs.md`)

| File | Change |
|------|--------|
| `spec/design/hla.md` | High-level mention of hints, AGENTS vs skills, navigation ownership. |
| `spec/design/agentic-flow.md` | Navigation merge, skill render hint block, AGENTS rollup behavior and warnings. |
| `spec/design/user-guide.md` | Maintainers edit **`rules`** (and optional **`hint`** under **`read-required`**); **do not** hand-edit **`- ext:`** blocks (machine-owned). |
| `spec/design/extension-author-guide.md` | **`hints.global` / `hints.local`** schema; plain text limits and warnings. |
| `spec/design/ide-adapters.md` | `SkillMetadata.hints`, render section order vs mandatory reads. |
| `spec/design/utility-method-flows.md` | `refresh_extension_for_ide` invokes **`refresh_navigation`**; ordering note if documented there. |

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `_DONE_1-core-merge-validation.md` → step `_DONE_2-render-agents-metadata.md` → step `_DONE_3-design-docs.md`
