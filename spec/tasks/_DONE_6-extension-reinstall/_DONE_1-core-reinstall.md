# Step 1: Core API — reinstall_extension

## Goal
Add `reinstall_extension(target_root: Path, extension: str) -> None` in `src/spawn_cli/core/high_level.py`.

## Approach
1. Call existing `_require_init` / init checks consistent with `update_extension`.
2. If `extension not in ll.list_extensions(target_root)`, raise `SpawnError` with a clear message (e.g. extension not installed).
3. `stored = dl._load_stored_source(target_root, extension)`; if `stored is None`, raise `SpawnError` matching `update_extension` wording: `no source.yaml for extension {extension!r}`.
4. `path, branch = stored.source.path, stored.source.branch` (branch may be `None`).
5. `remove_extension(target_root, extension)` then `install_extension(target_root, path, branch)`.
6. Add `reinstall_extension` to `__all__`.

## Affected files
- `src/spawn_cli/core/high_level.py`

## Code example (illustrative)

```python
def reinstall_extension(target_root: Path, extension: str) -> None:
    _require_init(target_root)
    if extension not in ll.list_extensions(target_root):
        raise SpawnError(f"extension {extension!r} is not installed")
    stored = dl._load_stored_source(target_root, extension)
    if not stored:
        raise SpawnError(f"no source.yaml for extension {extension!r}")
    remove_extension(target_root, extension)
    install_extension(target_root, stored.source.path, stored.source.branch)
```
