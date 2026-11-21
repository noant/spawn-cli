# 1-remove-ide-metadata-dir

## Goal

After `remove_ide` completes, eliminate the `spawn/.metadata/<ide>/` directory so no rendered-state or agent-ignore list files remain for a removed IDE.

## Approach

1. In `remove_ide`, keep the existing sequence for workspace-facing work: uninstall rendered MCP and skills per extension for that IDE; remove agent-ignore block from IDE files using the stored globs from `get_agent_ignore_list` **before** deleting metadata. Prefer **drop** the `save_agent_ignore_list(target_root, ide, [])` call when the implementation removes `spawn/.metadata/<ide>/` in the same function (avoid a redundant empty file write followed by immediate `rmtree`). Update any tests that expected the empty file to exist briefly.
2. Add a low-level helper such as `remove_ide_metadata_dir(target_root, ide)` that performs `shutil.rmtree(metadata_ide_root, ignore_errors=True)` where `metadata_ide_root` is `_spawn(target_root) / ".metadata" / ide`.
3. Call `remove_ide_metadata_dir` at the end of `remove_ide`, **after** `remove_ide_from_list`. Complete ordering: finalize adapter roots (`finalize_repo_after_ide_removed`), then remove IDE from list, then `remove_ide_metadata_dir` (drops `spawn/.metadata/<ide>/` including rendered YAML).

All reads from `spawn/.metadata/<ide>/` required for teardown must finish **before** `finalize_repo_after_ide_removed`.

Re-read existing `remove_ide` ordering in `spawn_cli/core/high_level.py`: prefer **drop** `save_agent_ignore_list(target_root, ide, [])` when the whole `spawn/.metadata/<ide>/` tree is removed in the same function; update tests if they assumed the empty file lingered.

## Affected files

- `src/spawn_cli/core/high_level.py` — `remove_ide`.
- `src/spawn_cli/core/low_level.py` — path helper / `remove_ide_metadata_dir` export if added.
- `tests/core/` — test that metadata dir is absent after removal.

## Code sketch

```python
# low_level.py
def remove_ide_metadata_dir(target_root: Path, ide: str) -> None:
    md = _spawn(target_root) / ".metadata" / ide
    if md.is_dir():
        shutil.rmtree(md, ignore_errors=True)
```

Ordering in `remove_ide`: perform directory removal **after** all reads from `spawn/.metadata/<ide>/` needed for teardown (typically after `save_agent_ignore_list`).
