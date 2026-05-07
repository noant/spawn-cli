# 25: Standalone maintainer hints only for read-required rules

## Source seed
- Path: none

## Status
- [x] Spec created
- [x] Self spec review passed
- [x] Spec review passed
- [x] Code implemented
- [x] Self code review passed
- [x] Code review passed
- [x] Design documents updated

## Goal
Stop supporting **`hint`** on file-backed **`read-required` → `rules`** rows so hints are only **standalone** hint-only rows (or extension **`hints`** lists), avoiding confusion between mandatory paths and free-form reminders.

## Design overview
- Affected modules: **`spawn_cli.core.low_level`** — **`_navigation_read_required_rule_hints_ordered`**, **`save_rules_navigation`** (`prune_read_required_rules`); **`spawn_cli.models.navigation`** — **`NavRuleRow`** validation; **`tests/core/test_low_level.py`**, **`tests/models/test_navigation.py`**; **`spec/design/agentic-flow.md`**, **`spec/design/user-guide.md`** (Step 7 via subtask 2); root **`README.md`** only if it documents the old shape.
- Data flow changes: Rollup pipelines (AGENTS / skill metadata) ingest maintainer rule hints **only** from rows **without** a non-empty stripped **`path`** field. Surviving file-backed rows are **never** written with a **`hint`** key; if refresh sees **`path`** plus non-empty **`hint`**, it **migrates** by emitting the file row without **`hint`** and inserting a **hint-only** row **immediately after** preserving hint text and order for rollup.
- Integration points: **`rollup_hints_for_agents`**, **`generate_skills_metadata`** unchanged at call sites; extension **`hints.global`** / navigation **`hints`** under **`- ext:`** blocks stay as today. **`read-contextual` → `rules`** authoring and prune behavior stay **out of scope** (no change unless a trivial doc alignment is needed).

## Before → After
### Before
- A **`read-required` → `rules`** row may be file-backed with optional **`hint`** on the same mapping entry, **or** hint-only, **or** both **`path`** and **`hint`** (task 24). The same hint bullet pipelines merge hints from **`hint`** on path rows and from hint-only rows.

### After
- File-backed **`read-required` → `rules`** rows carry **`path`** (and **`description`** only); **`hint` must not appear** on that YAML row after refresh.
- Maintainer reminders use **hint-only** rows (and/or extension lists). **`_navigation_read_required_rule_hints_ordered`** ignores **`hint`** when the row has a non-empty stripped **`path`** so behavior is correct even before the next refresh.
- **`NavRuleRow`** rejects validation when both a non-empty **`path`** and a non-empty stripped **`hint`** are present.

## Details

### Rationale
Tying **`hint`** to a **`path`** suggests the hint is “about” that mandatory file; standalone rows and extension **`hints`** make global reminders explicit.

### Migration on `save_rules_navigation`
When a rule row has a **surviving** file-backed path **and** a non-empty stripped **`hint`**:
1. Append to the pruned list a normal file row (`path`, `description`) **without** **`hint`**.
2. Append **next** a minimal hint-only row with that hint string (strip for storage; optional **`description`** only if present and non-trivial per existing conventions).
3. Emit **`SpawnWarning`** once per migrated row with short, actionable text (e.g. that the hint was moved to a standalone row).

**Do not** migrate when the path is missing or invalid (row removed as today; hint is **not** salvaged — same as task 24).

### Ordering and dedupe
Hint order follows **YAML list order** after migration (hint-only row immediately after its former file row). Existing **dedupe / limits** for hint streams stay unchanged.

### Non-goals
- Changing **`read-contextual` → `rules`** hint preservation in YAML.
- Extension **`hints`** / **`hints.global`** semantics.
- Multiple **`hint`** fields per row (still one string).

### Implementation clarifications (Step 1.1 defaults)
- **Scope** is **`read-required` → `rules`** maintainer hints only.
- **`NavRuleRow`**: mutual exclusivity — non-empty path **xor** non-empty stripped hint for validation (file-backed rows: path required, hint forbidden; hint-only: hint required, no path).

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `1-low-level-model-and-tests.md` → step `2-design-docs.md`
