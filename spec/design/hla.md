# High-Level Architecture (HLA)

This document describes how the Spawn CLI package is structured and how major pieces interact. Detailed behavior lives in `spec/design/utility.md`, `spec/design/data-structure.md`, and `spec/design/ide-adapters.md`.

## Packaging and entry point

The project is an installable Python package with a `src/` layout. Build and dependency metadata live in `pyproject.toml` (`setuptools`, `pytest`). The console script `spawn` maps to `spawn_cli.cli:main`. Maintainers can publish to PyPI with `scripts/publish.py` (requires `uv` on PATH): it bumps the patch segment of `[project].version`, rebuilds artifacts under `dist/`, and runs `uv publish` using `SPAWN_CLI_PYPI_TOKEN` or `--token` (passed to the child process as `UV_PUBLISH_TOKEN`).

## Layering

1. **`spawn_cli.cli`** — Parses `argparse` subcommands (including `extension reinstall <name>`) with human-readable **`help`/description strings** per argument and nesting level (`build_parser`), resolves the target repository as `Path.cwd().resolve()`, enforces `spawn init` before other commands, and wraps (almost) all handlers in a non-blocking repository lock (`spawn_cli.io.lock.spawn_lock`). At process start, **`install_spawn_warning_format`** (`spawn_cli.warnings_display`) replaces `warnings.showwarning` so **`SpawnWarning`** lines print as `spawn: warning: ...` on stderr (no Python `file:line:` banner); other categories delegate to the prior handler.
2. **`spawn_cli.core.high_level`** — Orchestration: refresh/remove skills, MCP, agent ignore, navigation, gitignore metadata; IDE and extension lifecycle (install, update, remove, **reinstall** from recorded `source.yaml` under `spawn/.extend/{name}/`, refresh, healthcheck, init, etc.); coordinates IDE adapters with low-level persistence. **`remove_ide`** finishes by calling each adapter's `finalize_repo_after_ide_removed` (vacancy cleanup of Spawn-owned repo-root dirs), then drops the IDE from the list and removes `spawn/.metadata/<ide>/`.
3. **`spawn_cli.core.download`** — Staging, source resolution (git, zip with safe extraction, local copy), version and conflict checks, build manifest install; **`_stage_extension`** invokes **`low_level.prune_metadata_temp`** on **`spawn/.metadata/temp`** before each new staging UUID directory so old staging trees age out (**24-hour** heuristic).
4. **`spawn_cli.core.scripts`** — Subprocess hooks for extension setup/uninstall with `SPAWN_*` environment variables.
5. **`spawn_cli.core.low_level`** — Direct filesystem and metadata operations: extension and IDE lists, skill/MCP/navigation helpers, rendered ownership YAML, `.gitignore` managed blocks, `init()` layout, **`remove_ide_metadata_dir`**, **`prune_metadata_temp`** (drops stale UUID directories under **`spawn/.metadata/temp/`** older than **24 hours** during extension staging). Defines **`CANONICAL_IDE_KEYS`** (single ordering source for the IDE registry). When building skill metadata and extension slices of `spawn/navigation.yaml`, the same repository-relative file is not listed as both mandatory and contextual: paths are compared normalized (`Path.as_posix`, slash rules), and **read-required** wins. Persisted `spawn/navigation.yaml` always emits top-level **`read-required` before `read-contextual`** (unknown keys after the pair): **`_ensure_navigation_root_key_order`** plus Ruamel reorder or dict rebuild before dump.
6. **`spawn_cli.ide`** — `IdeAdapter` ABC (with default **`finalize_repo_after_ide_removed`**), registry (`get`, `register`, `detect_supported_ides`), vacancy helpers (**`spawn_cli.ide._vacancy`**: empty MCP payloads, guarded removal of vacant IDE dotdirs such as `.cursor`), shared rendering helpers (`render_skill_md`: skill body after frontmatter, then mandatory reads with **`spawn/navigation.yaml` always last**, then contextual reads), optional **`StubAdapter`** for tests or in-progress work, and concrete adapters (Cursor, Codex, Claude Code, GitHub Copilot, Gemini CLI, Windsurf) registered for every **`CANONICAL_IDE_KEYS`** entry.
7. **`spawn_cli.models`** — Pydantic v2 models for configs, navigation, MCP, skills, and rendered metadata shapes.
8. **`spawn_cli.io`** — YAML I/O via **`save_yaml`** and shared **`configure_yaml_dump`** (block-style nested collections; **`sort_base_mapping_type_on_output = False`** so dump order matches insertion order; comment-preserving navigation uses **`YAML(typ="rt")`** where `low_level.save_extension_navigation` loads/writes), JSON, TOML, text, path safety, and file locking under `spawn/.metadata/`.
9. **`spawn_cli.errors`** — Defines `SpawnError` and `SpawnWarning`; `spawn_cli.core.errors` re-exports them. Path and lock helpers import from here so lightweight I/O modules avoid initializing `spawn_cli.core` during import ordering.

## Data and concurrency

State for a managed repository lives under `spawn/`: core config, `.extend/` (installed extensions), `.metadata/` (per-IDE rendered metadata, lists, lock file), `navigation.yaml`, and `rules/`. CLI operations that mutate or depend on that tree run under a **non-blocking** file lock; contention surfaces a fixed user-facing message per design.

## Tests

Automated tests live under `tests/`, mirror the package layout (`tests/core`, `tests/io`, `tests/models`, `tests/ide`), and use `tmp_path` and mocks so unit tests do not require network access.
