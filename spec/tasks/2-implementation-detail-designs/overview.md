# 2: Implementation Detail Designs

IMPORTANT: always use `spec/main.md` and `spec/navigation.yaml` for rules.

## Status
- [V] Spec created
- [V] Self spec review passed
- [V] Spec review passed
- [ ] Code implemented
- [ ] Self code review passed
- [ ] Code review passed
- [ ] HLA updated

## Goal
Implement the full Spawn CLI in Python — data layer, utility modules, agentic flow helpers, extension lifecycle, and IDE adapters for cursor, codex, claude-code, github-copilot, gemini-cli, and windsurf — including unit tests and CLI wiring.

## Design overview

- **Affected modules:**
  - `src/spawn_cli/` — all new subpackages below
  - `src/spawn_cli/cli.py` — extended with all public subcommands
  - `src/spawn_cli/models/` — Pydantic data models (config, metadata, extension, MCP, navigation, skills)
  - `src/spawn_cli/io/` — file I/O helpers: YAML, JSON, TOML, text, path utilities, lock
  - `src/spawn_cli/core/` — low-level utility modules (list_extensions, list_ides, get_*_read, list_skills, list_mcp, ignore helpers, navigation, rendered-skills/mcp metadata)
  - `src/spawn_cli/utility/` — high-level orchestration modules (refresh_*, remove_*, add_ide, remove_ide, install_extension, update_extension, etc.)
  - `src/spawn_cli/ide/` — IDE adapter registry + 6 adapter implementations
  - `tests/` — pytest unit tests for every module

- **Data flow changes:**
  - CLI receives subcommand → calls utility layer → uses core modules + IDE adapters → reads/writes target repository files through io layer
  - All file paths relative to `targetRoot`
  - Spawn lock acquired before any mutating operation

- **Integration points:**
  - `argparse` CLI → utility layer public functions
  - Utility layer → IDE adapter registry (`ide.get(name)`)
  - Core modules → `io/` helpers
  - IDE adapters → normalized skill/MCP metadata from core
  - `filelock` library for repository-level lock

## Before → After

### Before
- `src/spawn_cli/` has only `cli.py` (stub) and `__init__.py`
- No subpackages, no data models, no utility logic, no IDE adapters

### After
- Full package structure with models, io, core, utility, ide subpackages
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
- **Lock:** `filelock` library; lock file at `spawn/.metadata/.spawn.lock`
- **Download:** full git (subprocess `git clone --depth 1`), zip (httpx download + zipfile), and local path copy

### Module → file map (abbreviated)

```
src/spawn_cli/
  models/
    config.py         # CoreConfig, IdeList, ExtensionConfig, SourceYaml, ExtensionsMeta
    metadata.py       # RenderedSkillsMeta, RenderedMcpMeta
    navigation.py     # NavigationFile, ReadRequiredGroup, ReadContextualGroup
    mcp.py            # NormalizedMcp, McpServer, McpTransport, McpEnvVar
    skill.py          # SkillMetadata, SkillRawInfo
  io/
    yaml_io.py        # load_yaml, save_yaml (ruamel round-trip)
    json_io.py        # load_json, save_json
    toml_io.py        # load_toml, save_toml
    text_io.py        # read_lines, write_lines
    paths.py          # ensure_dir, rel_path, safe_path (no escape)
    lock.py           # SpawnLock context manager (filelock)
  core/
    low_level.py      # all low-level module functions
    high_level.py     # all high-level module functions (refresh_*, remove_*)
    download.py       # download_extension, install_extension, list_build_extensions
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
