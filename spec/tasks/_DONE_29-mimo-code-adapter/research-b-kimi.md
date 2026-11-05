# Research B (external facts): MiMo Code adapter

Role: A2-researcher, line B. Researcher model: Kimi-k3.
Date basis: public docs at mimo.xiaomi.com and github.com/XiaomiMiMo/MiMo-Code (fetched during research).

Fact markers: [verified] = confirmed from cited source; [assumed] = inference / repo-precedent-based.

## 1. What MiMo Code is

- MiMo Code (MiMoCode) is Xiaomi's terminal-native AI coding agent, a fork of OpenCode; same experience in terminal, desktop app, and IDE extensions. [verified] https://github.com/XiaomiMiMo/MiMo-Code , https://mimo.xiaomi.com/mimocode/start
- Config format and many conventions are inherited from OpenCode (JSON/JSONC config, `mcp` root key, `permission` rules, AGENTS.md rules). [verified] README "Relationship to OpenCode" section.

## 2. Project detection markers

- Project config directory: `.mimocode/` in the repo root. [verified] https://mimo.xiaomi.com/mimocode/config-files and README "File Locations".
- Main project config files: `.mimocode/mimocode.jsonc` (also `.mimocode/mimocode.json`). [verified] README "File Locations" table.
- Other project-level files/dirs MiMo Code uses: `.mimocode/tui.json`, `.mimocode/skills/`, `.mimocode/agents/`, `.mimocode/commands/`, `.mimocode/workflows/`. [verified] README + docs pages (skills/agents/commands; workflows from README "Custom workflows").
- Rules file: `AGENTS.md` in project root. [verified] https://mimo.xiaomi.com/mimocode/rules
- Global config: `~/.config/mimocode/mimocode.jsonc` (XDG; Windows `%LOCALAPPDATA%\mimocode\`; override via `MIMOCODE_HOME`). [verified] README.
- [assumed] For detect(): `.mimocode/` existence is the reliable marker. `AGENTS.md` alone is NOT a valid marker - it is shared by Codex/OpenCode/MiMo Code and other agents (precedent: codex.py detects `.codex` or `.agents`, not AGENTS.md).

## 3. Skills / agents / commands support

### Skills
- Skill = a folder containing `SKILL.md`; skill name comes from YAML frontmatter, NOT from the folder name; discovery is recursive. [verified] https://mimo.xiaomi.com/mimocode/skills
- Project discovery locations:
  - `.mimocode/skills/**/SKILL.md` (singular `.mimocode/skill/` also works);
  - compatibility dirs `.claude/skills/**`, `.agents/skills/**`, `.codex/skills/**`, `.opencode/skills/**` (scanned at project level).
  [verified] same page.
- Global: `~/.config/mimocode/skills/**/SKILL.md` and the same four compat dirs under `~/`. [verified] same page.
- Frontmatter fields read: `name` (required), `description` (required), `hidden` (optional bool). Other fields ignored. [verified] same page.
- Name format: NOT enforced by MiMo Code; recommendation is lowercase alphanumerics with single hyphens (e.g. `git-release`). Duplicate names: last loaded wins with a warning. [verified] same page.
- Extra sources via config: `skills.paths` (array of dirs), `skills.urls`. [verified] same page + config-files page.
- Skill permissions via `permission.skill` glob rules (allow/deny/ask). [verified] skills page.
- Builtin skills can be overridden by a same-named skill in `.mimocode/skills/<name>/SKILL.md`. [verified] README "Builtin Skills".
- [assumed] Adapter mapping: render to `.mimocode/skills/<normalized-name>/SKILL.md`. Because the name comes from frontmatter (not dirname), rule 04's strict "name == dirname" constraint is likely NOT required; standard `normalize_skill_name` should suffice. Keeping dirname == frontmatter name is still recommended for predictability.

### Agents
- Custom agents: JSON via `agent` key in config, or Markdown files in `.mimocode/agents/*.md` (project) / `~/.config/mimocode/agents/` (global); filename becomes agent name. Frontmatter: description, mode (primary|subagent|all), model, temperature, permission, tools (deprecated), hidden, color, etc. [verified] https://mimo.xiaomi.com/mimocode/agents
- Built-in agents: build (primary, full tools), plan (primary, read-only-ish), general + explore (subagents). [verified] same page + README.

### Commands
- Custom commands: `.mimocode/commands/<name>.md` with frontmatter (description, agent, model, subtask); body is the prompt template with `$ARGUMENTS`, `$1..$N`, `!`shell`` injection, `@file` references. Also JSON via `command` key. [verified] https://mimo.xiaomi.com/mimocode/commands
- [assumed] Not directly needed for the spawn adapter contract (no commands method in IdeAdapter), but relevant if spawn later maps slash-command-like skills.

## 4. MCP support

- Project-scope location: `mcp` root key in `.mimocode/mimocode.jsonc` / `.mimocode/mimocode.json`. [verified] https://mimo.xiaomi.com/mimocode/mcp-servers
- Local (stdio) entry format:
  ```jsonc
  "name": {
    "type": "local",
    "command": ["npx", "-y", "my-mcp-command"],   // array, command + args
    "environment": { "VAR": "value" },
    "enabled": true,
    "timeout": 5000
  }
  ```
  [verified] same page ("Local" + Options table).
- Remote (streamable HTTP) entry format:
  ```jsonc
  "name": {
    "type": "remote",
    "url": "https://my-mcp-server.com",
    "headers": { "Authorization": "Bearer MY_API_KEY" },
    "oauth": { "clientId": "...", "clientSecret": "...", "scope": "..." } | false,
    "enabled": true,
    "timeout": 5000
  }
  ```
  [verified] same page ("Remote" + OAuth sections).
- Env/file substitution in config values: `{env:VAR}` (empty when unset), `{file:path}` (relative to config file dir). Works inside `headers`/`environment` values. [verified] https://mimo.xiaomi.com/mimocode/config-files "Variable substitution".
- CLI management: `mimo mcp` (list/auth/logout/debug). [verified] README + mcp-servers page.
- Per-agent/global tool gating via `permission`-style `tools` glob keys (`"my-mcp*": false`); MCP tool names are prefixed `<servername>_*`. [verified] mcp-servers page "Manage".
- [assumed] Adapter mapping: identical to the existing opencode.py `_build_mcp_entry` (type local/remote, command array, environment, headers, enabled=true). A spawn stdio proxy entry becomes `"command": ["spawn", ...mcp_stdio_argv(...)]` with `"type": "local"`. Note SSE transport: docs only name "remote"; opencode.py already renders both streamable-http and sse as `{"type":"remote","url":...}` - reuse [assumed for MiMo Code, verified for opencode precedent].
- [assumed] Canonical config file choice (rule 05): pick `.mimocode/mimocode.json` as the single canonical file; if only `.mimocode/mimocode.jsonc` exists, write the canonical `.json` and emit SpawnWarning naming both (mirrors opencode.py precedent; JSONC comments make safe json merges impossible).

## 5. Agent ignore

- No dedicated ignore file (like `.cursorignore`/`.codeiumignore`) is documented for MiMo Code. [verified absence] no mention in docs tree (Rules, Permissions, Config Files, MCP, Skills, Agents pages checked).
- Closest native mechanism: granular `permission` rules keyed by tool with glob patterns, last matching rule wins. Relevant tools: `read` (matches file path), `edit` (all file modifications), `glob`, `grep`, `bash`, plus `external_directory` guard. Example:
  ```json
  { "permission": { "edit": { "*": "deny", "packages/web/src/content/docs/*.mdx": "allow" } } }
  ```
  [verified] https://mimo.xiaomi.com/mimocode/permissions
- Wildcards: `*` any chars, `?` one char, rest literal; `~`/`$HOME` expansion at pattern start. [verified] same page.
- Default: read of `.env` files is denied out of the box. [verified] same page "Defaults".
- `watcher.ignore` exists but only controls the file watcher, NOT agent file access - do not use it for agent ignore. [verified] config-files page "watcher".
- [assumed] Adapter mapping: mirror opencode.py `add_agent_ignore` - write `"deny"` rules for spawn globs under `permission.read` and `permission.edit` in `.mimocode/mimocode.json`; remove symmetrically and prune empty subtrees (rules 01/02). Idempotent dict-keyed entries satisfy rule 02 point 3.

## 6. Entry point / rules-instructions file

- Primary rules file: `AGENTS.md` in project root (markdown, free-form). Recommended to commit to Git. [verified] https://mimo.xiaomi.com/mimocode/rules
- Global rules: `~/.config/mimocode/AGENTS.md`. Claude Code fallbacks: project `CLAUDE.md`, global `~/.claude/CLAUDE.md` (only used when the corresponding AGENTS.md is absent). [verified] same page.
- Precedence: local files by traversing up from cwd (AGENTS.md, then CLAUDE.md) -> global `~/.config/mimocode/AGENTS.md` -> `~/.claude/CLAUDE.md`. First match wins per category. [verified] same page.
- Extra instruction files via config `instructions` array: paths, globs (`packages/*/AGENTS.md`, `.cursor/rules/*.md`), even remote URLs (5s fetch timeout); combined with AGENTS.md. [verified] same page + config-files page.
- `/init` generates/improves AGENTS.md in place. [verified] same page.
- [assumed] Managed-block rewriting: AGENTS.md is plain markdown with no native managed-block concept; the standard spawn approach (`rewrite_managed_block` from registry, SPAWN_BLOCK_START/END markers, as in codex.py/opencode.py `rewrite_entry_point`) applies unchanged.

## 7. Adapter contract mapping (from repo precedents)

Sources: src/spawn_cli/ide/registry.py, src/spawn_cli/ide/codex.py, src/spawn_cli/ide/opencode.py.

- IdeAdapter abstract methods: `detect`, `add_skills`, `remove_skills`, `add_mcp`, `remove_mcp`, `add_agent_ignore`, `remove_agent_ignore`, `rewrite_entry_point`; optional overrides `clear_spawn_agent_ignore`, `finalize_repo_after_ide_removed`. [verified] registry.py.
- Registration: `register(MimoCodeAdapter())` with `key` present in `CANONICAL_IDE_KEYS` (core/low_level.py) - the new key (suggested `mimo-code`) must be added there; registry raises SpawnError otherwise. [verified] registry.py `register()`.
- Closest template: opencode.py (same config schema family). Suggested capabilities:
  - skills: `native` (`.mimocode/skills/<name>/SKILL.md`);
  - mcp: `project` (`.mimocode/mimocode.json`, `mcp` key);
  - agent_ignore: `project` (`permission.read`/`permission.edit` deny globs in same file);
  - entry_point: `agents-md` (root AGENTS.md managed block).
  [assumed] mapping based on sections 3-6; capability vocabulary [verified] registry.py IdeCapabilities.
- detect(): `used_in_repo = (target_root / ".mimocode").exists()`; possibly also check `.mimocode/mimocode.json(c)` explicitly. [assumed], precedent codex.py/opencode.py detect().
- Rules to honor (spawn/rules):
  - 00-general: ASCII, concise docs, no auto-build. [verified]
  - 01-vacancy-cleanup-subtrees: any new config subtree written must be known to `finalize_mimo_code_repo` in `_vacancy.py` (known keys: `mcp`, `permission`); add cleanup test. [verified]
  - 02-agent-config-namespacing: deny rules live under `permission.*` dict entries; idempotent; never mutate unrelated user keys. [verified]
  - 03-adapter-spawn-warning: use `SpawnWarning` (from spawn_cli.errors) for all user-facing warnings. [verified]
  - 04-adapter-skill-name-constraints: likely NOT needed (MiMo reads name from frontmatter, no strict regex documented); standard `normalize_skill_name` is enough. [assumed]
  - 05-adapter-canonical-config-file: single canonical `.mimocode/mimocode.json`; warn (SpawnWarning) if only `.jsonc` variant exists; raise SpawnError before mutation on unparseable canonical file. [assumed application of verified rule, mirroring opencode.py]

## 8. Open questions / risks

- Whether MiMo Code's JSONC loader would conflict if both `.mimocode/mimocode.json` and `.mimocode/mimocode.jsonc` exist (merge precedence not documented) - the canonical-file rule (05) mitigates this by warning. [assumed risk]
- SSE vs streamable-http remote typing: docs mention only "remote"; verify behavior if an SSE server is configured. [assumed]
- Docs site version drift: facts reflect the live docs at fetch time; MiMo Code evolves quickly (README mentions V0.1.0 open-source release and rapid changelog).

## R14-changed-files

- spec/tasks/29-mimo-code-adapter/research-b-kimi.md (created, this file)
