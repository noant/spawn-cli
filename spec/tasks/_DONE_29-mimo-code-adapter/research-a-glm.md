# Research A (GLM): Mimo Code adapter — codebase facts

Task: new adapter `src/spawn_cli/ide/mimo_code.py` replacing StubAdapter for Mimo Code.
Seed: `spec/seeds/6-mimo-code-adapter.md`.

## 1. Important discovery: no Mimo stub exists yet

- `mimo` / `mimo-code` appears NOWHERE in `src/` or `tests/` (grep confirmed). Only reference is the seed `spec/seeds/6-mimo-code-adapter.md`.
- `CANONICAL_IDE_KEYS` (src/spawn_cli/core/low_level.py:28-37) is currently: `("cursor", "codex", "claude-code", "windsurf", "github-copilot", "gemini-cli", "cline", "opencode")` — no `mimo-code`.
- `registry.register()` raises `SpawnError("Cannot register unknown IDE key")` if the key is not in `CANONICAL_IDE_KEYS` (src/spawn_cli/ide/registry.py:110-115).
- Consequence: implementation must ALSO add `"mimo-code"` to `CANONICAL_IDE_KEYS` (append at the end to preserve existing ordering; tests assert `detect_supported_ides` keys == `CANONICAL_IDE_KEYS`, so ordering change is safe but append-only is conventional).

## 2. BaseAdapter interface (src/spawn_cli/ide/registry.py)

`IdeAdapter(ABC)` with class attr `key: str`. Abstract methods (all must be implemented):

- `detect(self, target_root: Path) -> DetectResult`
- `add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]` — returns `[{"skill": <original name>, "path": <posix rel path>}]`
- `remove_skills(self, target_root: Path, rendered_paths: list[dict]) -> None`
- `add_mcp(self, target_root: Path, normalized_mcp: NormalizedMcp) -> list[str]` — returns rendered server names
- `remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None`
- `add_agent_ignore(self, target_root: Path, globs: list[str]) -> None`
- `remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None`
- `rewrite_entry_point(self, target_root: Path, prompt: str) -> str` — returns rendered rel path

Optional (default no-op) overrides:
- `rewrite_core_agent_ignore(target_root, globs)` / `rewrite_extension_agent_ignore(target_root, globs)` — dual-region ignore; used by text-ignore adapters (cursor, cline), NOT by config-based adapters (codex, claude-code, opencode).
- `clear_spawn_agent_ignore(target_root)` — config-based adapters implement it as: read recorded globs via `ll.get_agent_ignore_list(target_root, self.key)` then call own `remove_agent_ignore`.
- `finalize_repo_after_ide_removed(target_root)` — delegates to `_vacancy` pruner.

Dataclasses:
- `IdeCapabilities(skills, mcp, agent_ignore, entry_point: str)` — values: native | project | entry-only | external | unsupported; adapters also use free-form entry_point tags like `"agents-md"`, `"claude-md"`.
- `DetectResult(used_in_repo: bool, capabilities: IdeCapabilities)`.

Registration: each adapter module ends with `register(XAdapter())` at import; `ide/__init__.py` imports the module (side-effect registration) and re-exports the class. `ALIASES` dict in registry.py maps short names (`claude`, `gemini`, `copilot`, `github`) — a `mimo` alias is optional.

`StubAdapter(key, caps)` (src/spawn_cli/ide/_stub.py): warns `f"{key}: ... not yet implemented"` for every op, detect returns `used_in_repo=False`.

## 3. Shared helpers (src/spawn_cli/ide/_helpers.py)

- Markers: `SPAWN_BLOCK_START = "<!-- spawn:start -->"`, `SPAWN_BLOCK_END = "<!-- spawn:end -->"` (entry-point MD files); ignore-file markers `# spawn:start/end` (legacy), `# spawn:core:start/end` and `# spawn:ext:start/end` (dual-region).
- `render_skill_md(skill: SkillMetadata) -> str` — frontmatter (name, description), body, "Hints:", "Mandatory reads:" (spawn/navigation.yaml deduped & last), "Contextual reads:".
- `rewrite_managed_block(file_path, prompt)` — regex-replaces existing spawn block (DOTALL) or prepends block + "\n" at top; creates parent dirs.
- `rewrite_ignore_block(file_path, globs)` / `remove_ignore_block(file_path, globs)` — legacy single-block managed region in text ignore files.
- Dual-region API: `rewrite_core_agent_ignore_region`, `rewrite_extension_agent_ignore_region`, `clear_split_agent_ignore_file`, `parse_split_agent_ignore_file`, `write_split_agent_ignore_file` — legacy block inner lines are discarded (migration), user chunks preserved and core/ext blocks interleaved.
- `normalize_skill_name` (from core/low_level.py:55): lower, spaces->`-`, strip `[^a-z0-9._-]`, collapse `-{2,}`.

