# High-Level Architecture (HLA)

This note is the **map of the codebase**: packaging, layers under `spawn_cli/`, where state lives under `spawn/`, and how the main flows connect. **Behavioral detail** belongs in the linked design docs below, not duplicated here.

## Related design documents

| Document | Scope |
| -------- | ----- |
| [`utility.md`](utility.md) | CLI commands and repository transformations. |
| [`utility-method-flows.md`](utility-method-flows.md) | Per-module data flow and persistence in the utility layer. |
| [`data-structure.md`](data-structure.md) | Target repo and workspace data shapes. |
| [`agentic-flow.md`](agentic-flow.md) | Navigation and rendered skills from an agent’s perspective. |
| [`extensions.md`](extensions.md) | Extension packaging and AIDD methodology. |
| [`extension-author-guide.md`](extension-author-guide.md) | Author-facing extension layout, config, workflows. |
| [`ide-adapters.md`](ide-adapters.md) | IDE adapter matrix and rendering contracts. |
| [`user-guide.md`](user-guide.md) | End-user install and invocation (pip, uvx, local). |

## Packaging and entry point

- **Layout**: installable Python package with `src/`; metadata in `pyproject.toml` (`setuptools`, `pytest`).
- **Console script**: `spawn` → `spawn_cli.cli:main`.
- **Publish**: `scripts/publish.py` (expects `uv` on PATH): bumps the patch segment of `[project].version`, rebuilds `dist/`, runs `uv publish` with `SPAWN_CLI_PYPI_TOKEN` or `--token` (child sees `UV_PUBLISH_TOKEN`).

## Managed repository layout and concurrency

**State** for a managed repo lives under `spawn/`: core config, `.extend/` (installed extensions), `.metadata/` (per-IDE artifacts, lists, lock file), `navigation.yaml`, `rules/`, etc.

**Concurrency**: mutating or state-dependent CLI work runs under a **non-blocking** repository lock (`spawn_cli.io.lock.spawn_lock`); contention uses the fixed user-facing message defined in design (see [`utility.md`](utility.md)).

## Layered architecture

Numbered bottom-up dependency style: higher layers call lower ones; `spawn_cli.errors` stays lightweight so import order does not pull in all of `core` early.

### 1. `spawn_cli.errors`

Defines `SpawnError` and `SpawnWarning`. `spawn_cli.core.errors` re-exports them. Path and lock helpers import from here so shallow modules avoid initializing all of `core` during imports.

### 2. `spawn_cli.io`

YAML (including Ruamel comment-preserving paths for navigation), JSON, TOML, text, path safety, and locking under `spawn/.metadata/`. Shared dump configuration: block-style nested mappings, insertion order preserved where relevant.

### 3. `spawn_cli.models`

Pydantic v2 models for configs, navigation, MCP, skills, and rendered metadata shapes.

### 4. `spawn_cli.ide`

- **`IdeAdapter`** ABC: optional `rewrite_core_agent_ignore`, `rewrite_extension_agent_ignore`, `clear_spawn_agent_ignore` (defaults), `finalize_repo_after_ide_removed`.
- **Registry**: `get`, `register`, `detect_supported_ides`.
- **Vacancy / cleanup**: e.g. `spawn_cli.ide._vacancy` (empty MCP payloads, guarded removal of vacant IDE dotdirs).
- **Rendering helpers**: `_helpers` (including `render_skill_md`: frontmatter, skill body, optional **Hints**, **Mandatory reads** with `spawn/navigation.yaml` last, **Contextual reads**).
- **`StubAdapter`** for tests or in-progress work.
- **Concrete adapters** (Cursor, Codex, Claude Code, GitHub Copilot, Gemini CLI, Windsurf) registered for every key in **`CANONICAL_IDE_KEYS`** (defined in `low_level` as the single ordering source for the IDE registry).

### 5. `spawn_cli.core.low_level`

Direct filesystem and metadata: extension and IDE lists, skill/MCP/navigation helpers, rendered ownership YAML, `.gitignore` managed blocks, `init()` layout, **`sync_core_config_from_defaults`** (overwrite `spawn/.core/config.yaml` from bundled **`CoreConfig`** after validating parse of any existing file), **`remove_ide_metadata_dir`**, **`prune_metadata_temp`** (stale UUID dirs under `spawn/.metadata/temp/` older than **24 hours** during extension staging).

**Navigation / skills metadata**: when building skill metadata and extension slices of `spawn/navigation.yaml`, the same repo-relative path is not both mandatory and contextual (normalized comparison; **read-required** wins). Persisted `spawn/navigation.yaml` keeps top-level **`read-required`** then **`read-contextual`** (unknown keys after), via **`_ensure_navigation_root_key_order`** and reorder before dump. **`generate_skills_metadata`** loads **`rules`** groups from merged navigation and folds them into each skill’s mandatory and contextual read lists, deduped with extension-driven reads the same way.

### 6. `spawn_cli.core.download`

Staging, source resolution (git, zip with safe extraction, local copy), version and conflict checks, build manifest install. **`_stage_extension`** calls **`low_level.prune_metadata_temp`** on `spawn/.metadata/temp` before each new staging UUID so old trees age out (**24-hour** heuristic).

