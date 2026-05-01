# Step 1: Core navigation merge, validation, and tests

## Goal
Extend navigation merge and persistence so extension **global** hints land under merged **`read-required`** **`ext`** entries (`hints` list), maintainer **`hint`** on **`read-required`** **`rules`** rows survives **`save_rules_navigation`** sync, validation emits **`SpawnWarning`** for length violations, and **`refresh_extension_for_ide`** refreshes navigation.

## Approach
1. **`ExtensionConfig`** (or adjacent parsing): add **`hints`** per canonical **`overview.md`** (`hints.global` / `hints.local` string lists); validate plain strings only.
2. **`save_extension_navigation`**: write **`hints`** (global) into the `- ext:` dict alongside **`files`**; strip, drop empties, dedupe strings after strip before append.
3. **`save_rules_navigation`**: preserve **`hint`** on surviving rows in **both** required and contextual **`rules`** lists when syncing paths/descriptions — ingestion ignores contextual **`hint`** elsewhere, but dropping keys accidentally regresses manual YAML.
4. **Per-hint enforcement:** hints longer than **512** codepoints after strip → **`SpawnWarning`** + **truncate to 512** for any pipeline that truncates (skills path); AGENTS assembly measures full strings for warnings without truncating output.
5. **Unit tests:** round-trip **`hints`** on ext blocks; **`hint`** preserved on **`read-required`** rule rows through prune/sync; oversized hint triggers warning + truncation where applicable.

## Approach — refresh wiring
6. **`high_level.refresh_extension_for_ide`:** after existing MCP/skills/agent-ignore work, call **`refresh_navigation(target_root)`** so **`spawn/navigation.yaml`** (extension mirrors + rules sync) matches installed packs before callers rely on merged YAML.

## Affected files (expected)
- `src/spawn_cli/core/low_level.py` (`save_extension_navigation`, `save_rules_navigation`, helpers)
- `src/spawn_cli/models/config.py` (or equivalent extension schema)
- `src/spawn_cli/core/high_level.py` (`refresh_extension_for_ide`)
- `tests/core/test_low_level.py`

## Code examples (illustrative)

Merged navigation snippet (`read-required`):

```yaml
read-required:
  - rules:
      - path: spawn/rules/00-general.md
        description: Local conventions.
        hint: Keep replies concise.
  - ext: spectask
    files:
      - path: spec/main.md
        description: Methodology.
    hints:
      - Prefer spectask steps in order.
```

Extension **`config.yaml`** (authoring):

```yaml
hints:
  global:
    - Prefer spectask steps in order.
  local:
    - This skill expects Step 3 approval before coding.
```