## 4. Precedent adapters — per-concern matrix

| Concern | codex.py | claude_code.py | cursor.py | cline.py | opencode.py |
|---|---|---|---|---|---|
| detect markers | `.codex/` or `.agents/` | `.claude/` or `CLAUDE.md` | `.cursor/` | `.cline/`, `.clinerules`, `.clineignore` | `.opencode/`, `opencode.json`, `opencode.jsonc` |
| caps | native/project/project/agents-md | native/project/project/claude-md | native/project/native/agents-md | native/unsupported/native/agents-md | native/project/project/agents-md |
| skills dir | `.agents/skills/<name>/SKILL.md` | `.claude/skills/...` | `.cursor/skills/...` | `.cline/skills/...` (frontmatter name == dir name via `model_copy(update={"name": name})`) | `.opencode/skills/...` (same rule; extra `_sanitize_skill_name` strips `_` and `.`) |
| MCP config | `.codex/config.toml` key `mcp_servers` (TOML, `load_toml`/`save_toml` from spawn_cli.io.toml_io) | root `.mcp.json` key `mcpServers` | `.cursor/mcp.json` key `mcpServers` | unsupported -> `SpawnWarning` | root `opencode.json` key `mcp`, entries `{"type": "local"/"remote", "command": [..], "enabled": true}` |
| agent ignore | TOML `permissions.spawn.filesystem[":workspace_roots"][glob] = "deny"`; warns if `sandbox_mode` set | `.claude/settings.json` `permissions.deny` list | `.cursorignore` managed blocks | `.clineignore` managed blocks | `opencode.json` `permission.read/edit` glob->"deny" |
| entry point | `AGENTS.md` + rewrite_managed_block | `CLAUDE.md` (warns if `.claude/CLAUDE.md` exists) | `AGENTS.md` | `AGENTS.md` | `AGENTS.md` |
| vacancy | `_vac.finalize_codex_repo` | `_vac.finalize_claude_repo` | `_vac.finalize_standard_dotdir_skills_and_mcp(root, ".cursor", allow_delete_entire=True)` | `_vac.finalize_cline_repo` | `_vac.finalize_opencode_repo` |

Common patterns (copy these verbatim for mimo_code.py):
- add_skills: warn `f"Overwriting existing rendered skill: {skill_path}"` (cline/opencode use `SpawnWarning` category, codex/claude/cursor plain UserWarning).
- remove_skills: unlink SKILL.md; rmdir parent only if empty (keeps user resources).
- MCP entry builders handle `server.spawn_stdio_proxy` -> command `["spawn"] + mcp_stdio_argv(extension, name)` (spawn_cli/ide/mcp_stdio_argv.py: `["mcp_stdio", "extension", <ext>, "name", <name>]`); secrets rendered as env placeholders (`${K}` or `{env:K}` depending on IDE format).
- remove_* are idempotent: missing file -> return; prune empty parent config keys (see opencode.remove_mcp / remove_agent_ignore).
- Errors: `SpawnError` / `SpawnWarning` from `spawn_cli.errors` (re-exported by `spawn_cli.core.errors`). opencode `_load_config` raises `SpawnError` on invalid JSON and warns `SpawnWarning` when canonical config is absent but `opencode.jsonc` exists ("canonical config file rule" precedent).

## 5. Registration checklist for mimo-code

1. Add `"mimo-code"` to `CANONICAL_IDE_KEYS` in src/spawn_cli/core/low_level.py (append).
2. Create `src/spawn_cli/ide/mimo_code.py` ending with `register(MimoCodeAdapter())`.
3. In `src/spawn_cli/ide/__init__.py`: add `from . import mimo_code  # noqa: F401` (after opencode) and `from .mimo_code import MimoCodeAdapter` + add to `__all__`.
4. Optional: add `"mimo": "mimo-code"` to `ALIASES` in registry.py.
5. Possibly a vacancy pruner in `_vacancy.py` (mirror `finalize_opencode_repo`) — see src/spawn_cli/ide/_vacancy.py.

