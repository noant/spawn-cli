# 4: Deduplicate navigation and skill reads (read-required wins)

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
Ensure the same repository-relative file never appears under both **read-required** and **read-contextual** for a given extension: **read-required takes precedence**, and duplicates are removed from contextual lists in merged navigation and rendered skill metadata.

## Design overview
- **Affected modules:**
  - `src/spawn_cli/core/low_level.py` — `generate_skills_metadata` (build `required_paths` / `auto_out` using **normalized path keys** for set membership so optional/automatic reads cannot slip in under another spelling); `save_extension_navigation` (before writing `read-contextual` `{ ext, files: [...] }`, **drop any contextual `SkillFileRef` whose normalized path is already in `read_required_files`**).
  - `tests/core/test_low_level.py` — regression tests for overlapping required/contextual inputs (metadata and navigation persistence).
- **Data flow changes:** `refresh_navigation` and `refresh_skills` / IDE skill render continue to call the same entry points; emitted `spawn/navigation.yaml` and `SkillMetadata` no longer list the same logical path twice across mandatory vs contextual sections.
- **Integration points:** No changes to extension config schema or IDE adapters; behavior is centralized in low-level merge helpers.

## Before → After

### Before
- A path can appear in **Mandatory reads** and **Contextual reads** in the same rendered `SKILL.md` (e.g. mixed path spellings in `required_paths` vs `required_key_set`, or overlapping global required vs global auto lists passed into `save_extension_navigation`).
- `spawn/navigation.yaml` can contain the same `path` under both `read-required` and `read-contextual` for one extension block.

### After
- For each skill and for each extension navigation write: every path is classified **once**; if it is required, it is **not** listed as contextual.
- Deduplication uses the existing helper `_norm_read_path` (`Path(...).as_posix()`, slash normalization) for identity.

## Details

### Recorded clarifications / defaults
- **Precedence:** Required always wins; contextual entries that match a required path (after normalization) are **omitted**, not merged.
- **Descriptions:** When removing a contextual duplicate, keep the **required** side description only (contextual text is discarded for that path).
- **Rules groups:** This task targets **`{ ext, files: [...] }`** navigation blocks from extensions (skill-facing file lists). Do **not** change `save_rules_navigation` unless a future task shows the same bug for `rules:` lists.
- **Order:** Preserve stable ordering within each list (first-seen wins in required; contextual order unchanged except for dropped items).
- **Tests:**
  - **Metadata:** Construct a scenario where the same logical path is contributed to required and auto (e.g. two spellings or overlapping lists) and assert the rendered `SkillMetadata` has the path **only** in `required_read`.
  - **Navigation:** Call `save_extension_navigation` with overlapping `read_required_files` and `read_contextual_files`, reload YAML, and assert no contextual `files` entry shares a normalized path with that extension’s required `files` list.
