from __future__ import annotations

import argparse

from spawn_cli import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spawn",
        description="A minimal installable Python CLI package.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"spawn {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return 0
