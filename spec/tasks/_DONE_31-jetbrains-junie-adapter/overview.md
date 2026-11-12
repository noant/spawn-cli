# 31: JetBrains Junie IDE adapter

## Source seed
- Path: spec/seeds/8-jetbrains-junie-adapter.md

## Status
- [V] Research [glm-5.3 + deepseek-v4-pro] (kimi-k3 rate-limited, deepseek-v4-pro substituted for cross line B)
- [V] User research review (auto mode)
- [V] Spec drafting [glm-5.3-flash]
- [V] Spec self-review [glm-5.3 + deepseek-v4-pro] (kimi-k3.1-pro rate-limited, substituted for cross line B)
- [ ] Spec review
- [V] Code implementation [glm-5.3-flash]
- [V] Code self-review [glm-5.3]
- [ ] Code review / debugging
- [V] Design document update [glm-5.3-flash]

## Goal
Replace the absent Junie stub with a full IDE adapter `src/spawn_cli/ide/junie.py` covering skills, MCP, agent ignore, entry point, finalize, registration, and tests.

## Motivation
New feature: support a new IDE (JetBrains Junie) so users can install Spawn skills, MCP servers, agent-ignore rules, and navigation entry point for Junie like for cursor/codex/cline.

## Invasiveness
medium-invasive — edits touch the IDE adapter layer (`src/spawn_cli/ide/`), registration constants (`src/spawn_cli/core/low_level.py`), tests, and design docs; no changes outside these layers.

## Review models
- Research review: single agent: glm-5.3
- Spec review: cross-review: glm-5.3, kimi-k3.1-pro
- Code review: single agent: glm-5.3

## Run mode
auto — fully LLM-run; user confirmations (Steps 4, 7) skipped, checkboxes left unchecked.

## Research summary
Cross-research (glm-5.3 + deepseek-v4-pro, reviewed by glm-5.3).

Repo facts (verified by reviewer):
- Adapter ABC `IdeAdapter` in `src/spawn_cli/ide/registry.py`: `detect`, `add_skills`, `remove_skills`, `add_mcp`, `remove_mcp`, `add_agent_ignore`, `remove_agent_ignore`, optional `rewrite_core_agent_ignore`, `rewrite_extension_agent_ignore`, `clear_spawn_agent_ignore`, `rewrite_entry_point`, `finalize_repo_after_ide_removed`.
- `IdeCapabilities(skills, mcp, agent_ignore, entry_point)` values: `native|project|entry-only|external|unsupported`; `entry_point` additionally uses the established repo value `agents-md` (cursor precedent). `DetectResult(used_in_repo, capabilities)`.
- `register(adapter)` validates `key` against `CANONICAL_IDE_KEYS` in `src/spawn_cli/core/low_level.py` (append-only tuple; length at implementation time per current tree - concurrent tasks 29/30 may append mimo-code/hermes).
- MCP entry builder precedent: `cursor.py::_build_mcp_server_entry` (stdio: command/args, proxy via `mcp_stdio_argv`; http/sse: type/url/headers with `${VAR}`; env secrets as `${KEY}`).
- Ignore helpers: `rewrite_ignore_block`, `remove_ignore_block`, `rewrite_core_agent_ignore_region`, `rewrite_extension_agent_ignore_region`, `clear_split_agent_ignore_file` (`_helpers.py`).
- Vacancy helpers in `_vacancy.py`; per-IDE `finalize_*_repo` functions.
- Tests: per-adapter files in `tests/ide/` + `test_registry.py` (asserts detect order == `CANONICAL_IDE_KEYS`) + `test_mcp_stdio_proxy_parity.py` (needs new key param).

Junie facts (citations):
- Instructions: Junie reads `AGENTS.md` (project root); `.junie/AGENTS.md` also supported; legacy `.junie/guidelines.md` deprecated. https://junie.jetbrains.com/docs/guidelines-and-memory.html, https://github.com/JetBrains/junie-guidelines
- Skills: Agent Skills format, project path `.junie/skills/<name>/SKILL.md` (global `~/.junie/skills/`). https://junie.jetbrains.com/docs/agent-skills.html — resolved in review: glm-5.3 wins; deepseek's `.agents/skills/` concern rejected.
- MCP: project scope `.junie/mcp/mcp.json`, top-level `mcpServers`, standard stdio `command`/`args`/`env` and remote `type`/`url`/`headers`; no `type: "stdio"` required for local servers (verified: Junie uses the standard mcpServers shape as Claude Desktop). https://junie.jetbrains.com/docs/junie-cli-mcp-configuration.html
- Agent ignore: `.aiignore` at project root, gitignore syntax; Junie does not process listed paths. https://www.jetbrains.com/help/ai-assistant/junie-agent.html — resolved in review: deepseek-v4-pro wins; glm-5.3's "no project-scope mechanism" was wrong.
- Detection marker: `.junie/` directory presence (root `AGENTS.md` is shared by many agents — not a marker).

