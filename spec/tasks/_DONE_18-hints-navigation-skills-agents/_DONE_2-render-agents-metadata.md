# Step 2: Skill metadata, render order, AGENTS entrypoint

## Goal
Expose **`hints`** on **`SkillMetadata`**, render them in skills **after body / before mandatory reads** with **truncate** + warnings, assemble **AGENTS** hint bullets **without truncation** but with **warnings** and remediation text when limits are exceeded, and reuse one hint-rollup helper where practical.

## Approach
1. **`SkillMetadata`:** add **`hints: list[str]`** (final strings prepared for render / AGENTS measurement).
2. **`generate_skills_metadata`:** collect per skill:
   - **Maintainer:** **`hint`** only from **`read-required` → `rules`** rows (**ignore** **`hint`** on **`read-contextual` → `rules`**).
   - **Extension global / local:** from **`ExtensionConfig`** (not from YAML mirror) for correct timing with extension blocks.
   - Dedup (strip + identical string).
   - Apply **512** per-hint truncate + **`SpawnWarning`** when truncating.
   - For **skill render payload:** enforce **4096** total character budget with final **`...`** truncation + warning when clipping.
3. **`render_skill_md`:** after **`skill.content`**, non-empty **Hints** section (bullets), blank line, then **Mandatory reads** / **Contextual reads**.
4. **Rollup helper** (e.g. in `high_level` or `low_level`): build ordered deduped hint list for AGENTS (**global extension + read-required maintainer only**); **do not** truncate strings for AGENTS output; if any hint length **> 512** or combined length **> 4096**, **`SpawnWarning`** with message to shorten hints and/or reduce extensions.
5. **`refresh_entry_point`:** compose managed-block string: static spine + **Hints** bullets (**full text**); run measurement/warnings from step 4.
6. **Tests:** `render_skill_md` hint placement; skill truncation ellipsis; AGENTS composition includes full oversized hint and emits expected warning behavior (where testable).

## Affected files (expected)
- `src/spawn_cli/models/skill.py`
- `src/spawn_cli/core/low_level.py` (`generate_skills_metadata`, navigation rule hint parsing for **read-required** only)
- `src/spawn_cli/ide/_helpers.py` (`render_skill_md`)
- `src/spawn_cli/core/high_level.py` (`refresh_entry_point`, shared rollup / warnings)
- `tests/core/test_low_level.py`, IDE helper tests as needed

## Notes
- Keep **`spawn/navigation.yaml`** last among mandatory reads (task 16).
- **`refresh_extension_for_ide` → `refresh_navigation`** lives in step 1; step 2 assumes navigation can be current when entry point runs after full refresh paths.
