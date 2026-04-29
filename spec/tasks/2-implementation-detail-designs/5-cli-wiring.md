# Step 5: CLI Wiring

## Required reading
Before implementing, read:
- `spec/design/utility.md` — Public Commands section: every command name, argument, and expected behavior

## Goal
Extend `src/spawn_cli/cli.py` with all public subcommands, integrate the Spawn lock, and connect CLI argument parsing to the utility layer (high-level modules).

## Approach
Replace the stub `cli.py` with a full `argparse` subcommand tree. Each subcommand handler acquires the lock (when mutating) and calls the appropriate high-level or low-level function. Read-only commands do not acquire the lock.

## Affected files

```
src/spawn_cli/cli.py
tests/test_cli.py  (integration-level CLI smoke tests)
```

## Subcommand tree

```
spawn
  init
  ide
    add    <ide1> [ide2 ...]
    remove <ide1> [ide2 ...]
    list
    list-supported-ides
  extension
    add    <path> [--branch <branch>]
    update <extension-name>
    remove <extension-name>
    list
    init   [path] --name <name>
    check  [path] [--strict]
    from-rules <source> --name <name> [--branch <branch>] [--output <path>]
    healthcheck <extension-name>
  build
    install <path> [--branch <branch>]
    list    <path> [--branch <branch>]
```

## `cli.py` structure

```python
import argparse
import sys
from pathlib import Path
from spawn_cli.io.lock import spawn_lock
from spawn_cli.core import high_level as hl
from spawn_cli.core import low_level as ll
from spawn_cli.core import download as dl
from spawn_cli.ide.registry import detect_supported_ides
from spawn_cli.core.errors import SpawnError

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spawn", description="Spawn CLI")
    parser.add_argument("--target", default=".", help="Target repository root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)

    # spawn init
    sub.add_parser("init", help="Initialize spawn/ in the target repository")

    # spawn ide
    ide_p = sub.add_parser("ide")
    ide_sub = ide_p.add_subparsers(dest="ide_command", required=True)
    _ide_add = ide_sub.add_parser("add")
    _ide_add.add_argument("ides", nargs="+")
    _ide_remove = ide_sub.add_parser("remove")
    _ide_remove.add_argument("ides", nargs="+")
    ide_sub.add_parser("list")
    ide_sub.add_parser("list-supported-ides")

    # spawn extension
    ext_p = sub.add_parser("extension")
    ext_sub = ext_p.add_subparsers(dest="ext_command", required=True)
    _ext_add = ext_sub.add_parser("add")
    _ext_add.add_argument("path")
    _ext_add.add_argument("--branch")
    _ext_update = ext_sub.add_parser("update")
    _ext_update.add_argument("extension_name")
    _ext_remove = ext_sub.add_parser("remove")
    _ext_remove.add_argument("extension_name")
    ext_sub.add_parser("list")
    _ext_init = ext_sub.add_parser("init")
    _ext_init.add_argument("path", nargs="?", default=".")
    _ext_init.add_argument("--name", required=True)
    _ext_check = ext_sub.add_parser("check")
    _ext_check.add_argument("path", nargs="?", default=".")
    _ext_check.add_argument("--strict", action="store_true")
    _ext_from_rules = ext_sub.add_parser("from-rules")
    _ext_from_rules.add_argument("source")
    _ext_from_rules.add_argument("--name", required=True)
    _ext_from_rules.add_argument("--branch")
    _ext_from_rules.add_argument("--output", default=".")
    _ext_health = ext_sub.add_parser("healthcheck")
    _ext_health.add_argument("extension_name")

    # spawn build
    build_p = sub.add_parser("build")
    build_sub = build_p.add_subparsers(dest="build_command", required=True)
    _build_install = build_sub.add_parser("install")
    _build_install.add_argument("path")
    _build_install.add_argument("--branch")
    _build_list = build_sub.add_parser("list")
    _build_list.add_argument("path")
    _build_list.add_argument("--branch")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    target_root = Path(args.target).resolve()

    try:
        return _dispatch(args, target_root)
    except SpawnError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


def _dispatch(args, target_root: Path) -> int:
    cmd = args.command

    if cmd == "init":
        with spawn_lock(target_root):
            ll.init(target_root)
        return 0

    if cmd == "ide":
        return _dispatch_ide(args, target_root)

    if cmd == "extension":
        return _dispatch_extension(args, target_root)

    if cmd == "build":
        return _dispatch_build(args, target_root)

    return 1


def _dispatch_ide(args, target_root: Path) -> int:
    sub = args.ide_command

    if sub == "list-supported-ides":
        # read-only, no lock
        results = detect_supported_ides(target_root)
        _print_yaml(results)
        return 0

    if sub == "list":
        ides = ll.list_ides(target_root)
        for ide in ides:
            print(ide)
        return 0

    if sub == "add":
        with spawn_lock(target_root):
            for ide in args.ides:
                hl.add_ide(target_root, ide)
        return 0

    if sub == "remove":
        with spawn_lock(target_root):
            for ide in args.ides:
                hl.remove_ide(target_root, ide)
        return 0

    return 1


def _dispatch_extension(args, target_root: Path) -> int:
    sub = args.ext_command

    if sub == "list":
        for ext in ll.list_extensions(target_root):
            print(ext)
        return 0

    if sub == "add":
        with spawn_lock(target_root):
            dl.install_extension(target_root, args.path, getattr(args, "branch", None))
        return 0

    if sub == "update":
        with spawn_lock(target_root):
            hl.update_extension(target_root, args.extension_name)
        return 0

    if sub == "remove":
        with spawn_lock(target_root):
            hl.remove_extension(target_root, args.extension_name)
        return 0

    if sub == "init":
        hl.extension_init(Path(args.path), args.name)
        return 0

    if sub == "check":
        warnings = hl.extension_check(Path(args.path), strict=args.strict)
        for w in warnings:
            print(f"Warning: {w}")
        return 0

    if sub == "from-rules":
        with spawn_lock(target_root):
            hl.extension_from_rules(args.source, Path(args.output), args.name, getattr(args, "branch", None))
        return 0

    if sub == "healthcheck":
        ok = hl.extension_healthcheck(target_root, args.extension_name)
        return 0 if ok else 1

    return 1


def _dispatch_build(args, target_root: Path) -> int:
    sub = args.build_command

    if sub == "list":
        exts = dl.list_build_extensions(args.path, getattr(args, "branch", None))
        _print_yaml(exts)
        return 0

    if sub == "install":
        with spawn_lock(target_root):
            dl.install_build(target_root, args.path, getattr(args, "branch", None))
        return 0

    return 1


def _print_yaml(data) -> None:
    """Serialize data to YAML. DetectResult/IdeCapabilities dataclasses are
    converted to camelCase dicts matching the utility.md output shape."""
    from ruamel.yaml import YAML
    from spawn_cli.ide.registry import DetectResult
    import sys

    def _to_serializable(obj):
        if isinstance(obj, DetectResult):
            return {
                "used-in-repo": obj.used_in_repo,
                "capabilities": obj.capabilities.to_dict(),
            }
        if isinstance(obj, dict):
            return {k: _to_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_to_serializable(i) for i in obj]
        return obj

    yaml = YAML()
    yaml.dump(_to_serializable(data), sys.stdout)
```

