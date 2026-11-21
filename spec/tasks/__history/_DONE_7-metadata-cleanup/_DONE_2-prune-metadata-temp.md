# 2-prune-metadata-temp

## Goal

Automatically reduce orphaned UUID staging folders under `spawn/.metadata/temp/` without requiring manual deletion or full temp wipes.

## Approach

1. Implement `prune_metadata_temp(parent: Path, *, max_age_seconds: int = 86400, reserved: str | None = None)` in `spawn_cli/core/low_level.py` or colocated module used by download staging:
   - If `parent` is not a directory, return.
   - For each child **directory**: accept the name as a staging UUID only if `uuid.UUID(name)` succeeds (standard library); skip if `reserved` is set and `name == reserved`. If directory mtime is older than `max_age_seconds`, `shutil.rmtree(child, ignore_errors=True)`.
2. Invoke from `spawn_cli/core/download.py` inside `_stage_extension` after assigning `temp_base = parent / op` and `ensure_dir(temp_base.parent)`: call `prune_metadata_temp(parent, reserved=op, ...)` immediately **before** the `try:` that stages sources into `temp_base`, so stale siblings disappear while the freshly chosen `op` is never targeted.
3. Keep failure modes non-blocking: swallowed `OSError`-family except where tests require visibility (none).

Constants: reuse `86400` as default or extract named constant in module.

## Affected files

- `src/spawn_cli/core/download.py` — `_stage_extension`.
- `src/spawn_cli/core/low_level.py` — prune helper exports or import from download if cyclic imports force colocation (prefer lowest layer without cycles).

## Tests

- Create fake `spawn/.metadata/temp/<uuid-old>/` at `mtime` patched to distant past plus `spawn/.metadata/temp/<uuid-new>/` as current staging name (or call prune with explicit `reserved`); assert old removed, reserved kept.
- Use `unittest.mock` or pathlib-friendly approach consistent with repo tests.

## Code sketch

```python
def prune_metadata_temp(parent: Path, *, max_age_seconds: int, reserved: str | None) -> None:
    now = time.time()
    ...
    try:
        uuid.UUID(name)
    except ValueError:
        continue
```
