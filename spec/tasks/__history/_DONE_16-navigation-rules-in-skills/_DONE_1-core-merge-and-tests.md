# 1: Core merge + tests

## Goal
Implement navigation `rules` extraction and merge into `generate_skills_metadata`, with regression tests.

## Approach
1. Add a helper (module-private is fine) that loads `spawn/navigation.yaml` from the target root, walks `read-required` and `read-contextual` list items for dicts keyed by `rules`, and returns two `list[SkillFileRef]` (required rules, contextual rules) with `path` / `description` from each entry (skip non-dicts, empty paths).
2. In `generate_skills_metadata`, after building the existing `required_paths` / `required_out` / `auto_out` logic, merge in:
   - required-rule refs: same dedup key as today (`_norm_read_path`); if a rule path is already mandatory, skip duplicate; descriptions from navigation when present.
   - contextual-rule refs: add to `auto_out` only if not already in the mandatory key set and not duplicate in `auto_out`.
3. Keep `spawn/navigation.yaml` handling in `render_skill_md` / `_mandatory_reads_for_render` unchanged (still deduped and last).
4. Tests in `tests/core/test_low_level.py` (or adjacent): temporary repo with minimal extension config + one skill + `navigation.yaml` containing `read-required` and `read-contextual` `rules` blocks; assert rendered metadata lists include expected rule paths and that a rule listed only under `read-required` does not appear as contextual; optional case where the same path appears in both tiers — mandatory wins.

## Affected files
- `src/spawn_cli/core/low_level.py`
- `tests/core/test_low_level.py`

## Code examples
None.
