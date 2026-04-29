# High-Level Architecture (HLA)

This document describes the high-level architecture and interaction of abstractions in the project.

## Python CLI package

The project is an installable Python package using a `src/` layout. Project metadata and tool configuration live in `pyproject.toml`, with `setuptools` as the build backend and `pytest` configured for the test suite.

The runtime package is `spawn_cli`. Package version metadata is exposed from `src/spawn_cli/__init__.py`, while `src/spawn_cli/cli.py` owns the command-line interface. The CLI uses the standard library `argparse`; `build_parser()` constructs the parser and `main(argv=None)` parses arguments and returns a process exit code.

The installed console command is `spawn`, wired through the `[project.scripts]` entry in `pyproject.toml` to `spawn_cli.cli:main`. Current tests live under `tests/` and smoke-test the CLI help path.