### 7. `spawn_cli.core.scripts`

Subprocess hooks for extension setup/uninstall with `SPAWN_*` environment variables.
Hook and healthcheck subprocesses **inherit** the parent process **stdin, stdout,
and stderr** (no output capture), so terminal users see live script output and
can use interactive prompts when Spawn runs interactively.
Immediately before each configured hook or healthcheck subprocess, **stderr** prints
`spawn: running {phase} script: {filename}` (`phase` matches `config.yaml` setup keys;
`filename` is the script basename).

### 8. `spawn_cli.core.high_level`

**Orchestration** for refresh/remove flows: skills, MCP, agent ignore, navigation, gitignore metadata; IDE and extension lifecycle (install, update, remove, **reinstall** from `spawn/.extend/{name}/source.yaml`, refresh, healthcheck, init, etc.); coordinates adapters with `low_level` persistence.

**Agent ignore**: **`refresh_core_agent_ignore`** and **`refresh_extension_agent_ignore`** maintain two managed regions (`# spawn:core:*` and `# spawn:ext:*`). **`agent-ignore.txt`** holds the extension merge only for IDEs that use it; project-style IDEs (e.g. Claude Code) diff a full core+extension snapshot into JSON permissions. **`refresh_agent_ignore(ide)`** runs core then extension. **`remove_ide`** calls **`clear_spawn_agent_ignore`**, then **`finalize_repo_after_ide_removed`**. **`refresh_repository`** (CLI `spawn refresh`) runs **`sync_core_config_from_defaults`**, then the same batched MCP/skills/ignore/navigation/gitignore/entry-point pass used after extension changes.

**Capability warnings (`SpawnWarning`)**: **`_warn_capability_gaps`** can warn once per IDE when **`IdeCapabilities`** marks skills **`unsupported`** or MCP **`unsupported`/`external`**, only if the caller’s work is affected — e.g. **`add_ide`** checks any installed extension with skill files or non-empty MCP (**`list_mcp`**); **`_refresh_extension_core`** uses the same aggregated skill predicate but MCP warnings target **the refreshed extension**; **`refresh_extension_for_ide`** aggregates skills the same way while scoping MCP to **that** extension. **`_refresh_extension_core`** and **`remove_extension`** re-render **all** installed extensions’ skills on each IDE when the extension set or global reads change; MCP refresh stays scoped to the operation’s target extension(s).

**MCP merge notice**: after **`refresh_mcp`** merges extension MCP, if the adapter returns non-empty server names and **`emit_mcp_merged_notice`** is true (default), **stdout** prints **`MCP_MERGED_NOTICE`** once (fixed line that project MCP was merged and the IDE may still require Enable in UI). **`add_ide`** and **`refresh_repository`** batch with **`emit_mcp_merged_notice=False`**, then print **at most once** if any merge wrote servers. No-op MCP adapters (e.g. Windsurf **`add_mcp`** → `[]`) emit nothing.

### 9. `spawn_cli.cli`

- **`argparse`** subcommands (including top-level **`refresh`** and `extension reinstall <name>`), human-readable help at each nesting level (`build_parser`).
- Resolves target repo as `Path.cwd().resolve()`, enforces `spawn init` before other commands.
- Wraps almost all handlers in the non-blocking repository lock.
- At startup, **`install_spawn_warning_format`** (`spawn_cli.warnings_display`) replaces `warnings.showwarning` so **`SpawnWarning`** prints as `spawn: warning: ...` on stderr (no Python `file:line:` banner); other categories delegate to the prior handler.

## Hints flow (summary)

Short hints originate in extension **`config.yaml`** (`hints.global` / `hints.local`, see [`extension-author-guide.md`](extension-author-guide.md)) and in maintainer **`read-required` → `rules`** rows (optional **`hint`**). On navigation refresh, each extension’s **`hints.global`** is mirrored under that extension’s **`- ext:`** stanza in **`spawn/navigation.yaml`** as a **`hints`** string list (normalize, dedupe).

**Rendered skills**: **`SkillMetadata.hints`** merges every installed extension’s **`hints.global`** (sorted extension id), then **`hints.local`** for the owning extension, then maintainer rule hints (deterministic dedupe; see **`generate_skills_metadata`**).

**IDE entry points**: **`rollup_hints_for_agents`** lists global extension hints across installed packs plus maintainer rule hints; **`hints.local`** appears in skills only, not in AGENTS.

Treat **`- ext:`** blocks in `spawn/navigation.yaml` as **machine-owned** (rewritten on refresh). **`rules`** groups are for durable hand-edits (paths, descriptions, **`hint`** on **read-required** rows).

Full detail: [`agentic-flow.md`](agentic-flow.md), [`extension-author-guide.md`](extension-author-guide.md).

## Tests

Automated tests live under `tests/`, mirror the package layout (`tests/core`, `tests/io`, `tests/models`, `tests/ide`), and use `tmp_path` and mocks so unit tests do not require network access.
