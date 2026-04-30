from __future__ import annotations

import argparse
import sys
from pathlib import Path

from spawn_cli import __version__
from spawn_cli.core import download as dl
from spawn_cli.core import high_level as hl
from spawn_cli.core import low_level as ll
from spawn_cli.core.errors import SpawnError
from spawn_cli.ide.registry import DetectResult, detect_supported_ides
from spawn_cli.io.lock import spawn_lock
from spawn_cli.warnings_display import install_spawn_warning_format


def _require_init(target_root: Path) -> None:
    if not (target_root / "spawn").is_dir():
        raise SpawnError("need init before: run spawn init in this repository.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spawn", description="Spawn CLI")
    parser.add_argument(
        "--version",
        action="version",
        version=f"spawn {__version__}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialize spawn/ in the current repository")

    rules_p = sub.add_parser("rules")
    rules_sub = rules_p.add_subparsers(dest="rules_command", required=True)
    rules_sub.add_parser("refresh", help="Sync spawn/rules/ into navigation.yaml")

    ide_p = sub.add_parser("ide")
    ide_sub = ide_p.add_subparsers(dest="ide_command", required=True)
    _ide_add = ide_sub.add_parser("add")
    _ide_add.add_argument("ides", nargs="+")
    _ide_remove = ide_sub.add_parser("remove")
    _ide_remove.add_argument("ides", nargs="+")
    ide_sub.add_parser("list")
    ide_sub.add_parser("list-supported-ides")

    ext_p = sub.add_parser("extension")
    ext_sub = ext_p.add_subparsers(dest="ext_command", required=True)
    _ext_add = ext_sub.add_parser("add")
    _ext_add.add_argument("path")
    _ext_add.add_argument("--branch", default=None)
    _ext_update = ext_sub.add_parser("update")
    _ext_update.add_argument("extension_name")
    _ext_remove = ext_sub.add_parser("remove")
    _ext_remove.add_argument("extension_name")
    _ext_reinstall = ext_sub.add_parser("reinstall")
    _ext_reinstall.add_argument("extension_name")
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
    _ext_from_rules.add_argument("--branch", default=None)
    _ext_from_rules.add_argument("--output", default=".")
    _ext_health = ext_sub.add_parser("healthcheck")
    _ext_health.add_argument("extension_name")

    build_p = sub.add_parser("build")
    build_sub = build_p.add_subparsers(dest="build_command", required=True)
    _build_install = build_sub.add_parser("install")
    _build_install.add_argument("path")
    _build_install.add_argument("--branch", default=None)
    _build_list = build_sub.add_parser("list")
    _build_list.add_argument("path")
    _build_list.add_argument("--branch", default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    install_spawn_warning_format()
    parser = build_parser()
    args = parser.parse_args(argv)
    target_root = Path.cwd().resolve()

    try:
        return _dispatch(args, target_root)
    except SpawnError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


def _dispatch(args: argparse.Namespace, target_root: Path) -> int:
    cmd = args.command

    if cmd == "init":
        with spawn_lock(target_root):
            ll.init(target_root)
        return 0

    _require_init(target_root)

    with spawn_lock(target_root):
        if cmd == "rules":
            return _dispatch_rules(args, target_root)
        if cmd == "ide":
            return _dispatch_ide(args, target_root)
        if cmd == "extension":
            return _dispatch_extension(args, target_root)
        if cmd == "build":
            return _dispatch_build(args, target_root)

    return 1


def _dispatch_rules(args: argparse.Namespace, target_root: Path) -> int:
    sub = args.rules_command
    if sub == "refresh":
        hl.refresh_rules_navigation(target_root)
        return 0
    return 1


def _dispatch_ide(args: argparse.Namespace, target_root: Path) -> int:
    sub = args.ide_command

    if sub == "list-supported-ides":
        results = detect_supported_ides(target_root)
        _print_yaml(results)
        return 0

    if sub == "list":
        ides = ll.list_ides(target_root)
        for ide in ides:
            print(ide)
        return 0

    if sub == "add":
        for ide in args.ides:
            hl.add_ide(target_root, ide)
        return 0

    if sub == "remove":
        for ide in args.ides:
            hl.remove_ide(target_root, ide)
        return 0

    return 1


def _dispatch_extension(args: argparse.Namespace, target_root: Path) -> int:
    sub = args.ext_command

    if sub == "list":
        for ext in ll.list_extensions(target_root):
            print(ext)
        return 0

    if sub == "add":
        dl.install_extension(target_root, args.path, args.branch)
        return 0

    if sub == "update":
        hl.update_extension(target_root, args.extension_name)
        return 0

    if sub == "remove":
        hl.remove_extension(target_root, args.extension_name)
        return 0

    if sub == "reinstall":
        hl.reinstall_extension(target_root, args.extension_name)
        return 0

    if sub == "init":
        hl.extension_init(Path(args.path).resolve(), args.name)
        return 0

    if sub == "check":
        warn_list = hl.extension_check(Path(args.path).resolve(), strict=args.strict)
        for w in warn_list:
            print(f"Warning: {w}")
        return 0

    if sub == "from-rules":
        hl.extension_from_rules(
            args.source,
            Path(args.output).resolve(),
            args.name,
            args.branch,
        )
        return 0

    if sub == "healthcheck":
        ok = hl.extension_healthcheck(target_root, args.extension_name)
        return 0 if ok else 1

    return 1


def _dispatch_build(args: argparse.Namespace, target_root: Path) -> int:
    sub = args.build_command

    if sub == "list":
        exts = dl.list_build_extensions(args.path, args.branch)
        _print_yaml(exts)
        return 0

    if sub == "install":
        dl.install_build(target_root, args.path, args.branch)
        return 0

    return 1


def _print_yaml(data: object) -> None:
    """Serialize data to YAML. DetectResult dataclass values use utility.md output shape."""
    from ruamel.yaml import YAML

    from spawn_cli.io.yaml_io import configure_yaml_dump

    def _to_serializable(obj: object) -> object:
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
    configure_yaml_dump(yaml)
    yaml.dump(_to_serializable(data), sys.stdout)
