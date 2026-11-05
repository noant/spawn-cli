# 28: OpenCode CLI IDE adapter

## Source seed
- Path: spec/seeds/5-opencode-cli-adapter.md

## Status
- [V] Research [GLM-5.3 + Kimi-k3]
- [ ] User research review
- [V] Spec drafting [glm-5.3-flash]
- [V] Spec self-review [glm-5.3]
- [V] Spec review
- [V] Code implementation [glm-5.3-flash]
- [V] Code self-review [glm-5.3]
- [ ] Code review / debugging
- [V] Design document update [glm-5.3-flash]

## Goal
Add a full OpenCode CLI IDE adapter (`src/spawn_cli/ide/opencode.py`, key `opencode`) with skills, MCP, project-scope agent ignore, AGENTS.md entry point, vacancy cleanup, registration and tests.

## Motivation
New feature: OpenCode CLI users get native Spawn integration (skills, MCP proxy, ignore, entry point) instead of no / stub support.

## Invasiveness level
medium-invasive — new adapter + import registration + `CANONICAL_IDE_KEYS` extension + vacancy helper + tests; no other layers reworked.

## Review models
- Research review: cross-review: glm-5.3, kimi-k3
- Spec review: single agent: glm-5.3
- Code review: single agent: glm-5.3

## Run mode
auto — fully LLM-run, no user participation; user confirmations (Steps 4, 7) skipped, checkboxes left unchecked.

## Research summary
Cross-research (GLM-5.3 + Kimi-k3), merged; findings verified by two A4-reviewers (both PASS, no conflicts).

Codebase facts:
- `CANONICAL_IDE_KEYS` (`src/spawn_cli/core/low_level.py:28-36`) currently ends with `"cline"`; precedent (task 27) appends new keys at the end -> `"opencode"` after `"cline"`. Registration must land in the same step, else `tests/ide/test_registry.py` fails (`get(key)` raises SpawnError for unregistered key).
- Adapter ABC (`src/spawn_cli/ide/registry.py`): detect/add_skills/remove_skills/add_mcp/remove_mcp/add_agent_ignore/remove_agent_ignore/rewrite_entry_point + optional rewrite_core/extension_agent_ignore, clear_spawn_agent_ignore, finalize_repo_after_ide_removed; `register()` validates key against `CANONICAL_IDE_KEYS`.
- StubAdapter (`src/spawn_cli/ide/_stub.py`) is NOT registered for opencode — the new adapter is a full implementation; `_stub.py` unchanged.
- `normalize_skill_name` (`low_level.py:54-59`) keeps `.` and `_`; OpenCode requires `^[a-z0-9]+(-[a-z0-9]+)*$`, 1-64 chars, name == directory name. Adapter needs stricter sanitization; precedent `cline.py:52-63` (`render_skill_md(skill.model_copy(update={"name": name}))`).
- JSON-merge precedent: `claude_code.py` (root `.mcp.json`, `json.dumps(indent=2)`); project-style agent ignore diff: `high_level._sync_project_agent_ignore_permissions` + state `spawn/.metadata/<ide>/agent-ignore.txt`; `clear_spawn_agent_ignore` reads `ll.get_agent_ignore_list`.
- Vacancy: `_vacancy.py` helpers are tied to dotdir layouts and key `mcpServers`; a new `finalize_opencode_repo` is required (root `opencode.json`, keys `mcp` + `permission`, prune `.opencode/skills`) per rule `spawn/rules/01-vacancy-cleanup-subtrees.md`.
- Tests: `tests/ide/test_opencode.py` mirrors peers (fixture adapter; detect; add/remove skills incl. overwrite warning; add/remove MCP incl. merge + shapes + secret placeholder; ignore roundtrip/idempotent; entry point; SpawnWarning category). `test_mcp_stdio_proxy_parity.py` parameterized — add opencode param reading root `opencode.json` key `mcp`. `test_vacancy.py` needs finalize tests.
- Warnings: user-facing warnings must use `spawn_cli.errors.SpawnWarning` (rule `spawn/rules/03-adapter-spawn-warning.md`).

OpenCode CLI facts (docs: opencode.ai/docs/{config,skills,mcp-servers,permissions,rules}):
- Detection markers: root `opencode.json` or `opencode.jsonc`, and/or `.opencode/` dir. Project config merges with global config.
- Skills: `.opencode/skills/<name>/SKILL.md`; frontmatter `name` required and must equal directory name; `description` required; unknown fields ignored -> `render_skill_md` compatible. OpenCode also reads `.claude/skills` and `.agents/skills` (compat; Spawn writes only `.opencode/skills`).
- MCP: key `mcp` in `opencode.json`. Local: `{"type":"local","command":[<single argv array>],"enabled":true,"environment":{...}}` (optional `cwd`, `timeout`). Remote: `{"type":"remote","url":...,"headers":{...}}` — sse and streamable-http both collapse to `remote` (known information loss). Placeholders: `{env:VAR}` (NOT `${VAR}`), also `{file:path}`.
- Agent ignore: no ignore file exists; project config `permission.read` / `permission.edit` map glob -> `allow|ask|deny`, last matching rule wins.
- Entry point: root `AGENTS.md` via managed block `<!-- spawn:start/end -->` (`rewrite_managed_block`), same as codex/cursor/cline.

