# 34: Kilo Code IDE adapter

## Source seed
- Path: none

## Status
- [V] Research [glm-5.3-flash]
- [ ] User research review
- [V] Spec drafting [glm-5.3]
- [V] Spec self-review [deepseek-v4-pro + glm-5.3]
- [ ] Spec review
- [V] Code implementation [glm-5.3]
- [V] Code self-review [deepseek-v4-pro + glm-5.3]
- [ ] Code review / debugging
- [V] Design document update [glm-5.3]

## Goal
Add a `kilo-code` IDE adapter to spawn-cli so `spawn add-ide kilo-code` renders skills, MCP, agent-ignore, and the entry point for Kilo Code (kilo.ai, VS Code extension).

## Motivation
New feature: the user requested support for the Kilo Code IDE ("давай добавим kilo code"). Kilo Code is a Cline/Roo-lineage VS Code extension reading project `AGENTS.md`; spawn should support it like its sibling adapters.

## Invasiveness level
minimally-invasive

## Review models
- Research review: single agent: glm-5.3-flash
- Spec review: cross-review: deepseek-v4-pro, glm-5.3
- Code review: cross-review: deepseek-v4-pro, glm-5.3

## Run mode
auto

## Research summary
Research (A2-researcher, glm-5.3-flash; sources: https://kilo.ai/docs/customize/agents-md, /customize/skills, /customize/context/kilocodeignore, /automate/mcp/using-in-kilo-code):

- Entry file: project-root `AGENTS.md` is read (priority: agent prompt > project `instructions` in kilo.jsonc > AGENTS.md > global instructions). Write-protected upstream.
- Skills: `.kilo/skills/<name>/SKILL.md`; frontmatter `name`+`description` required; `name` must equal directory name; name regex `^[a-z0-9]+(-[a-z0-9]+)*$`, max 64 chars. Project `.kilo/skills/` overrides global.
- MCP: no dedicated mcp.json; servers live under the top-level `mcp` key of the main config: project `kilo.json`/`.kilo/kilo.json(c)`. Entry shape (same family as OpenCode/Mimo): local `{type: "local", command: [argv...], environment, enabled}`, remote `{type: "remote", url, headers, enabled}`; env placeholders `{env:VAR}`.
- Agent ignore: root `.kilocodeignore`, gitignore-style syntax (the file keeps the legacy kilocode prefix after the `.kilo` rename).
- Detect markers: `.kilo/` (primary, current) and `.kilocode/` (legacy, auto-included upstream). Root `kilo.json`/`kilo.jsonc` also indicate usage.
- Kilo also loads `.agents/skills/` and `.claude/skills/` by default (compat) - outside this adapter; the adapter owns only `.kilo/skills/`.

Adapter shape decision: MCP part mirrors `mimo_code.py` (canonical `.kilo/kilo.json`, key `mcp`); agent-ignore part mirrors `cline.py` (text ignore file `.kilocodeignore` with split spawn regions); skill-name sanitization mirrors `opencode.py` `_sanitize_skill_name` (Kilo enforces the same regex). Canonical config per rule 05: one file `.kilo/kilo.json`; SpawnWarning when sibling `.kilo/kilo.jsonc` exists; SpawnError on unparseable JSON before mutation.

## Design overview
- Affected modules: `spawn_cli.ide` (new adapter module + wiring), `spawn_cli.core.low_level` (keys), `spawn_cli.ide._vacancy` (cleanup), tests, design docs.
- Files & symbols:
  - `src/spawn_cli/core/low_level.py` - `CANONICAL_IDE_KEYS` (append `kilo-code`)
  - `src/spawn_cli/ide/kilo_code.py` - new `KiloCodeAdapter(IdeAdapter)`, `_load_config`, `_save_config`, `_build_mcp_entry`, `_sanitize_skill_name`, module-level `register(KiloCodeAdapter())`, `__all__`
  - `src/spawn_cli/ide/registry.py` - `ALIASES` (`kilo -> kilo-code`)
  - `src/spawn_cli/ide/__init__.py` - import, class re-export, `__all__` entry
  - `src/spawn_cli/ide/_vacancy.py` - new `finalize_kilo_code_repo` + `__all__`
  - `tests/ide/test_kilo_code.py` - new test module
  - `tests/ide/test_registry.py` - key/alias/entry-file assertions
  - `tests/ide/test_mcp_stdio_proxy_parity.py` - parametrize entry
  - `spec/design/ide-adapters.md`, `spec/design/hla.md`, `README.md` - docs
- Data flow changes: none; new adapter plugs into the existing registry/detect/refresh pipeline.
- Integration points: `spawn ide add/remove kilo-code` via `registry.get`; vacancy cleanup via `finalize_repo_after_ide_removed`.

## Before → After
### Before
- `CANONICAL_IDE_KEYS` has 11 keys, no `kilo-code`; no `src/spawn_cli/ide/kilo_code.py`; `spawn ide kilo-code` raises `SpawnError: Unknown IDE`.
### After
- `kilo-code` is a registered adapter; `spawn add-ide kilo-code` (alias `kilo`) renders `.kilo/skills/*/SKILL.md`, `.kilo/kilo.json` (mcp), `.kilocodeignore` spawn block, and the `AGENTS.md` entry block; removal + vacancy cleanup work.

## Details
Capabilities: `skills="native"`, `mcp="project"`, `agent_ignore="native"`, `entry_point="agents-md"`.

- detect markers: `.kilo/`, `.kilocode/`, root `kilo.json`, root `kilo.jsonc`.
- skills: `.kilo/skills/<sanitized-name>/SKILL.md`; frontmatter name == dirname (rule 04); `render_skill_md(skill.model_copy(update={"name": name}), "AGENTS.md")`.
- mcp: canonical `.kilo/kilo.json`, top-level `mcp` dict; entries copied from `mimo_code._build_mcp_entry` (stdio -> `{"type": "local", "command": [...]}`, proxy -> `["spawn"] + mcp_stdio_argv(...)`, remote -> `{"type": "remote", "url": ..., "headers": {k: "{env:v}"}}`, `enabled: true`, `environment` with `{env:VAR}` for secrets). Removal pops server keys and the empty `mcp` key.
- agent ignore: `.kilocodeignore` with `rewrite_ignore_block` / `remove_ignore_block` / split-region rewrites / `clear_split_agent_ignore_file` (mirror `cline.py`).
- entry point: `AGENTS.md` via `rewrite_managed_block`.
- vacancy: `finalize_kilo_code_repo` - `.kilo/kilo.json` deleted when vacant (known keys `{"mcp"}` only, mirror `_mimo_config_vacant`); prune empty dirs under `.kilo/` and `.kilocode/`; drop both dotdirs when they contain zero files; clear the `.kilocodeignore` spawn block and unlink the file when blank.
- warnings: `SpawnWarning` for overwrite and JSONC-variant notices (rule 03); `SpawnError` on unparseable `.kilo/kilo.json` before mutation (rule 05).
- no MCP parity-test skip: MCP is supported, so the adapter joins `test_mcp_stdio_proxy_parity.py` parametrize with `kilo_json` reading `data["mcp"]` (opencode-style single argv-array golden check).

## Execution Scheme
Suggested coordinator model: glm-5.3
> Each step id is the subtask filename (e.g. `1-adapter`).
> Each step is executed by a dedicated `A5-coder` subagent (see Step 5).
- Phase 1 (sequential): step 1-adapter → step 2-tests-docs
- Phase 2 (sequential): step review — inspect all changes, fix inconsistencies (A6-coordinator + A4-reviewer per code review scheme)