## Design overview
- Affected modules: `src/spawn_cli/ide/` (new `junie.py`, `_vacancy.py`, `__init__.py`), `src/spawn_cli/core/low_level.py`, `tests/ide/`.
- Files & symbols:
  - NEW `src/spawn_cli/ide/junie.py` — `JunieAdapter(IdeAdapter)`, `key = "junie"`, module-level `_build_mcp_server_entry(server: McpServer) -> dict`, `register(JunieAdapter())`.
  - `src/spawn_cli/ide/_vacancy.py` — NEW `finalize_junie_repo(target_root: Path) -> None`.
  - `src/spawn_cli/core/low_level.py` — append `"junie"` to `CANONICAL_IDE_KEYS`.
  - `src/spawn_cli/ide/__init__.py` — import `.junie`, export `JunieAdapter`.
  - NEW `tests/ide/test_junie.py`; EDIT `tests/ide/test_mcp_stdio_proxy_parity.py` (add junie param).
- Data flow changes: none outside adapter layer; `spawn ide add junie` will render skills to `.junie/skills/`, merge MCP into `.junie/mcp/mcp.json`, managed-block `AGENTS.md`, managed block in `.aiignore`.
- Integration points: `registry.register` validation, `detect_supported_ides` ordering, `mcp_stdio_argv` spawn proxy, vacancy finalize on IDE removal.

## Before -> After
### Before
- No `junie` key anywhere: no adapter, no key in `CANONICAL_IDE_KEYS` (length per current tree; concurrent tasks 29/30 in flight); `get("junie")` raises `SpawnError`; no Junie tests (except `test_registry.py` will exercise it automatically once registered).
### After
- `junie` is a first-class IDE key with a full adapter (native skills, project MCP, native `.aiignore` ignore, AGENTS.md entry point), registered at import, covered by tests mirroring peer adapters.

## Details
- Capabilities: `IdeCapabilities(skills="native", mcp="project", agent_ignore="native", entry_point="agents-md")`.
- Skills: `.junie/skills/<normalize_skill_name(skill.name)>/SKILL.md` via `render_skill_md`; overwrite warning like cursor.
- MCP: merge/remove into `.junie/mcp/mcp.json` (`mcpServers` map); JSON only; reuse cursor entry shape verbatim (stdio no `type`; http/sse with `type`; proxy `command="spawn"` + `mcp_stdio_argv`; env secrets `${KEY}`).
- Agent ignore: managed block in root `.aiignore` (`rewrite_ignore_block` / `remove_ignore_block`) plus split-region overrides and `clear_spawn_agent_ignore` (cursor pattern). `.aiignore` is gitignore syntax, so `# spawn:` comment markers are inert to Junie.
- Entry point: root `AGENTS.md` via `rewrite_managed_block` (shared surface; `.junie/AGENTS.md` alternative not used).
- Finalize: unlink `.junie/mcp/mcp.json` when `mcpServers` empty; prune empty dirs under `.junie`; remove `.junie` only when it has zero files under it (user content like `memory/`, `rules/`, `playbook.md` prevents removal). Do NOT touch `.aiignore` wholesale in finalize (peer finalize for ignore files is done by remove_agent_ignore paths; junie finalize clears spawn block then unlinks if empty, mirroring `finalize_cline_repo`).
- Registration checklist: `low_level.py` tuple append + `__init__.py` import/export must land together (register() raises otherwise).
- Sources: junie.jetbrains.com/docs (guidelines-and-memory, agent-skills, junie-cli-mcp-configuration), jetbrains.com/help/ai-assistant (junie-agent, disable-ai-assistant), github.com/JetBrains/junie-guidelines.
- Spec review fixes applied (cross glm-5.3 + deepseek-v4-pro, kimi-k3.1-pro rate-limited): rebased anchors on the current tree (mimo-code/hermes in flight), SpawnWarning per spawn/rules/03-adapter-spawn-warning.md, frontmatter name == dir name via model_copy per spawn/rules/04-adapter-skill-name-constraints.md, `finalize_junie_repo` __all__ excerpt added, `junie_json` parity dispatch wording, IdeCapabilities value-domain note. Design doc update (`spec/design/ide-adapters.md` supported-names list, IDE Matrix row, entry-point and agent-ignore tables) happens in Step 8, not in a coder subtask.

## Execution Scheme
Suggested coordinator model: glm-5.3-flash
> Each step id is the subtask filename.
> Each step is executed by a dedicated `A5-coder` subagent (see Step 5).
- Phase 1 (sequential): step 1-adapter-module -> step 2-tests
- Phase 2 (sequential): step review — inspect all changes, fix inconsistencies
