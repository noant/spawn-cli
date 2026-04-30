# Step 2: CLI and tests

## Goal
Expose `spawn extension reinstall <extension_name>` and cover it with tests.

## Approach
1. In `build_parser`, under `extension` subparsers: add `reinstall` with positional `extension_name` (mirror `update` / `remove` help text style).
2. In `_dispatch_extension`, call `hl.reinstall_extension(target_root, args.extension_name)` when `sub == "reinstall"`.
3. **Tests — `tests/test_cli.py`:** Add `test_spawn_extension_reinstall` — patch `hl.reinstall_extension`, assert `main(["extension", "reinstall", "my-ext"]) == 0` and single call `(root, "my-ext")`.
4. **Tests — `tests/core/test_high_level.py`:** Add tests for `reinstall_extension`:
   - Success path: install fixture extension with `source.yaml` (minimal valid `SourceYaml` shape via `save_yaml` / model dump if available); mock `remove_extension` and `install_extension`; assert call order and arguments for install (`path`, `branch`).
   - Missing `source.yaml`: expect `SpawnError` with `no source.yaml`.
   - Extension not in `list_extensions`: expect `SpawnError` (not installed).

Use existing fixtures (`target`, `_install_ext`) where possible; extend `_install_ext` or inline a small helper to write `source.yaml` if cleaner.

## Affected files
- `src/spawn_cli/cli.py`
- `tests/test_cli.py`
- `tests/core/test_high_level.py`

## Code example (CLI fragment)

```python
_ext_reinstall = ext_sub.add_parser("reinstall")
_ext_reinstall.add_argument("extension_name")
```

```python
if sub == "reinstall":
    hl.reinstall_extension(target_root, args.extension_name)
    return 0
```