## 6. Tests (tests/ide/)

Peer files: `test_cline.py`, `test_codex.py`, `test_cursor.py`, `test_claude_code.py`, `test_opencode.py`, `test_registry.py`, `test_gemini_cli.py`, `test_windsurf.py`, `test_github_copilot.py`; plus shared `test_vacancy.py` and `test_mcp_stdio_proxy_parity.py`.

Structure (from test_cline.py / test_opencode.py):
- module fixture `adapter()` returning the adapter instance;
- helper `_skill(name="spectask-execute") -> SkillMetadata` (name, description, content="# body\n", hints=[...]);
- `_stdio_server(name, proxy=False) -> McpServer` for MCP tests (McpTransport(type="stdio", command=..., args=[...]), spawn_stdio_proxy flag);
- per-adapter tests: detect markers (False on empty tmp_path, True per marker file/dir), capabilities string assertions, add/remove skills roundtrip incl. exact rendered path & frontmatter name rule, extra-file retention, overwrite warning (`pytest.warns(UserWarning, match="Overwriting")`), MCP add/remove roundtrip + proxy variant, agent-ignore roundtrip/idempotency/legacy-migration, entry-point block rewrite (SPAWN_BLOCK_START/END);
- `test_registry.py` asserts `detect_supported_ides(tmp_path)` keys == `CANONICAL_IDE_KEYS` — adding mimo-code updates this automatically; consider adding `get("mimo-code")`/alias assertions there.

## 7. Line B: external facts about Mimo Code (brief, from official docs mimo.xiaomi.com)

- Product: MiMo Code — Xiaomi's terminal coding agent CLI (github.com/XiaomiMiMo/MiMo-Code; docs at mimo.xiaomi.com/mimocode). Distinct from third-party KoinaAI/MiMo-CLI.
- Config: JSON/JSONC `mimocode.json` (project root) / `~/.config/mimocode/mimocode.json` (global); layers merged, `{env:VAR}` and `{file:path}` substitution. Top-level keys include `mcp`, `permission`, `instructions`, `skills`, `agent`, `watcher`. Docs: /mimocode/config-files.
- Skills: `SKILL.md` with YAML frontmatter `name` (required), `description` (required), `hidden` (optional). Name comes from frontmatter, NOT folder name; discovery recursive at `.mimocode/skills/**/SKILL.md` (also `skill/` singular), plus compatibility dirs `.claude`, `.agents`, `.codex`, `.opencode`. Duplicate names: last loaded wins. Docs: /mimocode/skills.
- MCP: config key `mcp`, entries `{"type": "local", "command": [...], "environment": {...}, "enabled": true}` or `{"type": "remote", "url": ..., "headers": {...}, "enabled": true}` — essentially identical shape to OpenCode's `mcp` format. Docs: /mimocode/mcp-servers.
- Rules / entry point: project-root `AGENTS.md` (created by `/init`); global `~/.config/mimocode/AGENTS.md`; CLAUDE.md fallback compatibility. Extra instruction files via `instructions` array (paths/globs/URLs). Docs: /mimocode/rules.
- Ignore: no dedicated `.mimoignore` documented; relevant mechanisms are `permission` (tool allow/deny/ask, per-tool patterns) and `watcher.ignore` glob list. Agent-ignore via `permission` deny for edit/read is the closest analog (verify exact glob-permission syntax on the Permissions page during spec synthesis).
- Mapping recommendation: Mimo Code's config/skills/MCP/AGENTS.md conventions are nearly identical to OpenCode's — `opencode.py` is the best implementation precedent (JSON config with `mcp` local/remote entries + `enabled`, `permission` read/edit deny globs, AGENTS.md entry point). Skills dir: `.mimocode/skills/<name>/SKILL.md`; frontmatter name need NOT equal dir name for Mimo (unlike cline/opencode), but keeping them equal is harmless.

## 8. Files created (R14-changed-files)

- `spec/tasks/29-mimo-code-adapter/research-a-glm.md` (this file)