## Notes

- `--target` global flag allows pointing at a different directory than `cwd`. Defaults to `.` (resolved to absolute).
- All mutating commands acquire `spawn_lock(target_root)` before calling utility functions.
- `list-supported-ides` is read-only; no lock.
- `SpawnError` → exit code 1, print to stderr.
- `spawn build list` is read-only; no lock.
- `spawn extension list`, `spawn ide list`, `spawn extension check`, `spawn extension init` do not require the lock (no target mutations, or self-contained path).

## Tests

`tests/test_cli.py`:
- `test_spawn_help` — `spawn --help` exits 0
- `test_spawn_init` — calls `ll.init` with correct target_root (mock)
- `test_spawn_ide_list_supported_ides` — calls `detect_supported_ides`, prints YAML
- `test_spawn_ide_add` — calls `hl.add_ide` for each ide, lock acquired
- `test_spawn_ide_remove` — calls `hl.remove_ide`
- `test_spawn_ide_list` — calls `ll.list_ides`, prints each
- `test_spawn_extension_add` — calls `dl.install_extension`
- `test_spawn_extension_update` — calls `hl.update_extension`
- `test_spawn_extension_remove` — calls `hl.remove_extension`
- `test_spawn_extension_list` — calls `ll.list_extensions`
- `test_spawn_extension_init` — calls `hl.extension_init`
- `test_spawn_extension_check` — calls `hl.extension_check`, prints warnings
- `test_spawn_extension_healthcheck_ok` — exit 0
- `test_spawn_extension_healthcheck_fail` — exit 1
- `test_spawn_build_install` — calls `dl.install_build`
- `test_spawn_build_list` — calls `dl.list_build_extensions`, prints YAML
- `test_spawn_error_exit_code` — SpawnError → exit 1
