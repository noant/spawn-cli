# 2: Implementation Detail Designs

IMPORTANT: always use `spec/main.md` and `spec/navigation.yaml` for rules.

## Status
- [V] Spec created
- [V] Self spec review passed
- [V] Spec review passed
- [V] Code implemented
- [V] Self code review passed
- [V] Code review passed
- [V] HLA updated

## Goal
Implement the full Spawn CLI in Python — data layer, utility modules, agentic flow helpers, extension lifecycle, and IDE adapters for cursor, codex, claude-code, github-copilot, gemini-cli, and windsurf — including unit tests and CLI wiring.

## Design overview

- **Affected modules:**
  - `src/spawn_cli/` — all new subpackages below
  - `src/spawn_cli/cli.py` — extended with all public subcommands
  - `src/spawn_cli/models/` — Pydantic data models (config, metadata, extension, MCP, navigation, skills)
  - `src/spawn_cli/io/` — file I/O helpers: YAML, JSON, TOML, text, path utilities, lock
  - `src/spawn_cli/core/` — low-level (`low_level.py`) and high-level orchestration (`high_level.py`, `download.py`, `scripts.py`): refresh_*, remove_*, add_ide, install/update/remove extension, etc.
  - `src/spawn_cli/ide/` — IDE adapter registry + 6 adapter implementations
  - `tests/` — pytest unit tests for every module

- **Data flow changes:**
  - CLI receives subcommand → (`cwd` = target repo root) → utility/core layers → IDE adapters → `io/`
  - All file paths relative to repository root (`Path.cwd()` for CLI)
  - **`spawn init` required** before any other command; message must include **`need init before`**
  - **Non-blocking `filelock`** on `spawn/.metadata/.spawn.lock` for **every** subcommand after init; busy lock → **`Операция в процессе (файл lock detected)`**
  - Supported platforms: **Windows, Linux, macOS**; Git required only for git-sourced operations (else `SpawnError` with per-OS install hints)
  - Console output: single **verbose** policy (no log-level flag)

- **Integration points:**
  - `argparse` CLI → core high-level / low-level / download (`spawn_cli.core.*` as in step module map)
  - IDE adapter registry (`ide.get(name)`)
  - Core modules → `io/` helpers
  - IDE adapters → normalized skill/MCP metadata from core
  - **`filelock`** (timeout 0 acquire) for repository-level serialization

## Before → After

### Before
- `src/spawn_cli/` has only `cli.py` (stub) and `__init__.py`
- No subpackages, no data models, no utility logic, no IDE adapters

### After
- Full package structure with models, io, core, ide subpackages
- All public commands wired in CLI (`spawn init`, `spawn ide *`, `spawn extension *`, `spawn build *`)
- 6 IDE adapters implemented (cursor, codex, claude-code, github-copilot, gemini-cli, windsurf) + adapter registry for remaining IDEs (warn-only stubs)
- Comprehensive pytest unit tests

## Details

### Python package conventions
- `src/` layout, `pyproject.toml` (setuptools), `pytest`
- Type hints everywhere; use `pathlib.Path` for all paths
- Pydantic v2 models for all config/metadata shapes
- `ruamel.yaml` (round-trip) for YAML I/O, `tomli`/`tomllib` for TOML, `json` stdlib for JSON
- `filelock.FileLock` for Spawn lock at `spawn/.metadata/.spawn.lock`
- All enum values validated at model parse time
- `subprocess` for setup script execution (python interpreter)
- `httpx` for zip/git download (git via `subprocess git clone`)

### Clarifications recorded
- **IDE adapters:** cursor, codex, claude-code, github-copilot, gemini-cli, windsurf fully implemented; remaining 5 IDEs have registered stubs that warn on all operations except `detect()`
- **Tests:** full pytest unit test coverage per module
- **Lock:** `filelock` with **non-blocking** acquire; **no** waiting queue; messages per `utility.md`
- **Download:** full git (requires `git` on PATH when used), zip (httpx + **anti path-traversal**), and local path copy
- **Versioning:** in-tree version string helper only — **no** `packaging` dependency

### Module → file map (abbreviated)

```
src/spawn_cli/
  models/
    config.py         # CoreConfig, IdeList, ExtensionConfig, SourceYaml, ExtensionsMeta
    metadata.py       # RenderedSkillsMeta, RenderedMcpMeta
    navigation.py     # NavigationFile, NavFile, NavExtGroup, NavRulesGroup
    mcp.py            # NormalizedMcp, McpServer, McpTransport, McpEnvVar
    skill.py          # SkillMetadata, SkillRawInfo
  io/
    yaml_io.py        # load_yaml, save_yaml (ruamel round-trip)
    json_io.py        # load_json, save_json
    toml_io.py        # load_toml, save_toml
    text_io.py        # read_lines, write_lines
    paths.py          # ensure_dir, safe_path, spawn_root (no escape)
    lock.py           # spawn_lock context manager (filelock, timeout=0)
  core/
    low_level.py      # all low-level module functions
    high_level.py     # all high-level module functions (refresh_*, remove_*)
    download.py       # download_extension, install_extension, list_build_extensions
    scripts.py        # extension setup script runner
  ide/
    registry.py       # IdeAdapter ABC, get(name), supported_ide_keys(), detect_supported_ides()
    cursor.py
    codex.py
    claude_code.py
    github_copilot.py
    gemini_cli.py
    windsurf.py
    _stub.py          # warn-only stub for remaining 5 IDEs
  cli.py              # extended argparse CLI
```

### Key design decisions
- **Managed block pattern** for entry-point files: `<!-- spawn:start -->` … `<!-- spawn:end -->` (update only Spawn-managed section)
- **Ownership record pattern**: adapters return rendered paths/names; utility layer writes `rendered-skills.yaml`, `rendered-mcp.yaml`, `agent-ignore.txt`
- **Idempotency**: all high-level refresh functions converge to the same state when re-run
- **Error vs warning**: follow spec rules — errors stop before mutation; warnings allow continue
- **Setup scripts**: executed via `subprocess` with `python {script}` and env vars: `SPAWN_EXT_NAME`, `SPAWN_EXT_PATH`, `SPAWN_EXT_VERSION`, `SPAWN_TARGET_VERSION`, `SPAWN_TARGET_ROOT`

## Execution Scheme

> Each step id is the subtask filename (e.g. `1-models`).
> MANDATORY! Each step is executed by a dedicated subagent (Task tool). Do NOT implement inline. No exceptions — even if a step seems trivial or small.

- Phase 1 (sequential):
  - step `1-models` — Pydantic data models + io helpers
  - step `2-core-low-level` — low-level utility modules (all `get_*`, `list_*`, `save_*` functions)
- Phase 2 (parallel):
  - step `3-core-high-level` || step `4a-ide-base`
    - `3-core-high-level` — high-level orchestration modules (refresh_*, remove_*, add/remove_ide, download/install, extension lifecycle)
    - `4a-ide-base` — IDE adapter ABC, registry, shared helpers, StubAdapter for 5 warn-only IDEs
- Phase 3 (parallel):
  - step `4b-ide-cursor` || step `4c-ide-codex` || step `4d-ide-claude-code` || step `4e-ide-github-copilot` || step `4f-ide-gemini-cli` || step `4g-ide-windsurf`
- Phase 4 (sequential):
  - step `5-cli-wiring` — wire all commands into `cli.py`, integrate lock, connect utility to adapters
  - step `6-tests` — comprehensive pytest unit tests for all modules
  - step `7-review` — inspect all changes, fix inconsistencies, naming, broken contracts
