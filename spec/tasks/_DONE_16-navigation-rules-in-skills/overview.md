# 16: Merge navigation rules into rendered skills

## Source seed
- Path: none

## Status
- [x] Spec created
- [x] Self spec review passed
- [x] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [x] Code review passed
- [x] HLA updated

## Goal
When Spawn renders IDE skills, include repository rule paths from `spawn/navigation.yaml` (`read-required` / `read-contextual` → `rules` groups) in each skill’s mandatory and contextual read lists so agents using a skill see the same rule files as navigation without relying on a second manual mechanism.

## Design overview
- Affected modules: `spawn_cli.core.low_level` (`generate_skills_metadata` and a small helper to load rule refs from merged `spawn/navigation.yaml`), tests under `tests/core/test_low_level.py`; optionally short clarifications in `spec/design/agentic-flow.md` (wording that today implies skills may omit repo rules when navigation already lists them).
- Data flow changes: navigation YAML (already merged on disk) becomes an additional input to skill metadata assembly; rule paths are normalized and deduplicated with existing extension-driven required/auto lists using the same path-normalization rules as today (**read-required** wins over **read-contextual** when the same path appears in both).
- Integration points: IDE adapters unchanged — they keep consuming `SkillMetadata` from `render_skill_md`; `spawn/navigation.yaml` remains last in the mandatory block per existing adapter helper.

## Before → After
### Before
- `save_rules_navigation` / extension navigation merges write `rules` entries under `read-required` and `read-contextual` in `spawn/navigation.yaml`.
- `generate_skills_metadata` merges only per-skill `required-read`, extension `localRead` / `globalRead` flags — **not** navigation `rules` lists — so rendered “Mandatory reads” / “Contextual reads” can omit `spawn/rules/...` even when navigation mandates them.

### After
- Loading `spawn/navigation.yaml` (if present and parseable) adds:
  - each `read-required` → `rules` entry to the skill’s mandatory read set (with descriptions from navigation);
  - each `read-contextual` → `rules` entry to the skill’s contextual read set, unless the path is already mandatory (extension config, global required, local required, or required rules).
- Ordering: preserve existing relative order within `generate_skills_metadata` (skill-owned and extension refs first, then navigation rule refs inserted in a stable rule — e.g. after extension-merge lists, before final dedup pass); `render_skill_md` continues to force `spawn/navigation.yaml` last among mandatory reads.

## Details
- **Source of truth:** `spawn/navigation.yaml` remains canonical for which rule files are required vs contextual; skills do not introduce a duplicate authoring surface for rules.
- **Non-goals (this task):** new hint/snippet file formats, AGENTS.md body generation beyond existing entrypoint, CI duplication checks, or changing spectask extension `config.yaml` defaults — those stay follow-ups unless the user expands scope at review.
- **Empty / missing navigation:** no rule injection; behavior matches today for the extension-only merge.
- **Malformed navigation:** follow existing project pattern for navigation loads in low_level (no crash; treat missing `read-required` / `read-contextual` as empty lists).
- **Related brainstorm (no seed linkage):** `spec/seeds/_DONE_3-short-hints-navigation-skills.md` is a broader idea (compact hints without opening whole files, single snippet source-of-truth, AGENTS ergonomics); this task deliberately does **not** close or claim that seed — it only fixes **navigation `rules` → rendered skill read lists**.

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step _DONE_1-core-merge-and-tests → step _DONE_2-agentic-docs
