# 1: Low-level sync and tests

## Goal
Implement overwrite semantics for core config on refresh and update unit tests.

## Approach
- In `spawn_cli.core.low_level`, change the refresh helper so it loads and validates `default_core_config.yaml`, optionally renames the function to match overwrite semantics, and writes that model to `spawn/.core/config.yaml` via existing `save_yaml` (no union with previous `agent-ignore`).
- Update `spawn_cli.core.high_level` import if the symbol is renamed; update `low_level.__all__` if the public name changes.
- In `tests/core/test_low_level.py`, replace expectations that preserve extra globs with expectations that the output equals the bundled default only; keep invalid/empty core config tests aligned with messages.

## Affected files
- `src/spawn_cli/core/low_level.py`
- `src/spawn_cli/core/high_level.py` (import only if rename)
- `tests/core/test_low_level.py`

## Code examples

```python
# After refresh, disk file matches bundled default CoreConfig serialization.
# Pseudocode — follow existing save_yaml / CoreConfig patterns in-repo.
bundled_core = CoreConfig.model_validate(...)
save_yaml(path, bundled_core.model_dump(by_alias=True))
```
