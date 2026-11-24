# 24: Hint-only rows under read-required rules

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
Allow maintainer-authored **`hint`** entries under **`read-required` → `rules`** without a **`path`**, preserved across **`spawn rules refresh`** / **`spawn refresh`** and merged into the same hint pipelines as row-level hints on file-backed rules (skills **Hints** block and **`AGENTS.md`** rollup).

## Design overview
- Affected modules: **`spawn_cli.core.low_level`** — **`save_rules_navigation`** (`prune`, path discovery), **`_navigation_read_required_rule_hints_ordered`** (hint collection order); optionally **`spawn_cli.models.navigation`** if typed **`NavRulesGroup`** / tests should accept hint-only dict shapes; **`tests/core/test_low_level.py`** regressions; **README** and **`spec/design/agentic-flow.md`** / **`spec/design/user-guide.md`** (Step 7 scope carried by subtask 2).
- Data flow changes: **`_navigation_rules_refs_from_section`** continues to emit **`SkillFileRef`** only for rows with a non-empty **`path`** — hint-only rows **never** become mandatory reads. Maintainer hints from **`read-required`** include both **`hint`** on path rows and **hint-only** rows, in **YAML list order**, before downstream dedupe/truncation unchanged from task 18.
- Integration points: **`rollup_hints_for_agents`**, **`generate_skills_metadata`** — no signature change if hint collection stays centralized in **`_navigation_read_required_rule_hints_ordered`**; **`save_rules_navigation`** remains the single mutator for rules-group hygiene.

## Before → After
### Before
- Under **`read-required` → `rules`**, every surviving row must include **`path`** pointing at an existing file under **`spawn/rules/`**; rows with only **`hint`** are dropped by **`prune`** (they lack **`path`**).
- Authors who want standalone reminders must duplicate a **`path`** or fold text into one **`hint`** string on an existing rule file row.

### After
- A **`rules`** row may be **file-backed** (**`path`** required to exist on disk, optional **`hint`**), or **hint-only**: non-empty stripped **`hint`**, no **`path`** (**`description`** only when present and non-trivial — same YAML emission conventions as other navigation rows — and never treated as a mandatory read label).
- Hint-only rows survive **`save_rules_navigation`** and contribute their **`hint`** string to the same ordering/dedup/limit behavior as today’s **`read-required`** rule **`hint`** fields.
- Mandatory read lists and skill **`required_paths`** remain driven only by rows with **`path`** (unchanged).

## Details

### Authoring shape (canonical examples)

**File-backed (unchanged):**

```yaml
read-required:
  - rules:
      - path: spawn/rules/00-general.md
        description: General conventions.
        hint: Optional reminder tied to that file.
```

**Hint-only (new):**

```yaml
read-required:
  - rules:
      - hint: Standalone reminder with no backing rule file path.
```

**Mixed order:** hints from hint-only rows interleave with hints from **`path`** rows according to their position in the **`rules`** list.

### Validation / pruning (`save_rules_navigation`)

| Row shape | Behavior |
|-----------|----------|
| **`path`** key present but file missing on disk (with or without **`hint`**) | **`SpawnWarning`**, entire row removed; **`hint`** is **not** converted to hint-only (today’s invalid-path semantics). |
| **`path`** present, file exists | Row kept; **`description`** default/filled as today; optional **`hint`** preserved (unchanged). |
| No usable **`path`**, non-empty stripped **`hint`** | Row kept as hint-only (minimal YAML: at least **`hint`**; **`description`** only when non-trivial under existing conventions). |
| Neither usable **`path`** nor non-empty **`hint`** | Row dropped; optional **`SpawnWarning`** for “junk” rows (explicitly allowed in implementation subtask). |

**`description`** on hint-only rows: emit only when present and non-trivial, following the same string/YAML conventions as other navigation **`rules`** rows; never treated as a mandatory read label without a **`path`**.

### Rollup and skills

- **`read-contextual` → `rules`**: **unchanged** from task 18 — contextual rule **`hint`** fields are **not** ingested into skills/AGENTS. Hint-only rows under **`read-contextual`** are **out of scope** (they remain subject to current **`prune`** unless separately specified; recommend authors use **`read-required`** only).
- Dedupe, per-hint and combined limits, warnings — **same behavior** as **`_DONE_18-hints-navigation-skills-agents`** ([overview](../_DONE_18-hints-navigation-skills-agents/overview.md)).

### Tests (minimum)

- **`save_rules_navigation`** preserves one or more hint-only rows alongside file-backed rows; disk scan still appends missing rule files as today.
- **`_navigation_read_required_rule_hints_ordered`** returns hints from hint-only rows in order; combined with **`path`+`hint`** rows matches documented interleaving.
- Regression: hint-only rows do not appear in **`_navigation_yaml_rules_refs`** **`read-required`** rules refs / **`generate_skills_metadata`** **`required_paths`** derivation.
- Row with **`path`** pointing at a missing file and a non-empty **`hint`**: row is removed in full (hint is **not** downgraded to hint-only — same semantics as today’s prune for invalid paths).
- Row with neither a usable **`path`** nor a non-empty stripped **`hint`**: dropped; if **`SpawnWarning`** is emitted for this junk shape, cover it once.
- **Whitespace-only **`hint`** after strip**: does not contribute to ordered maintainer hints (same net effect as today’s rollup merge, which strips before dedupe).
- **`read-contextual` → `rules`**: out of scope for hint rollup; optionally assert unchanged behavior — entries still require a **`path`** with a surviving file after **`save_rules_navigation`** prune (standalone **`hint`** rows there are **not** supported).

### Non-goals

- Ingesting **`read-contextual`** hints or hint-only contextual rows into AGENTS/skills.
- Replacing extension-owned **`hints`** blocks or **`hints.global`** authoring.
- Multiple hints per row (still a single **`hint`** string field).

### Implementation clarifications (Step 1.1 defaults)

- **Equivalence:** “**`path`** and **`hint`** equally valid” means a row may carry **only **`path`**, only **`hint`**, or both** (both only when **`path`** points to an existing file); not mutual exclusivity.
- **Scope:** Feature defined for **`read-required` → `rules`** only.

## Execution Scheme
> Each step id is the subtask filename (e.g. `1-abstractions`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.
- Phase 1 (sequential): step `_DONE_1-low-level-and-tests.md` → step `_DONE_2-documentation.md`
