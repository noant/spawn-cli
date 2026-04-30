# High-Level Architecture (HLA)

This document describes how the Spawn CLI package is structured and how major pieces interact. Detailed behavior lives in `spec/design/utility.md`, `spec/design/data-structure.md`, and `spec/design/ide-adapters.md`.

## Packaging and entry point

The project is an installable Python package with a `src/` layout. Build and dependency metadata live in `pyproject.toml` (`setuptools`, `pytest`). The console script `spawn` maps to `spawn_cli.cli:main`.

## Layering

1. **`spawn_cli.cli`** — Parses `argparse` subcommands, resolves the target repository as `Path.cwd().resolve()`, enforces `spawn init` before other commands, and wraps (almost) all handlers in a non-blocking repository lock (`spawn_cli.io.lock.spawn_lock`).
2. **`spawn_cli.core.high_level`** — Orchestration: refresh/remove skills, MCP, agent ignore, navigation, gitignore metadata; IDE and extension lifecycle; coordinates IDE adapters with low-level persistence.
3. **`spawn_cli.core.download`** — Staging, source resolution (git, zip with safe extraction, local copy), version and conflict checks, build manifest install.
4. **`spawn_cli.core.scripts`** — Subprocess hooks for extension setup/uninstall with `SPAWN_*` environment variables.
5. **`spawn_cli.core.low_level`** — Direct filesystem and metadata operations: extension and IDE lists, skill/MCP/navigation helpers, rendered ownership YAML, `.gitignore` managed blocks, `init()` layout. Defines **`CANONICAL_IDE_KEYS`** (single ordering source for the IDE registry).
6. **`spawn_cli.ide`** — `IdeAdapter` ABC, registry (`get`, `register`, `detect_supported_ides`), shared rendering helpers, stub adapters for IDEs without full support, and concrete adapters (e.g. Cursor, Codex, Claude Code, GitHub Copilot, Gemini CLI, Windsurf).
7. **`spawn_cli.models`** — Pydantic v2 models for configs, navigation, MCP, skills, and rendered metadata shapes.
8. **`spawn_cli.io`** — YAML (round-trip where needed), JSON, TOML, text, path safety, and file locking under `spawn/.metadata/`.

## Data and concurrency

State for a managed repository lives under `spawn/`: core config, `.extend/` (installed extensions), `.metadata/` (per-IDE rendered metadata, lists, lock file), `navigation.yaml`, and `rules/`. CLI operations that mutate or depend on that tree run under a **non-blocking** file lock; contention surfaces a fixed user-facing message per design.

## Tests

Automated tests live under `tests/`, mirror the package layout (`tests/core`, `tests/io`, `tests/models`, `tests/ide`), and use `tmp_path` and mocks so unit tests do not require network access.
