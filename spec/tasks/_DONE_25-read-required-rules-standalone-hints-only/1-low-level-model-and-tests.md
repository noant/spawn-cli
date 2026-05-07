# Step 1: Low-level behavior, model validation, tests

## Goal
Implement standalone-only maintainer rule hints for **`read-required`** and lock in regressions.

## Approach
1. **`NavRuleRow`**: Replace “path and/or hint” with **mutual exclusivity**: a non-empty stripped **`path`** cannot coexist with a non-empty stripped **`hint`**. Update module docstring accordingly.
2. **`_navigation_read_required_rule_hints_ordered`**: Include a hint string **only** from rows **without** a non-empty stripped **`path`** field (hint-only rows). Rows that still have both in an unmigrated file are unchanged on disk until refresh, but rollup ignores path-bound **`hint`** immediately.
3. **`save_rules_navigation` → `prune_read_required_rules`**: For each surviving file-backed row, **never** write **`hint`**. If input had non-empty stripped **`hint`**, write the file row without it, then append a hint-only row **immediately after** with that hint; **`SpawnWarning`** per migrated row with actionable wording.
4. **Tests** (`tests/core/test_low_level.py`, `tests/models/test_navigation.py`):
   - **`NavRuleRow` / `NavRulesGroup`**: `model_validate` **fails** when **`path`** and **`hint`** are both non-empty (after strip rules consistent with the model).
   - Replace or adjust tests that expected **`hint`** preserved on file-backed rows (`test_save_rules_navigation_preserves_hint_on_rules_rows` and any rollup test using **`path`+`hint`** on required rules) to match migration + rollup rules.
   - **`_navigation_read_required_rule_hints_ordered`**: with a hand-built **`navigation.yaml`** that still has **`path`+`hint`** on one row **before** save, assert the path-bound hint is **excluded**; after **`save_rules_navigation`**, assert YAML has no **`hint`** on path rows and hint appears in a following hint-only row; rollup order matches.
   - Keep task 24 regressions for hint-only rows, invalid paths, empty junk rows, contextual ignore — adjust expectations only where they assumed path-row hints counted toward rollup or were stored on path rows.

## Affected files
- `src/spawn_cli/models/navigation.py`
- `src/spawn_cli/core/low_level.py`
- `tests/core/test_low_level.py`
- `tests/models/test_navigation.py`

## Code examples (illustrative)

**Authoring after change:**

```yaml
read-required:
  - rules:
      - path: spawn/rules/00-general.md
        description: General conventions.
      - hint: Prefer MemPalace search before ripgrep when available.
```

**Forbidden shape (validation / refresh will normalize away):**

```yaml
      - path: spawn/rules/team.yaml
        hint: Same line as path — do not use.
```
