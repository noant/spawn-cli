# Step 1: Low-level behavior and tests

## Goal
Implement hint-only **`read-required` → `rules`** rows: persist through **`save_rules_navigation`**, collect into maintainer hint streams, and keep mandatory reads derived only from **`path`** rows.

## Approach

1. **`save_rules_navigation` — `prune`**
   - Split logic so rows are retained when:
     - (**`path`** valid non-empty string after strip/normalize → refers to existing file): emit **`path`**, **`description`**, optional **`hint`** (current shape).
     - Else if **`path`** present (key exists) but missing, not a file on disk, or whitespace-only / empty after normalize: warn as today when a concrete missing path was intended, then **drop the entire row** — do **not** salvage **`hint`** into a hint-only row (invalid **`path`** wins).
     - Else if **no usable file-backed **`path`** but **`hint`** strips to non-empty: emit hint-only mapping (omit **`path`** key; at least **`hint`**; include **`description`** only if present and non-trivial per existing string conventions).
   - Preserve relative order of surviving rows.
   - Optionally emit **`SpawnWarning`** for entries with neither a usable file-backed **`path`** nor a non-empty **`hint`** after strip (e.g. empty dict fragment or stub row).

2. **`_navigation_read_required_rule_hints_ordered`**
   - When iterating **`read-required`** **`rules`** entries, append **`hint`** for:
     - file-backed rows (existing), and
     - hint-only rows (**`hint`** string after strip).
   - Ignore empty/strip-only-whitespace **`hint`** (do not append).

3. **`_navigation_rules_refs_from_section`**
   - No change required if it already skips entries without a non-empty **`path`**; verify hint-only rows never produce **`SkillFileRef`**.

   **`read-contextual` → `rules` prune:** unchanged and **out of scope** for rollup — keep current behavior where only entries with **`path`** survive; standalone contextual **`hint`** rows continue to **not** be supported.

4. **Models / tests typing**
   - If **`NavRulesGroup`** / **`NavFile`** strict validation blocks representative hint-only payloads in **`tests/models/test_navigation.py`**, extend models or tests so hint-only shapes are documented (optional **`path`**, **`hint`** present) without breaking existing fixtures.

5. **Tests** in **`tests/core/test_low_level.py`**
   - New test(s): navigation with **`read-required` → `rules`** mixing hint-only and file-backed rows → after **`save_rules_navigation`**, hint-only survives; **`_navigation_yaml_rules_refs`** first tuple (required rules refs) / **`generate_skills_metadata`** **`required_paths`** excludes hint-only from mandatory paths.
   - New or extended test: ordered maintainer hints via **`_navigation_read_required_rule_hints_ordered`** (or public **`rollup_hints_for_agents`** if easier) matches YAML list order across hint-only and **`path`+`hint`** rows.
   - Regression: **`path`** to missing file plus non-empty **`hint`** → row removed entirely after save; hint text does **not** appear in ordered maintainer hints.
   - Regression: whitespace-only **`hint`** does not contribute to ordered hints post-merge (or filtered at collection — either way observable via rollup/skills ordering tests).
   - Optional: **`read-contextual` → `rules`** remains path-only after save (standalone hint contextual rows absent or stripped).

## Affected files (expected)

- **`src/spawn_cli/core/low_level.py`** — **`save_rules_navigation`**, **`_navigation_read_required_rule_hints_ordered`** (and verification pass over **`_navigation_rules_refs_from_section`**).
- **`tests/core/test_low_level.py`**
- Optionally **`src/spawn_cli/models/navigation.py`**, **`tests/models/test_navigation.py`**

## Constraints

- Block-style YAML policy for nested navigation writes remains unchanged ([task 3](../_DONE_3-block-yaml-serialization/overview.md)).
- Do not ingest **`read-contextual`** rule hints (task 18 behavior).
