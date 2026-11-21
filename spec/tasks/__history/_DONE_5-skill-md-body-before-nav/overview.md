# 5: Rendered skill body before read lists; navigation path last in mandatory reads

IMPORTANT: always use `spawn/navigation.yaml` and `spec/main.md` for rules.

## Status
- [V] Spec created
- [V] Self spec review passed
- [V] Spec review passed
- [V] Code implemented
- [V] Self code review passed
- [V] Code review passed
- [V] HLA updated

## Goal
Change the rendered IDE `SKILL.md` layout so the **extension skill source body** appears immediately after YAML frontmatter, and the generated **Mandatory reads** / **Contextual reads** sections follow; ensure `spawn/navigation.yaml` is always the **last** bullet under Mandatory reads (path identity after the same normalization as read dedup: POSIX segments).

## Design overview
- **Affected modules:** `src/spawn_cli/ide/_helpers.py` — `render_skill_md` (section order; build mandatory list with `spawn/navigation.yaml` deduplicated and pinned to the end; drop the standalone `Read \`spawn/navigation.yaml\` first.` line).
- **Tests:** `tests/ide/test_registry.py` (`test_render_skill_md_minimal`, `test_render_skill_md_full`, ordering / dedup cases); `tests/ide/test_cursor.py` — `test_add_skills_creates_file` currently asserts `Read \`spawn/navigation.yaml\` first.`; replace with assertions for body-before-list and `spawn/navigation.yaml` last under Mandatory reads.
- **Documentation (Step 7):** `spec/design/ide-adapters.md` — **Skill Rendering** numbered list and the **Markdown Skill Shape** / **Cursor MDC Fallback** examples must match the new order (body before lists; `spawn/navigation.yaml` as last mandatory bullet, not a pre-list line).
- **Data flow:** `generate_skills_metadata` output is unchanged; only the Markdown assembly in `render_skill_md` changes. IDE adapters keep calling `render_skill_md`.

## Before → After

### Before
- After frontmatter: `Read \`spawn/navigation.yaml\` first.`, then Mandatory reads, Contextual reads, then skill body.

### After
- After frontmatter: skill body, then Mandatory reads (with `spawn/navigation.yaml` last when the section is present), then Contextual reads.
- No separate “read navigation first” line above the lists.

## Details

### User clarifications (defaults)
- **Mandatory reads:** Always emit a **Mandatory reads** section so agents see the navigation manifest; it must include `spawn/navigation.yaml` exactly once, **last** among mandatory bullets.
- **If already present:** Any existing `SkillFileRef` whose normalized path equals `spawn/navigation.yaml` is **not duplicated**; keep the **existing description** and **move** that entry to the end of the mandatory list.
- **If absent:** Append `- \`spawn/navigation.yaml\` - {description}` with description: **`Merged Spawn navigation (read-required, read-contextual).`** (ASCII, fixed string in code unless a single shared constant already exists — prefer one module-local constant in `_helpers.py`).
- **Empty body:** Still valid; body may be empty between frontmatter and the lists.
- **Contextual reads:** Unchanged except for position after mandatory section (still before nothing else).

### Non-goals
- Do not change YAML merge / `generate_skills_metadata` ordering of `required_read` for non-render consumers unless a test proves a shared contract requires it (none today).
- Do not change `AGENTS.md` / spawn block text in this task unless implementation reveals a hard dependency (unlikely).

### Tests to add or adjust
- **Minimal meta:** Assert no `Read \`spawn/navigation.yaml\` first.`; assert body appears before `Mandatory reads:`; assert mandatory section includes `spawn/navigation.yaml` as the **last** `- \`...\`` line in that section.
- **Full meta:** When `required_read` already contains `spec/main.md` and `spawn/navigation.yaml` in the wrong order, rendered output lists `spec/main.md` first and `spawn/navigation.yaml` last.
- **Dedup:** `required_read` contains `spawn/navigation.yaml` twice (e.g. different slash spelling) → single entry at end; compare paths with the same normalization as `low_level._norm_read_path` (implementation may call that symbol from `_helpers` — no import cycle with `low_level`).

### Self spec review notes
- Single cohesive change: `render_skill_md`, IDE tests, Step 7 doc sync in `spec/design/ide-adapters.md`.
- MDC fallback narrative in `ide-adapters.md` references the old line; update examples to match rendered output.