Disagreements: none between the two research models.

## Design overview
- Affected modules: `spawn_cli.ide` (new adapter), `spawn_cli.core.low_level` (key tuple), `spawn_cli.ide._vacancy` (new finalize helper), `tests.ide`.
- Files & symbols:
  - `src/spawn_cli/core/low_level.py` — `CANONICAL_IDE_KEYS` (append `"opencode"`)
  - `src/spawn_cli/ide/opencode.py` — NEW: `OpenCodeAdapter(IdeAdapter)`, helpers `_sanitize_skill_name`, `_build_mcp_entry`, module-level `register(OpenCodeAdapter())`
  - `src/spawn_cli/ide/__init__.py` — import registration + `OpenCodeAdapter` export
  - `src/spawn_cli/ide/_vacancy.py` — NEW: `finalize_opencode_repo(target_root)`
  - `tests/ide/test_opencode.py` — NEW
  - `tests/ide/test_mcp_stdio_proxy_parity.py` — new opencode param
  - `tests/ide/test_vacancy.py` — finalize tests
  - `spec/design/ide-adapters.md` — matrix rows (updated in Step 8)
- Data flow changes: none outside existing IDE adapter flow; MCP goes through `NormalizedMcp` -> root `opencode.json` key `mcp`; ignore globs diff-synced via `spawn/.metadata/opencode/agent-ignore.txt`.
- Integration points: registry import registration; `high_level._sync_project_agent_ignore_permissions` (agent_ignore="project"); `ll.get_agent_ignore_list`; proxy argv from `mcp_stdio_argv`.

## Before -> After
### Before
- `opencode` is absent from `CANONICAL_IDE_KEYS` and the registry; `spawn refresh --ide opencode` fails; StubAdapter for opencode is not even instantiated.
### After
- `opencode` is a canonical key; full adapter: skills to `.opencode/skills/`, MCP to root `opencode.json` (`mcp`), ignore via `permission.read/edit` deny globs in `opencode.json`, entry point AGENTS.md managed block, vacancy cleanup `finalize_opencode_repo`.

## Details
Decisions (auto mode, recorded per Step 2.2):
1. Agent ignore capability: `project` — deny globs written to BOTH `permission.read` and `permission.edit` in `opencode.json` as idempotent dict entries `"glob": "deny"` (rule 02-compatible: dict-keyed, removal prunes only spawn-owned empty subtrees). Clear via `ll.get_agent_ignore_list`.
2. Skill names: `_sanitize_skill_name` = `normalize_skill_name` then replace `.`/`_` with `-`, collapse `-+` -> `-`, strip leading/trailing `-`; frontmatter name forced to equal dir name (cline precedent).
3. Config file policy: always read/write root `opencode.json`. If `opencode.jsonc` exists and `opencode.json` does not, emit `SpawnWarning` ("Spawn manages opencode.json; opencode.jsonc is not merged") and create `opencode.json`. Unparseable `opencode.json` -> raise `SpawnError` before mutation (no partial writes).
4. MCP transport mapping: `stdio` -> `local` (proxy: `"command": ["spawn"] + mcp_stdio_argv(...)`); `streamable-http`/`sse` -> `remote` (sse/http distinction lost — accepted). Env placeholders `{env:VAR}`; `enabled: True` always set; `cwd` not emitted (parity with peers).
5. OpenCode also scanning `.claude/skills`/`.agents/skills` is ignored — Spawn writes only `.opencode/skills` (no compat layouts).
6. Detection: `opencode.json` OR `opencode.jsonc` OR `.opencode/` exist. Capabilities: `skills="native"`, `mcp="project"`, `agent_ignore="project"`, `entry_point="agents-md"`. `AGENTS.md` alone is NOT a detect marker (shared with codex/cursor/cline).
7. All adapter warnings use `SpawnWarning`.

## Execution Scheme
Suggested coordinator model: glm-5.3-flash
> Each step id is the subtask filename.
> Each step is executed by a dedicated `A5-coder` subagent (see Step 5).
- Phase 1 (sequential): step 1-adapter-and-registration -> step 2-vacancy-cleanup
